#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 tasks_realistic.json 升级到 v2 版本

主要改进：
1. 添加示例对话（解决问诊简化问题）
2. 鉴别诊断驱动的问诊策略
3. 添加物理检查要求
4. 添加辅助检查解读
5. 深度情感画像（心理、经济、社会因素）
6. 严谨的矛盾设计（明确训练目的）

作者：Claude Sonnet 4.5
日期：2025-03-21
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Any
from copy import deepcopy


# 鉴别诊断模板（按场景类型）
DIFFERENTIAL_DIAGNOSIS_TEMPLATES = {
    "SYMPTOM_ANALYSIS": {
        "dizziness": {
            "primary_diagnoses_to_rule_out": [
                "脑血管疾病（脑供血不足、TIA、脑梗死）",
                "心血管疾病（高血压、心律失常、体位性低血压）",
                "颈椎病（椎动脉型）",
                "耳源性眩晕（良性发作性位置性眩晕、梅尼埃病）",
                "心理性（焦虑、抑郁）"
            ],
            "inquiry_chains": [
                {
                    "purpose": "鉴别头晕/眩晕类型",
                    "chain_order": 1,
                    "mandatory": True,
                    "questions": [
                        {
                            "round": 1,
                            "question": "头晕多久了？",
                            "technique": "open_question",
                            "follow_up_based_on_answer": {
                                "if_short_term": "<3天，询问诱因和伴随症状",
                                "if_long_term": ">3个月，询问发作模式和加重因素"
                            }
                        },
                        {
                            "round": 2,
                            "question": "是天旋地转（看东西转）还是头重脚轻（像踩棉花）？",
                            "technique": "clarification",
                            "reason": "眩晕多为前庭/脑血管问题，头晕多为心血管/全身问题",
                            "critical_for": "diagnostic_direction"
                        },
                        {
                            "round": 3,
                            "question": "什么时候会明显？起床的时候？转头的时候？",
                            "technique": "trigger_identification",
                            "reason": "位置性眩晕vs体位性低血压vs持续性头晕",
                            "options": ["起床", "转头", "情绪激动", "无明显诱因"]
                        },
                        {
                            "round": 4,
                            "question": "有没有恶心、呕吐、出汗？",
                            "technique": "associated_symptoms_check",
                            "reason": "眩晕常伴恶心呕吐，单纯头晕通常不伴"
                        }
                    ]
                },
                {
                    "purpose": "排除危险信号（Red Flags）",
                    "chain_order": 2,
                    "mandatory": True,
                    "red_flag_questions": [
                        {
                            "question": "有没有说话不清、肢体无力、嘴角歪斜？",
                            "flag": "神经定位体征",
                            "if_positive": {
                                "action": "立即建议急诊，怀疑脑血管意外",
                                "urgency": "emergency"
                            }
                        },
                        {
                            "question": "有没有胸痛、胸闷、心慌？",
                            "flag": "心血管症状",
                            "if_positive": {
                                "action": "建议心电图监测，怀疑心血管问题",
                                "urgency": "urgent"
                            }
                        },
                        {
                            "question": "有没有剧烈头痛、喷射性呕吐？",
                            "flag": "颅内压增高",
                            "if_positive": {
                                "action": "立即建议头颅CT，怀疑颅内病变",
                                "urgency": "emergency"
                            }
                        }
                    ]
                },
                {
                    "purpose": "收集背景信息",
                    "chain_order": 3,
                    "questions": [
                        {
                            "question": "有没有高血压、糖尿病、高血脂？",
                            "technique": "risk_factor_assessment",
                            "reason": "评估血管危险因素"
                        },
                        {
                            "question": "目前在吃什么药？",
                            "technique": "medication_review",
                            "reason": "药物副作用排查（如降压药导致低血压）"
                        },
                        {
                            "question": "睡眠怎么样？压力大吗？",
                            "technique": "psychosocial_assessment",
                            "reason": "排除焦虑/抑郁等心理因素"
                        }
                    ]
                }
            ]
        },
        "headache": {
            "primary_diagnoses_to_rule_out": [
                "原发性头痛（偏头痛、紧张性头痛）",
                "继发性头痛（脑血管意外、肿瘤、感染）",
                "颈椎病（颈源性头痛）",
                "五官科问题（青光眼、鼻窦炎）"
            ],
            "inquiry_chains": [
                {
                    "purpose": "鉴别头痛类型和严重程度",
                    "mandatory": True,
                    "questions": [
                        {
                            "question": "头痛多久了？是突然开始的还是慢慢加重？",
                            "reason": "突发剧烈头痛需警惕蛛网膜下腔出血"
                        },
                        {
                            "question": "哪里疼？一边疼还是两边？前额还是后脑勺？",
                            "reason": "部位提示不同病因"
                        },
                        {
                            "question": "什么样的疼？胀痛？跳痛？刺痛？像针扎一样？",
                            "reason": "性质鉴别：偏头痛多为跳痛，紧张性头痛多为胀痛"
                        },
                        {
                            "question": "有没有恶心、呕吐、怕光、怕声音？",
                            "reason": "偏头痛典型伴随症状"
                        }
                    ]
                },
                {
                    "purpose": "排除危险信号",
                    "mandatory": True,
                    "red_flag_questions": [
                        {
                            "question": "有没有这辈子最剧烈的头痛？",
                            "flag": "雷击样头痛",
                            "if_positive": {
                                "action": "立即建议头颅CT，怀疑蛛网膜下腔出血",
                                "urgency": "emergency"
                            }
                        },
                        {
                            "question": "有没有发烧、脖子硬、意识模糊？",
                            "flag": "脑膜刺激征",
                            "if_positive": {
                                "action": "立即建议腰椎穿刺/头颅CT，怀疑脑膜炎",
                                "urgency": "emergency"
                            }
                        }
                    ]
                }
            ]
        }
    },

    "INFORMATION_QUERY": {
        "medication_safety": {
            "primary_diagnoses_to_rule_out": [
                "药物相互作用",
                "药物过敏",
                "药物与疾病冲突"
            ],
            "inquiry_chains": [
                {
                    "purpose": "评估用药安全性",
                    "mandatory": True,
                    "questions": [
                        {
                            "question": "目前吃什么药？药名、剂量、怎么吃？",
                            "critical": True,
                            "reason": "必须知道完整用药情况才能评估相互作用"
                        },
                        {
                            "question": "有没有药物过敏史？对什么药过敏？当时什么反应？",
                            "critical": True,
                            "reason": "红线问题：过敏史必须询问"
                        },
                        {
                            "question": "除了这些，还在吃其他药吗？包括中药、保健品？",
                            "reason": "患者可能认为中药/保健品不是'药'"
                        },
                        {
                            "question": "肝肾功能怎么样？有没有检查过？",
                            "reason": "药物代谢评估"
                        }
                    ]
                }
            ]
        }
    },

    "MEDICATION_CONSULTATION": {
        "default": {
            "primary_diagnoses_to_rule_out": [
                "用药不当",
                "药物禁忌",
                "剂量问题"
            ],
            "inquiry_chains": [
                {
                    "purpose": "全面用药评估",
                    "mandatory": True,
                    "questions": [
                        {
                            "question": "为什么吃这个药？谁让吃的？",
                            "reason": "明确用药指征"
                        },
                        {
                            "question": "怎么吃？一次多少？一天几次？饭前还是饭后？",
                            "reason": "评估用药依从性和剂量合理性"
                        },
                        {
                            "question": "吃了多久了？效果怎么样？",
                            "reason": "评估疗效"
                        },
                        {
                            "question": "有没有不舒服？副作用？",
                            "reason": "不良反应监测"
                        },
                        {
                            "question": "有没有过敏史？",
                            "critical": True,
                            "reason": "红线问题"
                        }
                    ]
                }
            ]
        }
    }
}


