#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 tasks_realistic_v2.json 升级到 v3 版本

核心改进：
1. 物理检查的感官描述和影响
2. 多轮动态工作流（开检查-等结果-调整）
3. 多种问诊模式（不只有理想化线性模式）

针对用户指出的三个根本性局限：
- 缺乏物理环境互动 → 添加感官描述和问诊影响
- 检查结果动态性缺失 → 添加多轮动态工作流
- 部分标注理想化 → 添加多种问诊模式和打断场景

作者：Claude Sonnet 4.5
日期：2025-03-21
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Any
from copy import deepcopy


# ========================================
# 改进 1: 物理检查的感官描述
# ========================================

PHYSICAL_EXAMINATION_SENSORY_TEMPLATES = {
    "SYMPTOM_ANALYSIS": {
        "dizziness": {
            "visual_findings": {
                "general_appearance": {
                    "possible_variations": [
                        {
                            "description": "患者面色正常，神志清楚，自动体位",
                            "severity": "appears_stable",
                            "interpretation": "患者整体情况稳定，无明显急症征象",
                            "impact_on_inquiry": "可以按常规节奏问诊",
                            "impact_on_urgency": "non_urgent"
                        },
                        {
                            "description": "患者面色苍白，出汗，呈痛苦面容",
                            "severity": "appears_ill",
                            "interpretation": "提示可能存在严重问题（如低血压、贫血、急性病变）",
                            "impact_on_inquiry": "需要加快评估，优先排除危险信号",
                            "impact_on_urgency": "urgent"
                        },
                        {
                            "description": "患者面色潮红，情绪焦虑，语速快",
                            "severity": "appears_anxious",
                            "interpretation": "可能为焦虑综合征或高血压",
                            "impact_on_inquiry": "需要同时评估情绪因素和躯体因素",
                            "impact_on_urgency": "moderate"
                        }
                    ]
                },
                "specific_signs": [
                    {
                        "sign": "眼睑/结膜苍白",
                        "when_present": "提示贫血",
                        "interpretation": "头晕可能为贫血导致",
                        "next_step": "询问出血史、检查血常规",
                        "impact": "如果确认贫血，需要查找贫血原因"
                    },
                    {
                        "sign": "眼球震颤",
                        "when_present": "提示前庭系统病变",
                        "interpretation": "眩晕可能为周围性（耳源性）或中枢性",
                        "next_step": "需要神经系统检查和头颅CT",
                        "impact": "鉴别诊断缩小到前庭/神经系统"
                    },
                    {
                        "sign": "瞳孔不等大",
                        "when_present": "危险信号！",
                        "interpretation": "可能提示神经系统病变（如Horner综合征、脑疝）",
                        "next_step": "立即神经影像学检查",
                        "impact": "紧急情况，不能按常规处理"
                    }
                ]
            },
            "vital_signs": {
                "blood_pressure": {
                    "variations": [
                        {
                            "value": "160/95 mmHg",
                            "measurement_context": "患者坐位，安静5分钟后测量",
                            "interpretation": "高血压2级，可能是头晕的直接原因",
                            "impact_on_treatment": "需要降压治疗，并评估靶器官损害",
                            "impact_on_inquiry": "询问高血压病史、用药情况、有无头痛"
                        },
                        {
                            "value": "85/55 mmHg",
                            "measurement_context": "卧位测量",
                            "interpretation": "低血压，可能为头晕原因（或头晕的结果）",
                            "impact_on_treatment": "需要寻找低血压原因（出血、感染、心功能不全）",
                            "impact_on_inquiry": "询问有无出血、黑便、感染症状"
                        },
                        {
                            "value": "120/80 mmHg",
                            "interpretation": "血压正常",
                            "impact_on_inquiry": "需要寻找其他头晕原因",
                            "impact_on_treatment": "不能归因于血压异常"
                        }
                    ]
                },
                "heart_rate": {
                    "variations": [
                        {
                            "value": "105次/分，律齐",
                            "interpretation": "窦性心动过速",
                            "possible_causes": ["焦虑", "贫血", "感染", "心功能不全"],
                            "impact": "需要结合其他发现判断原因"
                        },
                        {
                            "value": "55次/分，律齐",
                            "interpretation": "窦性心动过缓",
                            "possible_causes": ["运动员心率", "病态窦房结综合征", "药物影响"],
                            "impact": "询问运动史、用药史、有无晕厥"
                        },
                        {
                            "value": "80次/分，心律不齐",
                            "interpretation": "心律不齐",
                            "urgency": "需要心电图确认心律失常类型",
                            "impact": "可能为心源性头晕，需要心内科评估"
                        }
                    ]
                }
            },
            "neurological_examination": {
                "cranial_nerves": {
                    "findings": "双侧瞳孔等大等圆，对光反射灵敏",
                    "interpretation": "无定位体征"
                },
                "motor_function": {
                    "findings": "四肢肌力5级，肌张力正常",
                    "interpretation": "无明显无力或瘫痪"
                },
                "coordination": {
                    "variations": [
                        {
                            "test": "指鼻试验",
                            "finding": "协调准确",
                            "interpretation": "无小脑性共济失调"
                        },
                        {
                            "test": "Romberg征",
                            "finding": "阳性（闭眼后摇晃）",
                            "interpretation": "提示本体感觉障碍或前庭病变",
                            "impact": "鉴别诊断缩小到感觉/前庭系统"
                        }
                    ]
                }
            }
        }
    },

    "INFORMATION_QUERY": {
        "medication_safety": {
            "visual_findings": {
                "general_appearance": {
                    "description": "患者外观正常，无明显用药不良反应体征",
                    "impact": "主要依赖问诊和实验室检查"
                }
            },
            "physical_exam": {
                "skin": {
                    "check_for": ["皮疹", "黄疸", "紫癜"],
                    "interpretations": {
                        "rash": "可能为药物过敏",
                        "jaundice": "可能为药物性肝损伤",
                        "purpura": "可能为血小板减少（药物影响）"
                    }
                }
            }
        }
    }
}


