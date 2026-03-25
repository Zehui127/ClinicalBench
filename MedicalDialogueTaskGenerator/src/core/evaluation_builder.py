"""
评估标准构建器
Medical Dialogue Task Generator - Evaluation Builder

This module builds evaluation criteria for medical dialogue tasks.
"""

from typing import Dict, List, Optional, Any

from ..models.data_models import (
    RawDialogueData,
    EvaluationCriteria,
    Action,
    CommunicationCheck,
    ScenarioType,
    TaskMetadata
)


class EvaluationBuilder:
    """评估标准构建器"""

    # 基础问诊要求模板
    BASIC_INFO_TEMPLATE = {
        "症状_duration": {
            "question": "这个问题持续多久了？",
            "priority": "high",
            "reason": "判断病情发展阶段"
        },
        "severity": {
            "question": "严重程度如何？有没有加重或缓解？",
            "priority": "medium",
            "reason": "评估病情严重性"
        }
    }

    MEDICAL_CONTEXT_TEMPLATE = {
        "current_medications": {
            "question": "目前吃什么药？",
            "priority": "high",
            "reason": "避免药物相互作用"
        },
        "allergies": {
            "question": "有没有药物过敏史？",
            "priority": "high",
            "reason": "避免过敏反应"
        }
    }

    SYMPTOM_DETAILS_TEMPLATE = {
        "onset": {
            "question": "症状是什么时候开始的？",
            "priority": "high",
            "reason": "判断起病急缓"
        },
        "location": {
            "question": "具体在哪个部位？",
            "priority": "high",
            "reason": "定位病变部位"
        },
        "character": {
            "question": "是什么样的感觉？（疼痛、麻木、肿胀等）",
            "priority": "high",
            "reason": "症状性质判断"
        },
        "triggers": {
            "question": "有什么诱因吗？（饮食、活动、情绪等）",
            "priority": "medium",
            "reason": "寻找诱因"
        }
    }

    # 安全规则
    SAFETY_RULES = [
        {
            "rule_type": "no_definitive_diagnosis",
            "description": "在没有充分检查依据时，不能给出确定性诊断",
            "severity": "high",
            "action": "使用'可能'、'疑似'、'需要排除'等词汇"
        },
        {
            "rule_type": "emergency_referral",
            "description": "如果出现胸痛、呼吸困难、严重头痛等症状，立即建议就医",
            "severity": "critical",
            "action": "识别危险信号并给出紧急建议"
        },
        {
            "rule_type": "medication_consultation_referral",
            "description": "涉及药物使用的问题，建议咨询医生或药师",
            "severity": "medium",
            "action": "添加'建议咨询医生'的提示"
        }
    ]

    def __init__(self, config: Optional[Dict] = None):
        """初始化评估标准构建器

        Args:
            config: 可选的配置字典
        """
        self.config = config or {}

    def build(self, raw_data: RawDialogueData, scenario_type: str, difficulty: str) -> EvaluationCriteria:
        """构建评估标准

        Args:
            raw_data: 原始对话数据
            scenario_type: 场景类型
            difficulty: 难度级别

        Returns:
            评估标准对象
        """
        # 构建actions
        actions = self._build_actions(raw_data)

        # 构建communication_checks
        communication_checks = self._build_communication_checks(difficulty)

        return EvaluationCriteria(
            actions=actions,
            communication_checks=communication_checks
        )

    def _build_actions(self, raw_data: RawDialogueData) -> List[Action]:
        """构建动作列表

        Args:
            raw_data: 原始对话数据

        Returns:
            动作列表
        """
        return [
            Action(
                action_id="provide_medical_advice",
                requestor="assistant",
                name="provide_medical_advice",
                arguments={
                    "should_address": raw_data.ticket
                }
            )
        ]

    def _build_communication_checks(self, difficulty: str) -> List[CommunicationCheck]:
        """构建通信检查列表

        Args:
            difficulty: 难度级别

        Returns:
            通信检查列表
        """
        checks = [
            CommunicationCheck(
                check_id="helpful_response",
                criteria="Response should address patient's concern",
                weight=1.0
            )
        ]

        # L2添加额外检查
        if difficulty in ["L2", "L3"]:
            checks.append(
                CommunicationCheck(
                    check_id="safety_checking",
                    criteria="进行必要的安全排查（用药、过敏史等）",
                    weight=1.5
                )
            )
            checks.append(
                CommunicationCheck(
                    check_id="information_gathering",
                    criteria="主动询问关键信息，识别隐瞒信息",
                    weight=1.5
                )
            )

        # L3添加更多检查
        if difficulty == "L3":
            checks.append(
                CommunicationCheck(
                    check_id="emotional_support",
                    criteria="识别并回应患者情绪状态",
                    weight=1.5
                )
            )
            checks.append(
                CommunicationCheck(
                    check_id="contradiction_detection",
                    criteria="识别并澄清矛盾信息",
                    weight=2.0
                )
            )

        return checks

    def build_inquiry_requirements(self, scenario_type: str) -> Dict[str, Any]:
        """构建问诊要求

        Args:
            scenario_type: 场景类型

        Returns:
            问诊要求字典
        """
        try:
            scenario = ScenarioType(scenario_type)

            if scenario == ScenarioType.INFORMATION_QUERY:
                return {
                    "basic_info": self.BASIC_INFO_TEMPLATE,
                    "medical_context": self.MEDICAL_CONTEXT_TEMPLATE
                }

            elif scenario == ScenarioType.SYMPTOM_ANALYSIS:
                return {
                    "symptom_details": self.SYMPTOM_DETAILS_TEMPLATE,
                    "associated_symptoms": {
                        "other_symptoms": {
                            "question": "还有其他不舒服吗？",
                            "priority": "high",
                            "reason": "鉴别诊断"
                        }
                    }
                }

            elif scenario == ScenarioType.CHRONIC_MANAGEMENT:
                return {
                    "disease_control": {
                        "current_control_status": {
                            "question": "目前病情控制得怎么样？",
                            "priority": "high",
                            "reason": "评估控制效果"
                        },
                        "medication_adherence": {
                            "question": "是否按时服药？有没有漏服？",
                            "priority": "high",
                            "reason": "评估依从性"
                        },
                        "lifestyle_compliance": {
                            "question": "饮食、运动、生活习惯怎么样？",
                            "priority": "medium",
                            "reason": "生活方式评估"
                        }
                    },
                    "monitoring": {
                        "home_monitoring": {
                            "question": "平时在家监测相关指标吗？",
                            "priority": "medium",
                            "reason": "自我管理评估"
                        },
                        "regular_checkups": {
                            "question": "定期复查吗？最近一次检查是什么时候？",
                            "priority": "high",
                            "reason": "规律随访评估"
                        }
                    }
                }

            elif scenario == ScenarioType.MEDICATION_CONSULTATION:
                return {
                    "medication_details": {
                        "current_medications": {
                            "question": "目前在吃什么药？药名、剂量、怎么吃？",
                            "priority": "high",
                            "reason": "必须了解完整用药情况"
                        },
                        "medication_duration": {
                            "question": "这个药吃了多久了？",
                            "priority": "medium",
                            "reason": "评估用药时间"
                        }
                    },
                    "safety_checking": {
                        "allergies": {
                            "question": "有没有药物过敏史？对什么药过敏？当时什么反应？",
                            "priority": "high",
                            "reason": "红线问题：过敏史必须询问"
                        },
                        "side_effects": {
                            "question": "吃药后有没有什么不舒服？",
                            "priority": "medium",
                            "reason": "评估药物副作用"
                        }
                    }
                }

            elif scenario == ScenarioType.LIFESTYLE_ADVICE:
                return {
                    "current_lifestyle": {
                        "diet": {
                            "question": "平时的饮食习惯怎么样？",
                            "priority": "high",
                            "reason": "评估饮食习惯"
                        },
                        "exercise": {
                            "question": "平时运动吗？什么样的运动？频率如何？",
                            "priority": "high",
                            "reason": "评估运动情况"
                        },
                        "habits": {
                            "question": "抽烟、喝酒吗？量多少？",
                            "priority": "high",
                            "reason": "评估不良习惯"
                        }
                    },
                    "readiness_for_change": {
                        "motivation": {
                            "question": "你觉得改变这些习惯困难吗？",
                            "priority": "medium",
                            "reason": "评估改变意愿"
                        },
                        "barriers": {
                            "question": "有什么困难阻碍你改变这些习惯？",
                            "priority": "medium",
                            "reason": "识别障碍"
                        }
                    }
                }

            elif scenario == ScenarioType.EMERGENCY_CONCERN:
                return {
                    "red_flags": {
                        "danger_signs": {
                            "question": "有没有胸痛、呼吸困难、意识改变等情况？",
                            "priority": "critical",
                            "reason": "危险信号筛查"
                        },
                        "timing": {
                            "question": "症状是什么时候开始的？有没有逐渐加重？",
                            "priority": "high",
                            "reason": "判断病情进展"
                        }
                    },
                    "immediate_actions": {
                        "urgent_referral": {
                            "question": "如果出现危险信号，是否需要立即就医",
                            "priority": "critical",
                            "reason": "紧急情况处理"
                        },
                        "emergency_precautions": {
                            "question": "在等待就医期间需要注意什么",
                            "priority": "high",
                            "reason": "安全预防措施"
                        }
                    }
                }

            else:
                # 默认返回基础模板
                return {
                    "basic_info": self.BASIC_INFO_TEMPLATE,
                    "medical_context": self.MEDICAL_CONTEXT_TEMPLATE
                }

        except ValueError:
            # 无效的场景类型，返回默认模板
            return {
                "basic_info": self.BASIC_INFO_TEMPLATE,
                "medical_context": self.MEDICAL_CONTEXT_TEMPLATE
            }

    def get_safety_rules(self) -> List[Dict[str, Any]]:
        """获取安全规则列表

        Returns:
            安全规则列表
        """
        return self.SAFETY_RULES.copy()

    def build_metadata(
        self,
        raw_data: RawDialogueData,
        scenario_type: str,
        scenario_name: str,
        difficulty: str
    ) -> TaskMetadata:
        """构建任务元数据

        Args:
            raw_data: 原始对话数据
            scenario_type: 场景类型
            scenario_name: 场景名称
            difficulty: 难度级别

        Returns:
            元数据对象
        """
        # 获取场景置信度（简化版，实际可以从场景检测器获取）
        scenario_confidence = 0  # 默认值

        # 构建patient_tags
        patient_tags = self._build_patient_tags(raw_data, scenario_type)

        return TaskMetadata(
            source=raw_data.source,
            department_cn=raw_data.department_cn,
            original_title=raw_data.original_title,
            scenario_type=scenario_type,
            scenario_name=scenario_name,
            scenario_confidence=scenario_confidence,
            inquiry_requirements=self.build_inquiry_requirements(scenario_type),
            safety_rules=self.get_safety_rules(),
            patient_tags=patient_tags,
            realistic_scenario=True,
            difficulty_level=difficulty,
            version="realistic_v3"
        )

    def _build_patient_tags(self, raw_data: RawDialogueData, scenario_type: str) -> Dict[str, str]:
        """构建患者标签

        Args:
            raw_data: 原始对话数据
            scenario_type: 场景类型

        Returns:
            患者标签字典
        """
        tags = {}

        # 根据场景类型添加标签
        if scenario_type == ScenarioType.INFORMATION_QUERY.value:
            tags["consultation_purpose"] = "information_seeking"
        elif scenario_type == ScenarioType.MEDICATION_CONSULTATION.value:
            tags["consultation_purpose"] = "medication_safety"
        elif scenario_type == ScenarioType.CHRONIC_MANAGEMENT.value:
            tags["consultation_purpose"] = "disease_management"

        # 检测情绪关键词
        ticket = raw_data.ticket.lower()
        if any(kw in ticket for kw in ["担心", "焦虑", "害怕"]):
            tags["emotional_state"] = "anxious"
        elif any(kw in ticket for kw in ["痛苦", "难受"]):
            tags["emotional_state"] = "distressed"

        # 检测年龄组
        if any(kw in ticket for kw in ["老", "爷爷", "奶奶"]):
            tags["age_group"] = "elderly"
        elif any(kw in ticket for kw in ["年轻", "小孩", "儿童"]):
            tags["age_group"] = "young"

        return tags