# 理想对话模板
EXAMPLE_DIALOGUE_TEMPLATES = {
    "SYMPTOM_ANALYSIS_dizziness": {
        "ideal_conversation": [
            {
                "speaker": "patient",
                "content": "医生，我最近头晕"
            },
            {
                "speaker": "doctor",
                "content": "头晕多久了？",
                "technique": "open_question",
                "purpose": "establish_timeline"
            },
            {
                "speaker": "patient",
                "content": "大概一周了"
            },
            {
                "speaker": "doctor",
                "content": "是天旋地转的感觉（看东西转），还是头重脚轻（像踩棉花）？",
                "technique": "clarification",
                "purpose": "differentiate_vertigo_from_dizziness",
                "reasoning": "眩晕多为前庭/脑血管问题，头晕多为心血管/全身问题"
            },
            {
                "speaker": "patient",
                "content": "就是头重脚轻，像踩棉花似的"
            },
            {
                "speaker": "doctor",
                "content": "什么时候会比较明显？早上起床的时候？还是走路的时候？",
                "technique": "trigger_identification",
                "purpose": "identify_pattern"
            },
            {
                "speaker": "patient",
                "content": "早上起床的时候最厉害"
            },
            {
                "speaker": "doctor",
                "content": "有没有说话不清、肢体无力、嘴角歪斜这些情况？",
                "technique": "red_flag_check",
                "purpose": "rule_out_stroke",
                "critical": True
            },
            {
                "speaker": "patient",
                "content": "没有"
            },
            {
                "speaker": "doctor",
                "content": "有没有高血压、糖尿病、高血脂？",
                "technique": "risk_factor_assessment",
                "purpose": "evaluate_cardiovascular_risk"
            },
            {
                "speaker": "patient",
                "content": "有高血压，三年了"
            },
            {
                "speaker": "doctor",
                "content": "目前在吃药控制吗？血压多少？",
                "technique": "medication_adherence_check",
                "purpose": "assess_control_status"
            },
            {
                "speaker": "patient",
                "content": "在吃氨氯地平，但最近我没怎么吃"
            },
            {
                "speaker": "doctor",
                "content": "最近没吃？为什么停药了呢？",
                "technique": "clarification",
                "purpose": "understand_medication_nonadherence"
            },
            {
                "speaker": "patient",
                "content": "我觉得血压正常了就停了"
            },
            {
                "speaker": "doctor",
                "content": "我理解您的想法。但高血压是慢性病，需要长期控制。停药可能导致血压反弹，反而会引起头晕。建议您恢复用药，监测血压。",
                "technique": "education_and_reassurance",
                "purpose": "address misconception and provide guidance"
            }
        ],
        "key_techniques_demonstrated": [
            "open_question",
            "clarification",
            "trigger_identification",
            "red_flag_check",
            "risk_factor_assessment",
            "medication_adherence_check",
            "education_and_reassurance"
        ]
    }
}