# ========================================
# 改进 2: 多轮动态工作流
# ========================================

DYNAMIC_WORKFLOW_TEMPLATES = {
    "SYMPTOM_ANALYSIS": {
        "dizziness_urgent_workflow": {
            "workflow_type": "urgent_workup",
            "total_rounds": 5,

            "round_1": {
                "stage": "initial_assessment",
                "duration": "5-10分钟",
                "activities": {
                    "doctor": [
                        "快速问诊：症状、持续时间、危险信号"
                    ],
                    "patient": [
                        "描述症状：头晕3天，加重半天"
                    ]
                },
                "decision_point": {
                    "condition": "如果有危险信号（胸痛、无力、言语不清）",
                    "action": "跳到 round_2_urgent",
                    "else": "继续常规评估"
                },
                "expected_findings": {
                    "red_flags_present": False,
                    "vital_signs": "血压偏高，其他正常"
                }
            },

            "round_2": {
                "stage": "focused_history",
                "duration": "5分钟",
                "activities": {
                    "doctor": [
                        "针对性问诊：高血压病史、用药情况",
                        "物理检查：血压、心率、神经系统"
                    ],
                    "patient": [
                        "承认有高血压3年，最近停药"
                    ],
                    "physical_exam": {
                        "blood_pressure": "165/100 mmHg",
                        "heart_rate": "88次/分",
                        "neurological": "正常"
                    }
                },
                "interpretation": {
                    "primary_issue": "高血压，药物控制不佳",
                    "secondary_issue": "停药导致血压反弹"
                },
                "decision": "需要辅助检查评估靶器官损害"
            },

            "round_3": {
                "stage": "order_tests",
                "duration": "2分钟（开单）",
                "activities": {
                    "doctor": [
                        "开具检查单",
                        "解释检查必要性"
                    ],
                    "tests_ordered": [
                        {
                            "test": "头颅CT",
                            "urgency": "routine",
                            "reason": "排除颅内病变"
                        },
                        {
                            "test": "颈动脉彩超",
                            "urgency": "routine",
                            "reason": "评估颈动脉狭窄"
                        },
                        {
                            "test": "心电图",
                            "urgency": "routine",
                            "reason": "排除心律失常"
                        },
                        {
                            "test": "生化全项",
                            "urgency": "routine",
                            "reason": "评估血糖、血脂、肝肾功能"
                        }
                    ]
                },
                "patient_concerns": [
                    "需要花多少钱？",
                    "能不能不做CT？辐射大吗？"
                ],
                "doctor_response": {
                    "address_financial": "医保可以报销大部分",
                    "address_radiation": "一次CT剂量在安全范围内",
                    "emphasize_necessity": "需要排除严重情况"
                }
            },

            "round_4": {
                "stage": "results_return",
                "time_delay": "30-60分钟",
                "activities": {
                    "wait_for_results": "患者进行检查",
                    "results_come_back": {
                        "ct_brain": {
                            "finding": "未见明显异常",
                            "interpretation": "排除脑出血、脑梗死、肿瘤",
                            "impact": "降低紧迫性"
                        },
                        "carotid_ultrasound": {
                            "finding": "双侧颈动脉内膜增厚，左侧可见斑块",
                            "interpretation": "动脉粥样硬化，支持高血压诊断",
                            "impact": "需要强化降脂抗血小板治疗"
                        },
                        "ecg": {
                            "finding": "窦性心律，左室高电压",
                            "interpretation": "高血压性心脏改变",
                            "impact": "需要长期降压治疗保护心脏"
                        },
                        "labs": {
                            "glucose": "6.8 mmol/L（轻度升高）",
                            "cholesterol": "6.2 mmol/L（升高）",
                            "creatinine": "85 μmol/L（正常）",
                            "interpretation": "代谢综合征，肾功能尚可",
                            "impact": "需要生活方式干预和降脂治疗"
                        }
                    }
                },
                "doctor_adjusts_diagnosis": {
                    "initial_impression": "头晕待查：高血压？脑血管病？",
                    "updated_diagnosis": "1. 高血压3级 很高危\n2. 代谢综合征\n3. 颈动脉粥样硬化",
                    "dizziness_cause": "高血压控制不佳导致",
                    "confidence": "高（基于检查结果）"
                }
            },

            "round_5": {
                "stage": "treatment_planning",
                "duration": "10分钟",
                "activities": {
                    "doctor_explains": {
                        "diagnosis": "根据检查结果，您的头晕是因为血压太高引起的",
                        "shows_patient": [
                            "头颅CT正常，没有脑出血或梗死",
                            "心脏有一些改变，需要好好控制血压"
                        ],
                        "treatment_plan": {
                            "medications": [
                                "氨氯地平 5mg 每日1次",
                                "阿托伐他汀 20mg 每晚1次",
                                "阿司匹林 100mg 每日1次"
                            ],
                            "lifestyle": [
                                "低盐低脂饮食",
                                "规律运动",
                                "监测血压",
                                "定期复查"
                            ],
                            "follow_up": "2周后复查血压、血脂"
                        }
                    },
                    "patient_reactions": [
                        "需要长期吃药吗？",
                        "能治好吗？"
                    ],
                    "doctor_handles_concerns": {
                        "address_duration": "高血压是慢性病，需要长期控制",
                        "address_cure": "不能根治，但可以控制，不影响正常生活"
                    }
                }
            }
        }
    },

    "EMERGENCY_WORKFLOW": {
        "chest_pain_possible_ami": {
            "workflow_type": "emergency",
            "total_rounds": 6,

            "round_1": {
                "stage": "triage",
                "duration": "<2分钟",
                "critical_action": "立即评估生命体征",
                "red_flags": ["胸痛", "出汗", "呼吸困难"],
                "decision": "立即做心电图，不要等待详细病史"
            },

            "round_2": {
                "stage": "emergency_ecg",
                "duration": "<5分钟",
                "action": "心电图 stat",
                "result": "V1-V4导联ST段抬高0.3mV",
                "interpretation": "急性前壁心肌梗死",
                "immediate_action": "启动心梗预案"
            },

            "round_3": {
                "stage": "emergency_treatment",
                "duration": "simultaneous_with_round_2",
                "medications_given": [
                    "阿司匹林 300mg 嚼服",
                    "氯吡格雷 600mg 负荷量",
                    "硝酸甘油 0.5mg 舌下含服"
                ],
                "while": "同时联系导管室"
            },

            "round_4": {
                "stage": "urgent_decision",
                "duration": "<10分钟",
                "discussion": "向患者和家属解释病情",
                "recommendation": "需要立即急诊PCI（介入手术）",
                "patient_concern": "我很害怕，能不能保守治疗？",
                "doctor_response": {
                    "empathy": "我理解您的恐惧",
                    "urgency": "但这是救命手术，每分钟都有心肌细胞死亡",
                    "recommendation": "强烈建议立即手术，风险远大于收益"
                }
            },

            "round_5": {
                "stage": "transfer_to_cath_lab",
                "duration": "30-90分钟",
                "process": "转运到导管室进行PCI",
                "outcome": "血管开通，症状缓解"
            },

            "round_6": {
                "stage": "post_procedure_instructions",
                "activities": [
                    "解释手术结果",
                    "交代用药",
                    "生活方式指导",
                    "随访计划"
                ]
            }
        }
    }
}


