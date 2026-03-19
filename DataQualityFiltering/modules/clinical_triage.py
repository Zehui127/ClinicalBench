#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clinical Triage Module - 临床分诊模块

功能：
1. 问题优先级判断 - 识别核心问题、相关问题、其他科室问题
2. 跨科室识别 - 判断问题属于哪个科室
3. 转诊建议生成 - 生成合适的转诊建议
4. 增强追问阈值规则 - 带优先级的追问规则

真实临床场景：
- 患者焦虑时会问各种问题
- 医生需要抓重点（核心疾病）
- 识别其他科室问题并转诊
- 对其他科室问题给予一般建议

Author: Claude Sonnet 4.5
Date: 2025-03-19
"""

import json
import re
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class QuestionPriority(Enum):
    """问题优先级"""
    CRITICAL = "CRITICAL"  # 核心问题，当前科室，必须详细处理
    HIGH = "HIGH"  # 高优先级，当前科室，应该处理
    MEDIUM = "MEDIUM"  # 中等优先级，需要评估
    LOW = "LOW"  # 低优先级，给予一般建议


class ActionRequired(Enum):
    """需要的处理动作"""
    DETAILED_INQUIRY = "detailed_inquiry"  # 详细问诊
    BASIC_ASSESSMENT = "basic_assessment"  # 基础评估
    GENERAL_ADVICE = "general_advice"  # 一般建议
    REFERRAL = "referral"  # 转诊
    GENERAL_ADVICE_AND_REFERRAL = "general_advice_and_referral"  # 一般建议+转诊
    BASIC_ASSESSMENT_AND_REFERRAL = "basic_assessment_and_referral"  # 基础评估+转诊


@dataclass
class QuestionAnalysis:
    """问题分析结果"""
    question: str
    priority: QuestionPriority
    department: str
    is_current_dept: bool
    action_required: ActionRequired
    reason: str
    suggested_questions: List[str] = field(default_factory=list)
    referral_advice: Optional[str] = None
    general_advice: Optional[str] = None


class CrossDepartmentDetector:
    """跨科室识别器"""

    # 关键词到科室的映射
    KEYWORD_DEPT_MAPPING = {
        # 内科相关
        "内科": {
            "keywords": ["高血压", "糖尿病", "感冒", "发烧", "咳嗽", "头痛", "头晕",
                       "胸闷", "心慌", "气短", "乏力", "食欲不振", "恶心", "呕吐",
                       "腹痛", "腹泻", "便秘", "肝功能", "肾功能", "血脂", "血糖"],
            "department": "内科",
            "urgent_keywords": ["胸痛", "呼吸困难", "意识不清"]
        },

        # 外科相关
        "外科": {
            "keywords": ["外伤", "伤口", "缝合", "骨折", "扭伤", "肿瘤", "囊肿",
                       "包块", "疝气", "阑尾炎", "胆囊炎", "结石"],
            "department": "外科",
            "urgent_keywords": ["剧烈疼痛", "出血", "伤口感染"]
        },

        # 眼科
        "眼科": {
            "keywords": ["眼睛", "视力", "看不清", "模糊", "老花", "近视", "远视",
                       "散光", "眼睛干", "眼睛痒", "眼睛红", "眼屎", "流泪",
                       "白内障", "青光眼", "结膜炎"],
            "department": "眼科",
            "urgent_keywords": ["突然失明", "剧烈眼痛", "外伤"]
        },

        # 耳鼻喉科
        "耳鼻喉科": {
            "keywords": ["耳朵", "听力", "耳鸣", "耳聋", "耳朵流脓", "鼻子",
                       "鼻塞", "流鼻涕", "鼻出血", "鼻窦", "嗓子", "咽炎",
                       "喉炎", "声音嘶哑", "扁桃体"],
            "department": "耳鼻喉科",
            "urgent_keywords": ["呼吸困难", "大出血"]
        },

        # 口腔科
        "口腔科": {
            "keywords": ["牙齿", "牙痛", "蛀牙", "牙龈", "牙周炎", "口腔溃疡",
                       "牙齿出血", "牙齿松动", "假牙", "拔牙", "镶牙"],
            "department": "口腔科",
            "urgent_keywords": ["剧烈牙痛", "面部肿胀"]
        },

        # 皮肤科
        "皮肤科": {
            "keywords": ["皮肤", "痒", "皮疹", "红点", "痘痘", "痤疮", "湿疹",
                       "皮炎", "过敏", "荨麻疹", "癣", "疱疹", "疣", "色斑",
                       "痣", "脱发", "头发"],
            "department": "皮肤科",
            "urgent_keywords": ["全身过敏", "严重皮疹"]
        },

        # 精神科/心理科
        "精神科": {
            "keywords": ["失眠", "抑郁", "焦虑", "情绪", "精神", "心理", "压力",
                       "想不开", "自杀", "幻觉", "妄想", "记忆力下降", "注意力不集中"],
            "department": "精神科",
            "urgent_keywords": ["自杀", "自伤", "幻觉", "妄想"]
        },

        # 妇产科
        "妇产科": {
            "keywords": ["月经", "怀孕", "孕期", "胎儿", "分娩", "流产", "白带",
                       "阴道", "盆腔", "子宫", "卵巢", "宫颈", "乳腺"],
            "department": "妇产科",
            "urgent_keywords": ["阴道大出血", "剧烈腹痛", "胎动异常"]
        },

        # 儿科
        "儿科": {
            "keywords": ["宝宝", "婴儿", "幼儿", "儿童", "小孩", "发烧", "咳嗽",
                       "腹泻", "呕吐", "不长个", "发育"],
            "department": "儿科",
            "urgent_keywords": ["高烧不退", "抽搐", "呼吸困难"]
        },

        # 肿瘤科
        "肿瘤科": {
            "keywords": ["肿瘤", "癌症", "癌", "化疗", "放疗", "靶向治疗",
                       "免疫治疗", "恶性肿瘤", "术后复查"],
            "department": "肿瘤科",
            "urgent_keywords": ["剧烈疼痛", "大出血"]
        },

        # 男科
        "男科": {
            "keywords": ["前列腺", "阳痿", "早泄", "性功能", "不育", "精子",
                       "睾丸", "附睾", "包皮", "性病"],
            "department": "男科",
            "urgent_keywords": ["睾丸剧痛", "尿潴留"]
        }
    }

    def detect_department(self, question: str) -> Tuple[str, float, bool]:
        """
        识别问题属于哪个科室

        Args:
            question: 患者的问题

        Returns:
            (department_name, confidence, is_urgent)
            - department_name: 科室名称
            - confidence: 置信度 (0-1)
            - is_urgent: 是否紧急
        """
        question_lower = question.lower()

        # 检查每个科室
        best_match = None
        best_confidence = 0.0
        is_urgent = False

        for dept_name, dept_info in self.KEYWORD_DEPT_MAPPING.items():
            keywords = dept_info["keywords"]
            urgent_keywords = dept_info.get("urgent_keywords", [])

            # 检查紧急关键词
            for urgent_kw in urgent_keywords:
                if urgent_kw in question:
                    is_urgent = True
                    break

            # 计算匹配度
            match_count = sum(1 for kw in keywords if kw in question_lower)
            if match_count > 0:
                confidence = min(match_count / 3.0, 1.0)  # 最多3个关键词就是1.0

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = dept_info["department"]

        if best_match:
            return best_match, best_confidence, is_urgent
        else:
            # 默认返回内科
            return "内科", 0.3, False


class QuestionPrioritizer:
    """问题优先级判断器"""

    def __init__(self):
        self.detector = CrossDepartmentDetector()

        # 科室优先级（数字越小越优先）
        self.DEPT_PRIORITY = {
            "精神科": 1,  # 自杀、抑郁等最优先
            "内科": 2,
            "外科": 3,
            "肿瘤科": 4,
            "妇产科": 5,
            "儿科": 6,
            "其他": 10
        }

    def prioritize_questions(self, questions: List[str],
                            current_dept: str) -> List[QuestionAnalysis]:
        """
        对患者的问题按优先级排序

        Args:
            questions: 患者的问题列表
            current_dept: 当前就诊科室

        Returns:
            按优先级排序的问题分析列表
        """
        analyses = []

        for question in questions:
            analysis = self._analyze_single_question(question, current_dept)
            analyses.append(analysis)

        # 按优先级排序
        analyses.sort(key=lambda x: (
            self._get_priority_score(x.priority),
            self.DEPT_PRIORITY.get(x.department, 99)
        ))

        return analyses

    def _analyze_single_question(self, question: str,
                                 current_dept: str) -> QuestionAnalysis:
        """分析单个问题"""
        # 识别科室
        detected_dept, confidence, is_urgent = self.detector.detect_department(question)

        # 判断是否是当前科室
        is_current_dept = (detected_dept == current_dept)

        # 确定优先级
        if is_urgent:
            priority = QuestionPriority.CRITICAL
        elif is_current_dept:
            priority = QuestionPriority.HIGH
        elif confidence > 0.6:
            priority = QuestionPriority.MEDIUM
        else:
            priority = QuestionPriority.LOW

        # 确定需要的处理动作
        if is_urgent or (is_current_dept and priority == QuestionPriority.HIGH):
            action = ActionRequired.DETAILED_INQUIRY
            reason = "当前科室核心问题，需要详细问诊"
        elif is_current_dept:
            action = ActionRequired.BASIC_ASSESSMENT
            reason = "当前科室相关问题，需要基础评估"
        elif confidence > 0.6:
            action = ActionRequired.BASIC_ASSESSMENT_AND_REFERRAL
            reason = f"其他科室问题（{detected_dept}），需要基础评估并建议转诊"
        else:
            action = ActionRequired.GENERAL_ADVICE_AND_REFERRAL
            reason = f"其他科室问题（{detected_dept}），给予一般建议并转诊"

        # 生成建议的追问
        suggested_questions = self._generate_suggested_questions(question, detected_dept, action)

        # 生成转诊建议
        if not is_current_dept:
            referral_advice = self._generate_referral_advice(question, detected_dept)
            general_advice = self._generate_general_advice(question, detected_dept)
        else:
            referral_advice = None
            general_advice = None

        return QuestionAnalysis(
            question=question,
            priority=priority,
            department=detected_dept,
            is_current_dept=is_current_dept,
            action_required=action,
            reason=reason,
            suggested_questions=suggested_questions,
            referral_advice=referral_advice,
            general_advice=general_advice
        )

    def _get_priority_score(self, priority: QuestionPriority) -> int:
        """获取优先级分数"""
        scores = {
            QuestionPriority.CRITICAL: 1,
            QuestionPriority.HIGH: 2,
            QuestionPriority.MEDIUM: 3,
            QuestionPriority.LOW: 4
        }
        return scores.get(priority, 5)

    def _generate_suggested_questions(self, question: str,
                                     department: str,
                                     action: ActionRequired) -> List[str]:
        """生成建议的追问"""
        # 根据科室和问题类型生成追问
        suggestions = []

        if department == "内科":
            if "血压" in question or "高血压" in question:
                suggestions = [
                    "血压控制情况如何？",
                    "目前是否在服用降压药？",
                    "有无头晕、头痛等不适？"
                ]
            elif "糖尿病" in question or "血糖" in question:
                suggestions = [
                    "空腹血糖和餐后血糖是多少？",
                    "有无使用胰岛素或口服降糖药？",
                    "有无多饮、多尿、体重下降？"
                ]
            elif "失眠" in question or "睡眠" in question:
                suggestions = [
                    "失眠多长时间了？",
                    "入睡困难还是早醒？",
                    "白天精神状态如何？"
                ]

        elif department == "眼科":
            suggestions = [
                "视力下降多长时间了？",
                "是一只眼还是两只眼？",
                "有无眼睛疼痛、流泪？"
            ]

        elif department == "精神科":
            if "抑郁" in question:
                suggestions = [
                    "情绪低落多长时间了？",
                    "对平时感兴趣的事情还有兴趣吗？",
                    "有无消极念头？"
                ]
            elif "失眠" in question:
                suggestions = [
                    "失眠多长时间了？",
                    "有无入睡困难或早醒？",
                    "有无焦虑、担心？"
                ]

        # 如果没有特定建议，返回通用建议
        if not suggestions:
            suggestions = [
                "这个问题多长时间了？",
                "有什么诱因吗？",
                "有没有做过检查？"
            ]

        return suggestions

    def _generate_referral_advice(self, question: str, target_dept: str) -> str:
        """生成转诊建议"""
        advices = {
            "眼科": "建议您到眼科进行视力、眼底等相关检查",
            "耳鼻喉科": "建议您到耳鼻喉科进行专科检查",
            "口腔科": "建议您到口腔科进行牙齿检查和治疗",
            "皮肤科": "建议您到皮肤科进行专科诊断和治疗",
            "精神科": "如果症状持续，建议到精神科/心理科就诊",
            "妇产科": "建议您到妇产科进行专科检查",
            "儿科": "建议您到儿科就诊",
            "肿瘤科": "建议您到肿瘤科进行专科评估",
            "男科": "建议您到男科进行专科检查",
        }

        base_advice = advices.get(target_dept, f"建议您到{target_dept}就诊")

        return f"{base_advice}，以获得专业的诊断和治疗。"

    def _generate_general_advice(self, question: str, target_dept: str) -> str:
        """生成一般建议"""
        general_advices = {
            "眼科": "在等待就诊期间，注意用眼卫生，避免长时间用眼",
            "耳鼻喉科": "注意休息，避免用力擤鼻涕",
            "口腔科": "注意口腔卫生，暂时避免用患侧咀嚼",
            "皮肤科": "避免搔抓，注意保持皮肤清洁",
            "精神科": "注意休息，适当放松，避免过度紧张",
        }

        return general_advices.get(target_dept, "注意观察症状变化，如有加重及时就医")


class ReferralRecommendationGenerator:
    """转诊建议生成器"""

    def generate_referral_response(self, analysis: QuestionAnalysis,
                                   urgent: bool = False) -> str:
        """
        生成转诊响应

        Args:
            analysis: 问题分析结果
            urgent: 是否紧急

        Returns:
            转诊建议文本
        """
        if urgent:
            return (f"【紧急】关于{analysis.question}的问题，"
                   f"这可能需要紧急处理。建议您尽快到{analysis.department}就诊。")

        # 一般转诊
        parts = []

        if analysis.general_advice:
            parts.append(f"一般建议：{analysis.general_advice}")

        if analysis.referral_advice:
            parts.append(f"转诊建议：{analysis.referral_advice}")

        return "。".join(parts) + "。"


class EnhancedInquiryThresholdValidator:
    """增强的追问阈值验证器（带优先级）"""

    def __init__(self):
        self.prioritizer = QuestionPrioritizer()
        self.referral_generator = ReferralRecommendationGenerator()

    def generate_threshold_rules_with_priority(self,
                                               task: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成带优先级的追问阈值规则

        Args:
            task: 任务字典

        Returns:
            增强的追问阈值规则
        """
        # 提取患者问题
        ticket = task.get("ticket", "")
        current_dept = task.get("metadata", {}).get("department_cn", "内科")

        # 分离多个问题
        questions = self._split_questions(ticket)

        # 如果只有一个问题，使用原有逻辑
        if len(questions) <= 1:
            return self._generate_simple_rules(task)

        # 多个问题：使用优先级判断
        analyses = self.prioritizer.prioritize_questions(questions, current_dept)

        # 生成增强规则
        enhanced_rules = self._generate_enhanced_rules(analyses, current_dept, task)

        return enhanced_rules

    def _split_questions(self, text: str) -> List[str]:
        """分离多个问题"""
        # 按标点符号分割
        separators = ['？', r'\?', '；', ';', '，', ',', '。']
        questions = []

        current = ""
        for char in text:
            current += char
            if char in separators:
                if current.strip():
                    questions.append(current.strip())
                current = ""

        if current.strip():
            questions.append(current.strip())

        # 过滤太短的问题
        questions = [q for q in questions if len(q) >= 3]

        return questions

    def _generate_simple_rules(self, task: Dict) -> Dict:
        """生成简单规则（单问题）"""
        # 这里可以调用原有的inquiry_threshold_validator
        # 简化起见，返回基础规则
        return {
            "scenario_type": "INFORMATION_QUERY",
            "risk_level": "LOW",
            "threshold_config": {
                "min_questions_before_advice": 2,
                "allowed_response_type": "FULL_ADVICE"
            }
        }

    def _generate_enhanced_rules(self, analyses: List[QuestionAnalysis],
                                current_dept: str,
                                task: Dict) -> Dict[str, Any]:
        """生成增强规则"""
        # 分类问题
        core_questions = [a for a in analyses if a.priority == QuestionPriority.CRITICAL]
        high_priority_questions = [a for a in analyses if a.priority == QuestionPriority.HIGH]
        other_dept_questions = [a for a in analyses if not a.is_current_dept]

        # 确定风险等级
        if any(a.priority == QuestionPriority.CRITICAL for a in analyses):
            risk_level = "HIGH"
        elif any(a.priority == QuestionPriority.HIGH for a in analyses):
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # 确定最小问题数
        base_min_questions = {
            "HIGH": 4,
            "MEDIUM": 3,
            "LOW": 2
        }.get(risk_level, 2)

        # 如果有其他科室问题，增加问题数
        if other_dept_questions:
            min_questions = base_min_questions + len(other_dept_questions)
        else:
            min_questions = base_min_questions

        # 生成必须问的问题
        must_ask = []
        for analysis in high_priority_questions:
            must_ask.extend(analysis.suggested_questions[:2])

        # 生成可选问题
        should_ask = []
        for analysis in other_dept_questions:
            should_ask.extend(analysis.suggested_questions[:1])

        # 生成转诊建议
        referral_items = []
        for analysis in other_dept_questions:
            referral_text = self.referral_generator.generate_referral_response(analysis)
            referral_items.append({
                "question": analysis.question,
                "target_dept": analysis.department,
                "advice": referral_text
            })

        # 返回增强规则
        return {
            "scenario_type": "MULTI_DEPARTMENT_CONSULTATION",
            "risk_level": risk_level,
            "priority_analysis": {
                "core_questions": [
                    {
                        "question": a.question,
                        "department": a.department,
                        "action": a.action_required.value
                    }
                    for a in core_questions
                ],
                "current_dept_questions": len(high_priority_questions),
                "other_dept_questions": len(other_dept_questions)
            },
            "threshold_config": {
                "min_questions_before_advice": min_questions,
                "allowed_response_type": "FULL_ADVICE_WITH_REFERRAL",
                "threshold_penalty": "WARNING"
            },
            "inquiry_strategy": {
                "must_ask": must_ask,
                "should_ask": should_ask,
                "other_dept_handling": "general_advice_and_referral"
            },
            "referral_recommendations": referral_items,
            "evaluation_rules": [
                f"🏥 多科室咨询场景：{len(analyses)}个问题涉及{len(set(a.department for a in analyses))}个科室",
                f"📋 核心问题：{len(high_priority_questions)}个（当前科室）",
                f"🔄 转诊问题：{len(other_dept_questions)}个（其他科室）",
                f"❓ 最小问题数：{min_questions}个",
                "⚠️ 必须对当前科室问题详细问诊",
                "➕ 对其他科室问题给予一般建议并转诊"
            ]
        }


# 便捷函数
def analyze_patient_questions(ticket: str, current_dept: str = "内科") -> Dict[str, Any]:
    """
    分析患者问题

    Args:
        ticket: 患者问题描述
        current_dept: 当前科室

    Returns:
        分析结果
    """
    validator = EnhancedInquiryThresholdValidator()

    # 构造临时任务
    temp_task = {
        "ticket": ticket,
        "metadata": {
            "department_cn": current_dept
        }
    }

    # 生成增强规则
    enhanced_rules = validator.generate_threshold_rules_with_priority(temp_task)

    return enhanced_rules


if __name__ == "__main__":
    # 测试
    test_cases = [
        ("高血压能吃党参吗？眼睛老花？失眠？会抑郁吗？", "内科"),
        ("胸痛呼吸困难，能吃心脏病药吗？", "内科"),
        ("宝宝发烧咳嗽，能吃退烧药吗？皮肤起红点怎么办？", "儿科"),
    ]

    for ticket, dept in test_cases:
        print(f"\n{'='*60}")
        print(f"患者问题: {ticket}")
        print(f"当前科室: {dept}")
        print(f"{'='*60}")

        result = analyze_patient_questions(ticket, dept)

        print(json.dumps(result, ensure_ascii=False, indent=2))
