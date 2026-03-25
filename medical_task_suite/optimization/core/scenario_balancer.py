"""
场景均衡器 - 自动优化场景类型分布
Scenario Balancer - Automatically Optimize Scenario Type Distribution

功能：
1. 分析当前场景分布
2. 识别过度集中和不足的场景
3. 基于内容相似度重新分配场景
4. 保持L3任务的场景类型不变
5. 确保最终分布符合目标
"""

import re
from typing import Dict, List, Any
from collections import Counter


class ScenarioBalancer:
    """场景均衡器 - 优化场景类型分布"""

    # 场景类型关键词映射
    SCENARIO_KEYWORDS = {
        'CHRONIC_MANAGEMENT': [
            '高血压', '糖尿病', '慢性', '长期', '控制', '复查',
            '用药调整', '规律', '监测', '管理', '维持', '稳定'
        ],
        'MEDICATION_CONSULTATION': [
            '药', '吃药', '服用', '副作用', '药物', '治疗',
            '用药', '停药', '换药', '剂量', '相互作用', '禁忌'
        ],
        'EMERGENCY_CONCERN': [
            '胸痛', '呼吸困难', '昏迷', '大出血', '严重',
            '急诊', '紧急', '危险', '突发', '剧烈', '昏厥'
        ],
        'SYMPTOM_ANALYSIS': [
            '痛', '痒', '肿', '胀', '晕', '咳', '吐', '泻',
            '症状', '怎么回事', '什么原因', '为什么', '怎么'
        ],
        'LIFESTYLE_ADVICE': [
            '饮食', '运动', '锻炼', '休息', '睡眠', '戒烟',
            '限酒', '生活方式', '习惯', '保养', '保健'
        ],
        'INFORMATION_QUERY': [
            '能吗', '可以吗', '会不会', '是不是', '有没有',
            '能否', '是否', '怎么样', '如何', '怎样'
        ]
    }

    def __init__(self, config: Dict[str, Any] = None):
        """初始化场景均衡器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.scenario_targets = self.config.get(
            'scenario_distribution',
            {
                'INFORMATION_QUERY': 0.40,
                'CHRONIC_MANAGEMENT': 0.25,
                'MEDICATION_CONSULTATION': 0.12,
                'SYMPTOM_ANALYSIS': 0.10,
                'EMERGENCY_CONCERN': 0.08,
                'LIFESTYLE_ADVICE': 0.05
            }
        )

        self.preserve_l3 = self.config.get('preserve_l3_scenarios', True)
        self.max_reassignment_rate = self.config.get('max_reassignment_rate', 0.30)

    def analyze_distribution(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析当前场景分布

        Args:
            tasks: 任务列表

        Returns:
            分布统计信息
        """
        scenarios = [t.get('metadata', {}).get('scenario_type', 'Unknown')
                    for t in tasks]
        total = len(scenarios)
        counter = Counter(scenarios)

        distribution = {}
        for scenario, count in counter.items():
            distribution[scenario] = {
                'count': count,
                'percentage': count / total if total > 0 else 0
            }

        # 识别过度集中和不足的场景
        overrepresented = {}
        underrepresented = {}

        for scenario, target in self.scenario_targets.items():
            current = distribution.get(scenario, {}).get('percentage', 0)
            diff = current - target

            if diff > 0.05:  # 超过目标5%以上
                overrepresented[scenario] = {
                    'current': current,
                    'target': target,
                    'excess': diff
                }
            elif diff < -0.05:  # 低于目标5%以上
                underrepresented[scenario] = {
                    'current': current,
                    'target': target,
                    'deficit': abs(diff)
                }

        return {
            'distribution': distribution,
            'overrepresented': overrepresented,
            'underrepresented': underrepresented
        }

    def calculate_scenario_similarity(self, task: Dict[str, Any],
                                     target_scenario: str) -> float:
        """计算任务与目标场景的相似度

        Args:
            task: 任务字典
            target_scenario: 目标场景类型

        Returns:
            相似度分数 (0-1)
        """
        # 提取任务文本内容
        ticket = task.get('ticket', '')
        known_info = task.get('user_scenario', {}).get('instructions', {}).get('known_info', '')
        text = f"{ticket} {known_info}"

        # 获取目标场景的关键词
        keywords = self.SCENARIO_KEYWORDS.get(target_scenario, [])

        # 计算匹配关键词数量
        match_count = sum(1 for keyword in keywords if keyword in text)

        # 计算相似度
        if len(keywords) == 0:
            return 0.0

        similarity = match_count / len(keywords)

        # 考虑关键词频率（出现次数）
        keyword_frequency = sum(text.count(keyword) for keyword in keywords)
        frequency_bonus = min(keyword_frequency / len(keywords) * 0.1, 0.3)

        return min(similarity + frequency_bonus, 1.0)

    def find_best_scenario_match(self, task: Dict[str, Any],
                                available_scenarios: List[str]) -> str:
        """为任务找到最佳的场景匹配

        Args:
            task: 任务字典
            available_scenarios: 可用的场景类型列表

        Returns:
            最佳匹配的场景类型
        """
        best_scenario = None
        best_similarity = 0.0

        for scenario in available_scenarios:
            similarity = self.calculate_scenario_similarity(task, scenario)
            if similarity > best_similarity:
                best_similarity = similarity
                best_scenario = scenario

        # 如果相似度太低，保持原场景
        if best_similarity < 0.3:
            return task.get('metadata', {}).get('scenario_type', 'INFORMATION_QUERY')

        return best_scenario

    def rebalance_scenarios(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重新平衡场景分布

        Args:
            tasks: 任务列表

        Returns:
            场景优化后的任务列表
        """
        # 分析当前分布
        analysis = self.analyze_distribution(tasks)

        print(f"\n场景分布分析:")
        print(f"  过度集中的场景: {list(analysis['overrepresented'].keys())}")
        print(f"  不足的场景: {list(analysis['underrepresented'].keys())}")

        # 如果没有需要调整的，直接返回
        if not analysis['overrepresented'] or not analysis['underrepresented']:
            print("  场景分布已经均衡，无需调整")
            return tasks

        # 找出需要重新分配的任务
        overrepresented_scenario = list(analysis['overrepresented'].keys())[0]
        target_scenarios = list(analysis['underrepresented'].keys())

        print(f"\n重新分配策略:")
        print(f"  从: {overrepresented_scenario}")
        print(f"  到: {target_scenarios}")

        # 筛选可以重新分配的任务
        reassignable_tasks = []
        for i, task in enumerate(tasks):
            current_scenario = task.get('metadata', {}).get('scenario_type')

            # 只重新分配过度集中的场景
            if current_scenario != overrepresented_scenario:
                continue

            # 保留L3任务的场景
            if self.preserve_l3 and task.get('difficulty') == 'L3':
                continue

            # 保留有红线测试的任务场景
            if task.get('red_line_tests'):
                continue

            reassignable_tasks.append((i, task))

        # 计算需要重新分配的数量
        total_tasks = len(tasks)
        target_count = int(total_tasks * self.max_reassignment_rate)
        reassign_count = min(len(reassignable_tasks), target_count)

        print(f"\n可重新分配的任务: {len(reassignable_tasks)}")
        print(f"计划重新分配: {reassign_count}")

        if reassign_count == 0:
            return tasks

        # 为任务分配新的场景
        optimized_tasks = tasks.copy()

        for i, (task_idx, task) in enumerate(reassignable_tasks[:reassign_count]):
            # 轮流分配到不同的目标场景
            target_scenario = target_scenarios[i % len(target_scenarios)]

            # 找到最佳匹配
            best_match = self.find_best_scenario_match(task, [target_scenario])

            # 更新场景
            if best_match:
                optimized_tasks[task_idx]['metadata']['scenario_type'] = best_match

                # 更新场景名称
                scenario_names = {
                    'INFORMATION_QUERY': '信息查询',
                    'CHRONIC_MANAGEMENT': '慢性病管理',
                    'MEDICATION_CONSULTATION': '药物咨询',
                    'SYMPTOM_ANALYSIS': '症状分析',
                    'EMERGENCY_CONCERN': '紧急关注',
                    'LIFESTYLE_ADVICE': '生活方式建议'
                }
                optimized_tasks[task_idx]['metadata']['scenario_name'] = scenario_names.get(
                    best_match, best_match
                )

        # 验证优化后的分布
        final_analysis = self.analyze_distribution(optimized_tasks)

        print(f"\n优化后的场景分布:")
        for scenario, stats in sorted(final_analysis['distribution'].items(),
                                     key=lambda x: x[1]['percentage'],
                                     reverse=True):
            target = self.scenario_targets.get(scenario, 0)
            print(f"  {scenario}: {stats['percentage']:.1%} (目标: {target:.1%})")

        return optimized_tasks

    def get_statistics(self, original_tasks: List[Dict[str, Any]],
                      optimized_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取优化统计信息

        Args:
            original_tasks: 原始任务列表
            optimized_tasks: 优化后任务列表

        Returns:
            统计信息字典
        """
        original_analysis = self.analyze_distribution(original_tasks)
        optimized_analysis = self.analyze_distribution(optimized_tasks)

        # 计算场景变化数量
        scenario_changes = sum(
            1 for orig, opt in zip(original_tasks, optimized_tasks)
            if orig.get('metadata', {}).get('scenario_type') !=
               opt.get('metadata', {}).get('scenario_type')
        )

        return {
            'original_distribution': original_analysis['distribution'],
            'optimized_distribution': optimized_analysis['distribution'],
            'scenario_changes': scenario_changes,
            'change_rate': scenario_changes / len(original_tasks) if original_tasks else 0,
            'overrepresented_resolved': len(original_analysis['overrepresented']) == 0,
            'underrepresented_resolved': len(optimized_analysis['underrepresented']) == 0
        }