# ========================================
# 改进 3: 多种问诊模式
# ========================================

INQUIRY_APPROACH_TEMPLATES = {
    "approaches": [
        {
            "mode": "linear_ideal",
            "name": "线性理想模式",
            "description": "按部就班，完整问诊，不遗漏关键信息",
            "when_appropriate": "患者配合，信息逐渐揭露，无明显紧急情况",
            "advantages": ["全面", "系统", "不易遗漏"],
            "disadvantages": ["可能较慢", "不适合紧急情况"],
            "characteristics": {
                "pacing": "系统但可能较慢",
                "flexibility": "低",
                "ideal_for": "初诊患者、复杂病例"
            },
            "example_pattern": [
                "主诉 → 现病史 → 既往史 → 用药史 → 过敏史 → 社会史"
            ]
        },

        {
            "mode": "focused_urgent",
            "name": "聚焦紧急模式",
            "description": "抓住重点，快速决策，优先排除危险",
            "when_appropriate": "患者有高危因素或危险信号",
            "advantages": ["快速", "针对性强", "不延误"],
            "disadvantages": ["可能遗漏非紧急信息"],
            "characteristics": {
                "pacing": "快速",
                "flexibility": "中",
                "ideal_for": "急症、高危患者"
            },
            "example_pattern": [
                "主诉 → 危险信号排查 → 快速针对性问诊 → 立即决策"
            ]
        },

        {
            "mode": "emotional_responsive",
            "name": "情绪响应模式",
            "description": "被患者情绪影响，优先安抚和检查",
            "when_appropriate": "患者焦虑严重，可能影响依从性",
            "advantages": ["建立信任", "提高依从性"],
            "disadvantages": ["可能过度检查", "可能被情绪误导"],
            "characteristics": {
                "pacing": "中等",
                "flexibility": "高",
                "ideal_for": "焦虑患者、恐惧患者"
            },
            "example_pattern": [
                "主诉 → 情绪评估 → 安抚 + 必要检查 → 解释教育"
            ]
        },

        {
            "mode": "opportunistic",
            "name": "机会主义模式",
            "description": "抓住患者主动提供的信息，灵活调整",
            "when_appropriate": "患者提供意外关键信息",
            "advantages": ["高效", "针对性"],
            "disadvantages": ["需要经验", "可能遗漏未提及的信息"],
            "characteristics": {
                "pacing": "快速调整",
                "flexibility": "很高",
                "ideal_for": "经验丰富的医生、提供信息多的患者"
            },
            "example_pattern": [
                "患者主动说'我有房颤' → 立即转向抗凝/卒中风险评估"
            ]
        },

        {
            "mode": "patient_centered",
            "name": "患者中心模式",
            "description": "围绕患者的担忧和期望展开问诊",
            "when_appropriate": "患者有明确的担忧或期望",
            "advantages": ["满意度高", "针对患者需求"],
            "disadvantages": ["可能偏离医学优先级"],
            "characteristics": {
                "pacing": "灵活",
                "flexibility": "高",
                "ideal_for": "慢性病管理、复诊患者"
            },
            "example_pattern": [
                "患者的担忧是什么？ → 患者希望解决什么？ → 围绕这些问题展开"
            ]
        }
    ],

    "scenarios_with_mode_selection": [
        {
            "scenario": "患者焦虑严重，邻居因脑出血去世",
            "appropriate_modes": ["emotional_responsive", "focused_urgent"],
            "inappropriate_modes": ["linear_ideal", "patient_centered"],
            "reasoning": "需要优先安抚情绪和排除危险，不能按部就班"
        },
        {
            "scenario": "患者主动提供关键信息'我有房颤'",
            "appropriate_modes": ["opportunistic", "focused_urgent"],
            "reasoning": "抓住关键信息，立即评估相关风险"
        },
        {
            "scenario": "患者陈述简单、配合度高",
            "appropriate_modes": ["linear_ideal"],
            "reasoning": "可以按理想流程进行完整评估"
        },
        {
            "scenario": "患者有胸痛、出汗",
            "appropriate_modes": ["focused_urgent"],
            "inappropriate_modes": ["linear_ideal", "patient_centered"],
            "reasoning": "必须快速排除危险，不能按常规节奏"
        }
    ]
}


