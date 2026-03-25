"""
任务优化器 - 整合所有优化功能的主入口
Task Optimizer - Main Entry Point for All Optimization Features

功能：
1. 整合场景均衡、评估增强、元数据构建等所有功能
2. 协调各个子模块
3. 批量优化任务
4. 生成优化报告
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any

from .scenario_balancer import ScenarioBalancer
from .evaluation_enhancer import EvaluationEnhancer
from .metadata_builder import MetadataBuilder
from .quality_scorer import QualityScorer


class TaskOptimizer:
    """任务优化器 - 整合所有优化功能"""

    def __init__(self, config_path: str = None, config: Dict[str, Any] = None):
        """初始化任务优化器

        Args:
            config_path: 配置文件路径
            config: 配置字典
        """
        # 加载配置
        self.config = self._load_config(config_path, config)

        # 初始化子模块
        self.scenario_balancer = ScenarioBalancer(self.config)
        self.evaluation_enhancer = EvaluationEnhancer(self.config)
        self.metadata_builder = MetadataBuilder(self.config)
        self.quality_scorer = QualityScorer(self.config)

        # 优化器状态
        self.optimization_count = 0
        self.statistics = {}

    def _load_config(self, config_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """加载配置

        Args:
            config_path: 配置文件路径
            config: 配置字典

        Returns:
            合并后的配置字典
        """
        merged_config = {}

        # 从文件加载
        if config_path:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                merged_config.update(file_config)
            except Exception as e:
                print(f"Warning: Failed to load config from {config_path}: {e}")

        # 合并传入的配置
        if config:
            merged_config.update(config)

        return merged_config

    def optimize_task(self, task: Dict[str, Any],
                     task_index: int,
                     optimizations: List[str] = None) -> Dict[str, Any]:
        """优化单个任务

        Args:
            task: 任务字典
            task_index: 任务索引
            optimizations: 应用的优化列表

        Returns:
            优化后的任务字典
        """
        if optimizations is None:
            optimizations = []

        optimized_task = task.copy()

        # 1. 增强评估标准
        if 'evaluation' not in optimizations:
            optimized_task = self.evaluation_enhancer.enhance_task(optimized_task)
            optimizations.append('weighted_evaluation')

        # 2. 添加转换元数据（临时，稍后会被完整替换）
        if 'metadata' not in optimizations:
            optimized_task['original_task_id'] = task.get('id', '')

        return optimized_task, optimizations

    def optimize(self, input_file: str = None,
                output_file: str = None,
                tasks: List[Dict[str, Any]] = None,
                enable_scenario_balancing: bool = True,
                enable_evaluation_enhancement: bool = True,
                enable_metadata_enrichment: bool = True) -> List[Dict[str, Any]]:
        """优化数据集

        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            tasks: 任务列表（如果提供，将忽略input_file）
            enable_scenario_balancing: 是否启用场景均衡
            enable_evaluation_enhancement: 是否启用评估增强
            enable_metadata_enrichment: 是否启用元数据丰富

        Returns:
            优化后的任务列表
        """
        print("=" * 70)
        print("数据集优化器 - Task Optimizer")
        print("=" * 70)

        # 1. 加载任务
        if tasks is None:
            if not input_file:
                raise ValueError("必须提供 input_file 或 tasks 参数")

            print(f"\n1. 加载数据集: {input_file}")
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                print(f"   [OK] 加载了 {len(tasks)} 个任务")
            except Exception as e:
                print(f"   [FAIL] 加载失败: {e}")
                return []

        optimized_tasks = tasks.copy()
        optimizations_applied = []

        # 2. 场景均衡优化
        if enable_scenario_balancing:
            print(f"\n2. 场景均衡优化")
            try:
                original_scenarios = [t.get('metadata', {}).get('scenario_type')
                                    for t in optimized_tasks]
                from collections import Counter
                scenario_dist = Counter(original_scenarios)
                print(f"   原始分布: {dict(scenario_dist)}")

                optimized_tasks = self.scenario_balancer.rebalance_scenarios(optimized_tasks)

                optimized_scenarios = [t.get('metadata', {}).get('scenario_type')
                                     for t in optimized_tasks]
                optimized_dist = Counter(optimized_scenarios)
                print(f"   优化分布: {dict(optimized_dist)}")
                print(f"   [OK] 场景均衡完成")

                optimizations_applied.append('scenario_balancing')
            except Exception as e:
                print(f"   [FAIL] 场景均衡失败: {e}")

        # 3. 评估增强
        if enable_evaluation_enhancement:
            print(f"\n3. 评估标准增强")
            try:
                optimized_tasks = self.evaluation_enhancer.enhance_tasks(optimized_tasks)

                # 统计权重覆盖
                with_weight = sum(
                    1 for t in optimized_tasks
                    if any(c.get('weight')
                          for c in t.get('evaluation_criteria', {})
                                      .get('communication_checks', []))
                )
                print(f"   权重覆盖: {with_weight}/{len(optimized_tasks)} "
                     f"({with_weight/len(optimized_tasks)*100:.1f}%)")
                print(f"   [OK] 评估增强完成")

                optimizations_applied.append('evaluation_enhancement')
            except Exception as e:
                print(f"   [FAIL] 评估增强失败: {e}")

        # 4. 质量评分
        print(f"\n4. 质量评分")
        try:
            quality_scores = self.quality_scorer.calculate_tasks_quality_scores(optimized_tasks)

            import statistics
            print(f"   平均质量分: {statistics.mean(quality_scores):.2f}")
            print(f"   最高质量分: {max(quality_scores):.2f}")
            print(f"   最低质量分: {min(quality_scores):.2f}")
            print(f"   [OK] 质量评分完成")
        except Exception as e:
            print(f"   [FAIL] 质量评分失败: {e}")
            quality_scores = None

        # 5. 元数据丰富
        if enable_metadata_enrichment:
            print(f"\n5. 元数据丰富")
            try:
                optimized_tasks = self.metadata_builder.enrich_tasks_metadata(
                    optimized_tasks,
                    quality_scores=quality_scores,
                    optimizations=optimizations_applied
                )

                with_metadata = sum(1 for t in optimized_tasks if 'conversion_metadata' in t)
                print(f"   元数据覆盖: {with_metadata}/{len(optimized_tasks)} "
                     f"({with_metadata/len(optimized_tasks)*100:.1f}%)")
                print(f"   [OK] 元数据丰富完成")

                optimizations_applied.append('metadata_enrichment')
            except Exception as e:
                print(f"   [FAIL] 元数据丰富失败: {e}")

        # 6. 保存结果
        if output_file:
            print(f"\n6. 保存优化结果: {output_file}")
            try:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(optimized_tasks, f, ensure_ascii=False, indent=2)

                file_size = output_path.stat().st_size / (1024 * 1024)
                print(f"   [OK] 保存成功")
                print(f"   文件大小: {file_size:.2f} MB")
            except Exception as e:
                print(f"   [FAIL] 保存失败: {e}")

        # 7. 生成统计报告
        print(f"\n7. 生成统计报告")
        self._generate_statistics(tasks, optimized_tasks, optimizations_applied)

        self.optimization_count = len(optimized_tasks)

        print("\n" + "=" * 70)
        print("优化完成!")
        print("=" * 70)

        return optimized_tasks

    def _generate_statistics(self, original_tasks: List[Dict[str, Any]],
                           optimized_tasks: List[Dict[str, Any]],
                           optimizations: List[str]) -> None:
        """生成统计报告

        Args:
            original_tasks: 原始任务列表
            optimized_tasks: 优化后任务列表
            optimizations: 应用的优化列表
        """
        self.statistics = {
            'task_count': len(optimized_tasks),
            'optimizations_applied': optimizations
        }

        # 难度分布
        from collections import Counter
        difficulty_dist = Counter(t.get('difficulty', 'Unknown')
                                for t in optimized_tasks)
        self.statistics['difficulty_distribution'] = dict(difficulty_dist)

        # 场景分布
        if 'scenario_balancing' in optimizations:
            scenario_stats = self.scenario_balancer.get_statistics(
                original_tasks, optimized_tasks
            )
            self.statistics['scenario_statistics'] = scenario_stats

        # 评估增强统计
        if 'evaluation_enhancement' in optimizations:
            eval_stats = self.evaluation_enhancer.get_statistics(
                original_tasks, optimized_tasks
            )
            self.statistics['evaluation_statistics'] = eval_stats

        # 元数据统计
        if 'metadata_enrichment' in optimizations:
            metadata_stats = self.metadata_builder.get_statistics(optimized_tasks)
            self.statistics['metadata_statistics'] = metadata_stats

        # 质量统计
        original_scores = self.quality_scorer.calculate_tasks_quality_scores(original_tasks)
        optimized_scores = self.quality_scorer.calculate_tasks_quality_scores(optimized_tasks)

        import statistics
        self.statistics['quality_statistics'] = {
            'original_mean': statistics.mean(original_scores) if original_scores else 0,
            'optimized_mean': statistics.mean(optimized_scores) if optimized_scores else 0,
            'quality_improvement': (statistics.mean(optimized_scores) -
                                   statistics.mean(original_scores))
                                   if original_scores and optimized_scores else 0
        }

        # 打印摘要
        print(f"\n   优化统计:")
        print(f"     - 任务数量: {self.statistics['task_count']}")
        print(f"     - 应用优化: {', '.join(optimizations)}")
        print(f"     - 难度分布: {self.statistics['difficulty_distribution']}")
        if self.statistics['quality_statistics']['optimized_mean']:
            print(f"     - 平均质量分: {self.statistics['quality_statistics']['optimized_mean']:.2f}")
            if self.statistics['quality_statistics']['quality_improvement']:
                improvement = self.statistics['quality_statistics']['quality_improvement']
                print(f"     - 质量提升: {improvement:+.2f}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息

        Returns:
            统计信息字典
        """
        return self.statistics

    def save_report(self, output_file: str) -> None:
        """保存优化报告

        Args:
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.statistics, f, ensure_ascii=False, indent=2)