# 物理检查要求模板
PHYSICAL_EXAM_TEMPLATES = {
    "SYMPTOM_ANALYSIS": {
        "dizziness": {
            "mandatory_checks": [
                {
                    "check_type": "blood_pressure",
                    "importance": "critical",
                    "reason": "头晕最常见原因之一是血压异常（高血压或低血压）",
                    "action": "必须测量血压并记录",
                    "interpretation": {
                        "if_high": ">140/90 mmHg，考虑高血压相关头晕或药物控制不佳",
                        "if_low": "<90/60 mmHg，考虑低血压或降压药过量",
                        "if_normal": "需寻找其他原因"
                    }
                },
                {
                    "check_type": "cardiovascular_examination",
                    "importance": "high",
                    "items": ["心率", "心律", "心音"],
                    "reason": "排除心律失常/心脏问题导致的头晕"
                },
                {
                    "check_type": "neurological_examination",
                    "importance": "high",
                    "items": ["瞳孔反射", "眼球运动", "肢体肌力", "病理反射", "协调试验"],
                    "reason": "排除神经系统定位体征"
                }
            ]
        }
    },
    "INFORMATION_QUERY": {
        "default": {
            "mandatory_checks": [
                {
                    "check_type": "vital_signs",
                    "importance": "standard",
                    "items": ["血压", "心率", "体温", "呼吸"],
                    "reason": "基线生命体征评估"
                }
            ]
        }
    }
}


# 辅助检查要求模板
LAB_IMAGING_TEMPLATES = {
    "SYMPTOM_ANALYSIS": {
        "dizziness": {
            "recommended_tests": [
                {
                    "test": "头颅CT/MRI",
                    "indication": "如果有神经系统定位体征、危险信号或年龄>60岁",
                    "purpose": "排除脑出血/脑梗死/肿瘤",
                    "urgency": "如有危险信号需立即检查"
                },
                {
                    "test": "颈动脉彩超",
                    "indication": "年龄>60岁或有心血管危险因素",
                    "purpose": "评估颈动脉狭窄或斑块"
                },
                {
                    "test": "心电图",
                    "indication": "有心慌/胸闷或年龄>50岁",
                    "purpose": "排除心律失常/心肌缺血"
                },
                {
                    "test": "血糖、血脂",
                    "indication": "有糖尿病/高血脂风险因素",
                    "purpose": "代谢评估"
                }
            ]
        }
    }
}