# ========================================
# 升级器类
# ========================================

class RealisticTaskUpgraderV3:
    """将 realistic 任务升级到 v3"""

    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.tasks = []

    def load_tasks(self):
        """加载 v2 任务"""
        print(f"[1/5] 加载 tasks_realistic_v2.json...")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            self.tasks = json.load(f)
        print(f"✓ 加载了 {len(self.tasks)} 个任务")

    def upgrade_tasks(self):
        """升级所有任务到 v3"""
        print(f"\n[2/5] 升级任务到 v3...")

        upgraded_count = 0
        stats = {
            "sensory_exam": 0,
            "dynamic_workflow": 0,
            "multiple_modes": 0
        }

        for i, task in enumerate(self.tasks):
            scenario_type = task.get('metadata', {}).get('scenario_type', 'INFORMATION_QUERY')
            difficulty = task.get('difficulty', 'L1')
            ticket = task.get('ticket', '')
            symptom_type = self._detect_symptom_type(ticket, scenario_type)

            # 改进 1: 添加感官描述的物理检查
            if difficulty in ['L2', 'L3']:
                sensory_exam = self._add_sensory_examination(scenario_type, symptom_type, difficulty)
                if sensory_exam:
                    task['physical_examination_findings'] = sensory_exam
                    stats['sensory_exam'] += 1

            # 改进 2: 添加多轮动态工作流
            if difficulty == 'L3':
                dynamic_workflow = self._add_dynamic_workflow(scenario_type, symptom_type, difficulty)
                if dynamic_workflow:
                    task['dynamic_clinical_workflow'] = dynamic_workflow
                    stats['dynamic_workflow'] += 1

            # 改进 3: 添加多种问诊模式
            if difficulty in ['L2', 'L3']:
                multiple_modes = self._add_multiple_inquiry_modes(scenario_type, symptom_type, difficulty)
                if multiple_modes:
                    task['inquiry_approaches'] = multiple_modes
                    stats['multiple_modes'] += 1

            # 标记为 v3
            if 'metadata' not in task:
                task['metadata'] = {}
            task['metadata']['version'] = 'realistic_v3'

            upgraded_count += 1

            if (i + 1) % 50 == 0:
                print(f"  进度: {i+1}/{len(self.tasks)}")

        print(f"✓ 升级了 {upgraded_count} 个任务")

        return stats

    def _detect_symptom_type(self, ticket: str, scenario_type: str) -> str:
        """检测症状类型"""
        if any(kw in ticket for kw in ['头晕', '头昏', '眩晕']):
            return 'dizziness'
        elif any(kw in ticket for kw in ['头痛', '疼']):
            return 'headache'
        elif any(kw in ticket for kw in ['胸痛', '胸闷', '心慌']):
            return 'chest_pain'
        elif any(kw in ticket for kw in ['药', '吃']):
            return 'medication_safety'
        else:
            return 'default'

    def _add_sensory_examination(self, scenario_type: str, symptom_type: str, difficulty: str) -> Dict:
        """添加感官描述的物理检查"""
        template = PHYSICAL_EXAMINATION_SENSORY_TEMPLATES.get(scenario_type, {}).get(symptom_type)

        if not template:
            return {}

        # 根据难度选择合适的变体
        exam_findings = deepcopy(template)

        # 为L3任务添加更多细节
        if difficulty == 'L3':
            # 添加具体的患者反应
            if 'visual_findings' in exam_findings:
                # 随机选择一个严重程度
                variations = exam_findings['visual_findings'].get('general_appearance', {}).get('possible_variations', [])
                if variations:
                    selected = random.choice(variations)
                    exam_findings['visual_findings']['general_appearance'] = selected
                    # 移除其他变体
                    exam_findings['visual_findings']['general_appearance'].pop('possible_variations', None)

        return exam_findings

    def _add_dynamic_workflow(self, scenario_type: str, symptom_type: str, difficulty: str) -> Dict:
        """添加多轮动态工作流"""
        if scenario_type == "SYMPTOM_ANALYSIS" and symptom_type == 'dizziness':
            return deepcopy(DYNAMIC_WORKFLOW_TEMPLATES["SYMPTOM_ANALYSIS"]["dizziness_urgent_workflow"])
        elif scenario_type == "EMERGENCY_CONCERN" and symptom_type == 'chest_pain':
            return deepcopy(DYNAMIC_WORKFLOW_TEMPLATES["EMERGENCY_WORKFLOW"]["chest_pain_possible_ami"])
        else:
            return {}

    def _add_multiple_inquiry_modes(self, scenario_type: str, symptom_type: str, difficulty: str) -> Dict:
        """添加多种问诊模式"""
        # 返回模式定义和适用场景
        return deepcopy(INQUIRY_APPROACH_TEMPLATES)

    def save_tasks(self):
        """保存升级后的任务"""
        print(f"\n[3/5] 保存升级后的任务...")
        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        print(f"✓ 保存到: {self.output_file}")

    def generate_report(self, stats):
        """生成升级报告"""
        print(f"\n[4/5] 生成升级报告...")

        print("\n=== v3 改进统计 ===")
        print(f"感官描述物理检查: {stats['sensory_exam']}/{len(self.tasks)} ({stats['sensory_exam']/len(self.tasks)*100:.1f}%)")
        print(f"多轮动态工作流: {stats['dynamic_workflow']}/{len(self.tasks)} ({stats['dynamic_workflow']/len(self.tasks)*100:.1f}%)")
        print(f"多种问诊模式: {stats['multiple_modes']}/{len(self.tasks)} ({stats['multiple_modes']/len(self.tasks)*100:.1f}%)")

        # 展示升级示例
        print(f"\n[5/5] 展示升级示例...")
        self._show_upgrade_example()

    def _show_upgrade_example(self):
        """展示升级示例"""
        # 找一个 L3 任务展示
        for task in self.tasks:
            if task.get('difficulty') == 'L3' and task.get('physical_examination_findings'):
                print(f"\n{'='*60}")
                print(f" v3 升级示例: {task['id']}")
                print(f"{'='*60}")
                print(f"难度: {task['difficulty']}")
                print(f"场景: {task.get('metadata', {}).get('scenario_type')}")

                if task.get('physical_examination_findings'):
                    print(f"\n[改进1] 感官描述的物理检查:")
                    exam = task['physical_examination_findings']
                    if 'visual_findings' in exam:
                        visual = exam['visual_findings'].get('general_appearance', {})
                        if isinstance(visual, dict) and 'description' in visual:
                            print(f"  观察: {visual['description']}")
                            print(f"  解读: {visual.get('interpretation', 'N/A')}")
                            print(f"  影响: {visual.get('impact_on_inquiry', 'N/A')}")

                if task.get('dynamic_clinical_workflow'):
                    print(f"\n[改进2] 多轮动态工作流:")
                    workflow = task['dynamic_clinical_workflow']
                    print(f"  工作流类型: {workflow.get('workflow_type')}")
                    print(f"  总轮数: {workflow.get('total_rounds')}")
                    for i in range(1, min(4, workflow.get('total_rounds', 0) + 1)):
                        round_key = f"round_{i}"
                        if round_key in workflow:
                            round_info = workflow[round_key]
                            print(f"    第{i}轮: {round_info.get('stage')}")
                            print(f"      时长: {round_info.get('duration', 'N/A')}")

                if task.get('inquiry_approaches'):
                    print(f"\n[改进3] 多种问诊模式:")
                    approaches = task['inquiry_approaches'].get('approaches', [])
                    print(f"  模式数量: {len(approaches)}")
                    for approach in approaches[:3]:
                        print(f"    - {approach['mode']}: {approach['name']}")
                        print(f"      适用: {approach['when_appropriate']}")

                break

    def compare_versions(self):
        """对比 v2 和 v3"""
        print(f"\n=== 版本对比总结 ===")
        print(f"\nv2 版本:")
        print(f"  - 物理检查: 简单要求列表")
        print(f"  - 检查结果: 静态预设")
        print(f"  - 问诊策略: 理想化线性模式")

        print(f"\nv3 版本:")
        print(f"  - 物理检查: 感官描述 + 问诊影响")
        print(f"  - 检查结果: 多轮动态工作流")
        print(f"  - 问诊策略: 多种模式（线性/紧急/灵活）")

        print(f"\n局限性:")
        print(f"  ⚠️ 仍然是纯文本，无法真正观察/检查患者")
        print(f"  ⚠️多轮工作流是模拟，不是真正的时间延迟")
        print(f"  ⚠️无法穷尽所有问诊变异性")