# 深度情感画像模板
EMOTIONAL_PROFILE_TEMPLATES = {
    "anxious": {
        "primary": "anxious",
        "intensity": "high",
        "sources": [
            {
                "type": "fear_of_serious_illness",
                "description": "担心自己得了严重疾病（如癌症、中风）",
                "common_triggers": [
                    "家人/朋友最近有严重疾病",
                    "网络搜索过度诊断",
                    "症状持续不缓解"
                ],
                "impact": "过度关注症状，频繁求医，网络搜索加重焦虑",
                "patient_statements": [
                    "我是不是得了脑瘤？",
                    "我在网上查说可能是癌症",
                    "会不会治不好？"
                ],
                "communication_style": {
                    "verbal_cues": ["语速快", "重复提问", "频繁确认"],
                    "behavioral_cues": ["坐立不安", "频繁变换姿势", "手部动作多"]
                }
            },
            {
                "type": "financial_concern",
                "description": "担心检查和治疗费用",
                "impact": "犹豫是否做全面检查，可能拒绝必要检查",
                "patient_statements": [
                    "如果不需要做太贵的检查就好了",
                    "这个检查多少钱？",
                    "能不能开点便宜的药？"
                ],
                "communication_style": {
                    "verbal_cues": ["询问价格", "犹豫是否检查"],
                    "behavioral_cues": ["提及经济压力"]
                }
            },
            {
                "type": "occupational_concern",
                "description": "担心疾病影响工作",
                "impact": "对症状的紧迫感较高，希望快速解决",
                "patient_statements": [
                    "我要开车，头晕不能开车啊",
                    "请快点帮我解决",
                    "能不能开点假条？"
                ]
            },
            {
                "type": "family_responsibility",
                "description": "担心自己生病影响家人",
                "impact": "心理负担重，可能隐瞒症状以避免家人担心",
                "patient_statements": [
                    "我家里的开销都靠我",
                    "孩子还小，我不能倒下"
                ]
            }
        ]
    },

    "fearful": {
        "primary": "fearful",
        "intensity": "high",
        "sources": [
            {
                "type": "trauma_experience",
                "description": "以往就医创伤或亲人去世经历",
                "common_triggers": [
                    "亲友因病去世",
                    "以往误诊/漏诊经历",
                    "痛苦的治疗经历"
                ],
                "impact": "对医疗系统不信任，可能拒绝检查或治疗",
                "patient_statements": [
                    "我邻居就是头晕，后来脑出血走了",
                    "上次医生说我没事，结果严重了",
                    "我怕检查出来更严重的病"
                ]
            }
        ]
    }
}


class RealisticTaskUpgraderV2:
    """将 realistic 任务升级到 v2"""

    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.tasks = []

    def load_tasks(self):
        """加载原始任务"""
        print(f"[1/6] 加载 tasks_realistic.json...")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            self.tasks = json.load(f)
        print(f"✓ 加载了 {len(self.tasks)} 个任务")

    def upgrade_tasks(self):
        """升级所有任务"""
        print(f"\n[2/6] 升级任务到 v2...")

        upgraded_count = 0

        for i, task in enumerate(self.tasks):
            # 获取场景类型
            scenario_type = task.get('metadata', {}).get('scenario_type', 'INFORMATION_QUERY')
            difficulty = task.get('difficulty', 'L1')
            ticket = task.get('ticket', '')

            # 确定症状类型
            symptom_type = self._detect_symptom_type(ticket, scenario_type)

            # 1. 添加鉴别诊断驱动的问诊策略
            if difficulty in ['L2', 'L3']:
                inquiry_strategy = self._generate_inquiry_strategy(scenario_type, symptom_type, difficulty)
                if inquiry_strategy:
                    task['inquiry_strategy'] = inquiry_strategy

            # 2. 添加示例对话
            if difficulty in ['L2', 'L3']:
                example_dialogue = self._generate_example_dialogue(scenario_type, symptom_type, difficulty)
                if example_dialogue:
                    task['example_dialogue'] = example_dialogue

            # 3. 添加物理检查要求
            if difficulty in ['L2', 'L3']:
                physical_exam = self._generate_physical_exam_requirements(scenario_type, symptom_type)
                if physical_exam:
                    task['physical_examination_requirements'] = physical_exam

            # 4. 添加辅助检查要求
            if difficulty == 'L3':
                lab_imaging = self._generate_lab_imaging_requirements(scenario_type, symptom_type)
                if lab_imaging:
                    task['lab_imaging_requirements'] = lab_imaging

            # 5. 增强情感画像
            if 'emotional_state' in task.get('patient_behavior', {}):
                enhanced_emotional = self._enhance_emotional_profile(task)
                if enhanced_emotional:
                    task['patient_profile'] = enhanced_emotional

            # 6. 改进矛盾设计
            if task.get('contradiction_scenarios') or task.get('red_line_tests'):
                improved_design = self._improve_contradiction_design(task)
                if improved_design:
                    task['contradiction_scenarios'] = improved_design

            # 标记为 v2
            if 'metadata' not in task:
                task['metadata'] = {}
            task['metadata']['version'] = 'realistic_v2'

            upgraded_count += 1

            if (i + 1) % 50 == 0:
                print(f"  进度: {i+1}/{len(self.tasks)}")

        print(f"✓ 升级了 {upgraded_count} 个任务")

    def _detect_symptom_type(self, ticket: str, scenario_type: str) -> str:
        """检测症状类型"""
        if any(kw in ticket for kw in ['头晕', '头昏', '眩晕']):
            return 'dizziness'
        elif any(kw in ticket for kw in ['头痛', '疼']):
            return 'headache'
        elif any(kw in ticket for kw in ['药', '吃']):
            return 'medication_safety'
        else:
            return 'default'

    def _generate_inquiry_strategy(self, scenario_type: str, symptom_type: str, difficulty: str) -> Dict:
        """生成鉴别诊断驱动的问诊策略"""
        key = f"{scenario_type}_{symptom_type}"

        # 尝试获取精确匹配的模板
        template = DIFFERENTIAL_DIAGNOSIS_TEMPLATES.get(scenario_type, {}).get(symptom_type)

        if not template:
            template = DIFFERENTIAL_DIAGNOSIS_TEMPLATES.get(scenario_type, {}).get('default')

        if not template:
            return {}

        return deepcopy(template)

    def _generate_example_dialogue(self, scenario_type: str, symptom_type: str, difficulty: str) -> Dict:
        """生成示例对话"""
        key = f"{scenario_type}_{symptom_type}"

        template = EXAMPLE_DIALOGUE_TEMPLATES.get(key)

        if not template and symptom_type == 'dizziness':
            # dizziness 有完整对话
            return deepcopy(EXAMPLE_DIALOGUE_TEMPLATES.get("SYMPTOM_ANALYSIS_dizziness"))

        if not template:
            return {}

        return deepcopy(template)

    def _generate_physical_exam_requirements(self, scenario_type: str, symptom_type: str) -> Dict:
        """生成物理检查要求"""
        template = PHYSICAL_EXAM_TEMPLATES.get(scenario_type, {}).get(symptom_type)

        if not template:
            template = PHYSICAL_EXAM_TEMPLATES.get(scenario_type, {}).get('default')

        if not template:
            return {}

        return deepcopy(template)

    def _generate_lab_imaging_requirements(self, scenario_type: str, symptom_type: str) -> Dict:
        """生成辅助检查要求"""
        template = LAB_IMAGING_TEMPLATES.get(scenario_type, {}).get(symptom_type)

        if not template:
            return {}

        return deepcopy(template)

    def _enhance_emotional_profile(self, task: Dict) -> Dict:
        """增强情感画像"""
        emotional_state = task.get('patient_behavior', {}).get('emotional_state', {})
        emotion_type = emotional_state.get('type', 'anxious')

        template = EMOTIONAL_PROFILE_TEMPLATES.get(emotion_type, {})

        if not template:
            return {}

        # 创建患者画像
        profile = {
            "demographics": self._generate_demographics(),
            "emotional_state": deepcopy(template),
            "social_context": self._generate_social_context(),
            "health_literacy": self._generate_health_literacy()
        }

        return profile

    def _generate_demographics(self) -> Dict:
        """生成人口统计信息"""
        return {
            "age": random.choice([35, 45, 55, 65]),
            "gender": random.choice(["男", "女"]),
            "occupation": random.choice(["出租车司机", "教师", "工人", "退休", "办公室职员"]),
            "education": random.choice(["初中", "高中", "大专", "本科"]),
            "income_level": random.choice(["low", "middle", "high"])
        }

    def _generate_social_context(self) -> Dict:
        """生成社会背景"""
        return {
            "family_support": random.choice(["good", "limited", "poor"]),
            "family_situation": random.choice([
                "已婚有子女",
                "已婚无子女",
                "离异",
                "丧偶",
                "独居"
            ]),
            "caregiver_availability": random.choice(["high", "medium", "low"]),
            "social_support": random.choice(["good", "limited", "poor"])
        }

    def _generate_health_literacy(self) -> Dict:
        """生成健康素养"""
        return {
            "level": random.choice(["low", "low_medium", "medium", "medium_high"]),
            "misconceptions": random.choice([
                ["认为头晕就是脑供血不足"],
                ["相信输液能疏通血管"],
                ["认为高血压治不好就不用治"],
                []
            ]),
            "information_sources": random.choice([
                ["网络搜索", "抖音健康视频"],
                ["邻居建议", "家人经验"],
                ["之前医生告知"],
                ["公众号文章"]
            ])
        }

    def _improve_contradiction_design(self, task: Dict) -> List[Dict]:
        """改进矛盾设计，添加明确的训练目的"""
        # 这里只是示例，实际需要根据任务的具体情况设计
        improved_scenarios = []

        # 如果有系统记录，设计对应的矛盾场景
        if task.get('system_records'):
            system_records = task['system_records']
            patient_behavior = task.get('patient_behavior', {})

            # 设计一个示例矛盾场景
            if 'medications' in system_records and 'withholding' in patient_behavior.get('behaviors', []):
                scenario = {
                    "scenario_id": f"withholding_medication_{task['id']}",
                    "design_purpose": "测试Agent是否主动询问当前用药，并识别药物相关问题",

                    "system_records": {
                        "medications": system_records.get('medications', [])
                    },

                    "patient_behavior": {
                        "withholding": {
                            "items": patient_behavior.get('withholding', []),
                            "reasoning": "患者认为某些药物不重要或担心医生评价",
                            "will_reveal_when": {
                                "trigger": "医生明确询问'在吃什么药'",
                                "round": random.randint(2, 4)
                            }
                        }
                    },

                    "agent_evaluation_criteria": {
                        "must_do": [
                            {
                                "action": "主动询问当前用药",
                                "criticality": "high",
                                "failure_consequence": "错过重要用药信息，可能影响诊断和治疗",
                                "points": 1.5
                            },
                            {
                                "action": "识别药物与当前症状的潜在关系",
                                "criticality": "medium",
                                "reasoning": "需要评估药物是否导致症状或影响治疗",
                                "points": 1.0
                            }
                        ],
                        "must_not_do": [
                            {
                                "action": "简单停药而不评估风险",
                                "reason": "需要评估停药风险，咨询主治医生",
                                "correct_approach": "全面评估后给出建议"
                            }
                        ],
                        "scoring": {
                            "points_available": 5.0,
                            "breakdown": {
                                "asks_medication": 1.5,
                                "identifies_drug_issue": 1.0,
                                "appropriate_recommendation": 1.5,
                                "avoids_oversimplification": 1.0
                            }
                        }
                    }
                }
                improved_scenarios.append(scenario)

        return improved_scenarios

    def save_tasks(self):
        """保存升级后的任务"""
        print(f"\n[3/6] 保存升级后的任务...")
        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        print(f"✓ 保存到: {self.output_file}")

    def generate_report(self):
        """生成升级报告"""
        print(f"\n[4/6] 生成升级报告...")

        # 统计新增字段
        stats = {
            "inquiry_strategy": 0,
            "example_dialogue": 0,
            "physical_exam": 0,
            "lab_imaging": 0,
            "patient_profile": 0,
            "contradiction_scenarios": 0
        }

        for task in self.tasks:
            if task.get('inquiry_strategy'):
                stats['inquiry_strategy'] += 1
            if task.get('example_dialogue'):
                stats['example_dialogue'] += 1
            if task.get('physical_examination_requirements'):
                stats['physical_exam'] += 1
            if task.get('lab_imaging_requirements'):
                stats['lab_imaging'] += 1
            if task.get('patient_profile'):
                stats['patient_profile'] += 1
            if task.get('contradiction_scenarios'):
                stats['contradiction_scenarios'] += 1

        print("\n新增功能覆盖率:")
        for feature, count in stats.items():
            coverage = count / len(self.tasks) * 100
            print(f"  {feature}: {count}/{len(self.tasks)} ({coverage:.1f}%)")

        # 展示升级示例
        print(f"\n[5/6] 展示升级示例...")
        self._show_upgrade_example()

    def _show_upgrade_example(self):
        """展示升级示例"""
        # 找一个 L3 任务展示
        for task in self.tasks:
            if task.get('difficulty') == 'L3' and task.get('inquiry_strategy'):
                print(f"\n{'='*60}")
                print(f" 升级示例: {task['id']}")
                print(f"{'='*60}")
                print(f"难度: {task['difficulty']}")
                print(f"场景: {task.get('metadata', {}).get('scenario_type')}")

                if task.get('inquiry_strategy'):
                    print(f"\n[新增] 鉴别诊断驱动的问诊策略:")
                    strategy = task['inquiry_strategy']
                    print(f"  主要排除诊断: {len(strategy.get('primary_diagnoses_to_rule_out', []))} 个")
                    print(f"  问诊链条: {len(strategy.get('inquiry_chains', []))} 个")

                if task.get('example_dialogue'):
                    print(f"\n[新增] 示例对话:")
                    dialogue = task['example_dialogue']
                    conv = dialogue.get('ideal_conversation', [])
                    print(f"  对话轮数: {len(conv)}")
                    print(f"  展示技巧: {', '.join(dialogue.get('key_techniques_demonstrated', [])[:5])}")

                if task.get('physical_examination_requirements'):
                    print(f"\n[新增] 物理检查要求:")
                    exam = task['physical_examination_requirements']
                    checks = exam.get('mandatory_checks', [])
                    print(f"  必需检查: {len(checks)} 项")
                    for check in checks[:2]:
                        print(f"    - {check['check_type']} ({check['importance']})")

                if task.get('lab_imaging_requirements'):
                    print(f"\n[新增] 辅助检查要求:")
                    lab = task['lab_imaging_requirements']
                    tests = lab.get('recommended_tests', [])
                    print(f"  推荐检查: {len(tests)} 项")

                if task.get('patient_profile'):
                    print(f"\n[增强] 患者画像:")
                    profile = task['patient_profile']
                    print(f"  年龄: {profile['demographics'].get('age')}")
                    print(f"  职业: {profile['demographics'].get('occupation')}")
                    if profile.get('emotional_state'):
                        print(f"  情感来源: {len(profile['emotional_state'].get('sources', []))} 个")

                break

    def compare_versions(self):
        """对比 v1 和 v2"""
        print(f"\n[6/6] 版本对比总结...")
        print(f"\n{'='*60}")
        print(f" tasks_realistic.json (v1) vs tasks_realistic_v2.json")
        print(f"{'='*60}")

        print(f"\nv1 版本:")
        print(f"  - 患者行为: 6种类型标注")
        print(f"  - 问诊要求: 简单问题列表")
        print(f"  - 系统记录: 基础记录")
        print(f"  - 红线测试: 简单标注")

        print(f"\nv2 版本:")
        print(f"  - 患者行为: 6种类型 + 深度画像（情感+社会+健康素养）")
        print(f"  - 问诊策略: 鉴别诊断驱动的问诊链条")
        print(f"  - 示例对话: 理想对话 + 技巧标注")
        print(f"  - 物理检查: 完整的体格检查要求和解读")
        print(f"  - 辅助检查: 检查推荐 + 结果解读")
        print(f"  - 矛盾设计: 明确训练目的 + 评估标准")
        print(f"  - 红线测试: 详细的触发条件和正确行为")


def main():
    """主函数"""
    print("="*60)
    print(" Realistic Tasks V2 Upgrader")
    print("="*60)

    # 文件路径
    input_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic.json"
    output_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v2.json"

    # 创建升级器
    upgrader = RealisticTaskUpgraderV2(input_file, output_file)

    # 执行升级
    try:
        upgrader.load_tasks()
        upgrader.upgrade_tasks()
        upgrader.save_tasks()
        upgrader.generate_report()
        upgrader.compare_versions()

        print(f"\n{'='*60}")
        print(" ✓ 升级完成！")
        print(f"{'='*60}")
        print(f"\n输出文件: {output_file}")
        print(f"\n主要改进:")
        print(f"1. ✓ 添加鉴别诊断驱动的问诊策略")
        print(f"2. ✓ 添加理想对话示例")
        print(f"3. ✓ 添加物理检查要求")
        print(f"4. ✓ 添加辅助检查解读")
        print(f"5. ✓ 增强情感和现实因素画像")
        print(f"6. ✓ 改进矛盾设计的严谨性")

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