def main():
    """主函数"""
    print("="*60)
    print(" Realistic Tasks V3 Upgrader")
    print("="*60)
    print("\n核心改进:")
    print("1. 物理检查的感官描述和问诊影响")
    print("2. 多轮动态工作流（开检查-等结果-调整）")
    print("3. 多种问诊模式（不只有理想化线性模式）")
    print("="*60)

    # 文件路径
    input_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v2.json"
    output_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v3.json"

    # 创建升级器
    upgrader = RealisticTaskUpgraderV3(input_file, output_file)

    # 执行升级
    try:
        upgrader.load_tasks()
        stats = upgrader.upgrade_tasks()
        upgrader.save_tasks()
        upgrader.generate_report(stats)
        upgrader.compare_versions()

        print(f"\n{'='*60}")
        print(" ✓ v3 升级完成！")
        print(f"{'='*60}")
        print(f"\n输出文件: {output_file}")
        print(f"\n主要改进:")
        print(f"1. ✓ 添加物理检查的感官描述和问诊影响")
        print(f"2. ✓ 添加多轮动态工作流（开检查-等结果-调整）")
        print(f"3. ✓ 添加多种问诊模式（线性/紧急/灵活/情绪响应）")
        print(f"\n仍存在的局限性:")
        print(f"⚠️ 纯文本无法真正观察/检查患者")
        print(f"⚠️ 多轮工作流是模拟，非真实时间延迟")
        print(f"⚠️ 无法穷尽所有问诊变异性")

    except Exception as e:
        print(f"\n[错误] 升级失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    import io

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 运行升级
    main()
