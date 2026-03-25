#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tasks.json Improver
任务改进工具 - 针对 chinese_internal_medicine/tasks.json

根据质量阈值评分标准改进任务数据，解决以下问题：
1. 添加患者年龄、性别等基本信息
2. 增强评估标准（准确性、安全性、完整性）
3. 添加医生端行为建模
4. 设计多轮交互任务
5. 增加患者多样性
"""

import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class TasksJsonImprover:
    """
    Tasks.json 改进器

    改进策略：
    1. 补充患者人口学信息（年龄、性别）
    2. 添加患者病史和用药信息
    3. 增强评估标准（多维度评估）
    4. 添加医生行为建模
    5. 设计多轮交互场景
    """

    # 患者多样性模板
    PATIENT_PROFILES = {
        "elderly_male": {
            "age_range": (60, 80),
            "gender": "男",
            "occupation": ["退休工人", "退休教师", "农民"],
            "emotional_state": ["担心", "焦虑", "积极配合"],
            "expression_style": "传统、保守"
        },
        "elderly_female": {
            "age_range": (60, 80),
            "gender": "女",
            "occupation": ["退休工人", "家庭主妇", "退休会计"],
            "emotional_state": ["担心", "细致", "谨慎"],
            "expression_style": "详细、啰嗦"
        },
        "middle_aged_male": {
            "age_range": (40, 59),
            "gender": "男",
            "occupation": ["教师", "工程师", "司机", "销售"],
            "emotional_state": ["务实", "忙碌", "重视健康"],
            "expression_style": "直接、简洁"
        },
        "middle_aged_female": {
            "age_range": (40, 59),
            "gender": "女",
            "occupation": ["教师", "护士", "会计", "销售"],
            "emotional_state": ["细心", "关注家人", "重视预防"],
            "expression_style": "详细、关心"
        },
        "young_male": {
            "age_range": (20, 39),
            "gender": "男",
            "occupation": ["学生", "程序员", "销售", "自由职业"],
            "emotional_state": ["好奇", "关注工作影响", "追求效率"],
            "expression_style": "直接、网络用语"
        },
        "young_female": {
            "age_range": (20, 39),
            "gender": "女",
            "occupation": ["学生", "白领", "教师", "自媒体"],
            "emotional_state": ["关注外貌", "重视预防", "细心"],
            "expression_style": "详细、理性"
        }
    }

    # 疾病相关的典型病史
    DISEASE_HISTORIES = {
        "高血压": {
            "common_symptoms": ["头晕", "头痛", "心悸", "失眠"],
            "common_medications": ["氨氯地平", "硝苯地平", "厄贝沙坦", "倍他乐克"],
            "risk_factors": ["肥胖", "高盐饮食", "缺乏运动", "家族史"],
            "common_comorbidities": ["糖尿病", "高血脂", "冠心病"]
        },
        "糖尿病": {
            "common_symptoms": ["多饮", "多尿", "多食", "体重下降"],
            "common_medications": ["二甲双胍", "胰岛素", "格列美脲"],
            "risk_factors": ["肥胖", "家族史", "缺乏运动", "不良饮食习惯"],
            "common_comorbidities": ["高血压", "高血脂", "视网膜病变"]
        },
        "冠心病": {
            "common_symptoms": ["胸痛", "胸闷", "气短", "乏力"],
            "common_medications": ["阿司匹林", "硝酸甘油", "他汀类药物"],
            "risk_factors": ["高血压", "高血脂", "吸烟", "糖尿病"],
            "common_comorbidities": ["高血压", "糖尿病", "心律失常"]
        }
    }

    # 医生行为模板
    DOCTOR_BEHAVIORS = {
        "inquiry_history": {
            "action_name": "inquire_patient_history",
            "description": "询问患者病史和症状",
            "examples": [
                "请问您这个症状持续多久了？",
                "您之前有过类似的病史吗？",
                "您平时有哪些不舒服？"
            ]
        },
        "physical_exam": {
            "action_name": "recommend_physical_exam",
            "description": "建议进行体格检查",
            "examples": [
                "我建议您测量一下血压",
                "需要检查一下心率",
                "建议做心电图检查"
            ]
        },
        "medication_advice": {
            "action_name": "provide_medication_advice",
            "description": "提供用药建议",
            "examples": [
                "建议继续服用降压药",
                "注意药物可能的副作用",
                "不要随意停药或改剂量"
            ]
        },
        "lifestyle_guidance": {
            "action_name": "provide_lifestyle_guidance",
            "description": "提供生活方式指导",
            "examples": [
                "建议低盐饮食",
                "适当运动有助于控制血压",
                "保持规律作息"
            ]
        },
        "follow_up_plan": {
            "action_name": "schedule_follow_up",
            "description": "安排随访计划",
            "examples": [
                "建议一周后复查",
                "如有不适请及时就医",
                "需要定期监测血压"
            ]
        },
        "referral": {
            "action_name": "refer_to_specialist",
            "description": "转诊专科",
            "examples": [
                "建议到心内科进一步检查",
                "需要眼科会诊",
                "建议到内分泌科就诊"
            ]
        }
    }

    def __init__(self, input_path: str, output_path: str):
        """
        初始化改进器

        Args:
            input_path: 输入的 tasks.json 文件路径
            output_path: 输出的改进后文件路径
        """
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "improved_fields": {
                "age_gender": 0,
                "medical_history": 0,
                "evaluation_criteria": 0,
                "doctor_behaviors": 0,
                "multi_turn": 0
            }
        }

    def detect_disease_from_text(self, text: str) -> str:
        """
        从文本中检测疾病类型

        Args:
            text: 输入文本

        Returns:
            疾病类型
        """
        disease_keywords = {
            "高血压": ["高血压", "血压", "降压"],
            "糖尿病": ["糖尿病", "血糖", "降糖"],
            "冠心病": ["冠心病", "心脏", "胸痛", "心绞痛"],
            "感冒": ["感冒", "发烧", "咳嗽", "流涕"],
            "胃炎": ["胃", "胃炎", "胃痛", "消化"],
            "头痛": ["头痛", "头晕", "偏头痛"]
        }

        for disease, keywords in disease_keywords.items():
            if any(keyword in text for keyword in keywords):
                return disease

        return "一般疾病"  # 默认

    def generate_patient_profile(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成患者档案

        Args:
            task: 原始任务

        Returns:
            患者档案
        """
        ticket = task.get("ticket", "")
        reason = task.get("user_scenario", {}).get("instructions", {}).get("reason_for_call", "")
        known_info = task.get("user_scenario", {}).get("instructions", {}).get("known_info", "")

        combined_text = f"{ticket} {reason} {known_info}"

        # 检测疾病类型
        disease = self.detect_disease_from_text(combined_text)

        # 从文本中提取年龄线索
        age = None
        if "68" in combined_text:
            age = 68
        elif "爷爷" in combined_text or "奶奶" in combined_text or "老年人" in combined_text:
            age = random.randint(65, 80)
        elif "中学教师" in combined_text or "老师" in combined_text:
            age = random.randint(40, 55)
        elif "我今年" in combined_text:
            # 尝试提取年龄
            import re
            age_match = re.search(r'我今年(\d+)[:岁岁]', combined_text)
            if age_match:
                age = int(age_match.group(1))

        # 如果没有检测到年龄，随机选择一个
        if age is None:
            profile_type = random.choice(list(self.PATIENT_PROFILES.keys()))
            age_range = self.PATIENT_PROFILES[profile_type]["age_range"]
            age = random.randint(*age_range)

        # 确定性别
        gender = None
        if "先生" in combined_text or "男的" in combined_text or "男性" in combined_text:
            gender = "男"
        elif "女士" in combined_text or "女的" in combined_text or "女性" in combined_text:
            gender = "女"

        # 如果没有检测到性别，根据年龄推测
        if gender is None:
            if age >= 60:
                gender = random.choice(["男", "女"])
            else:
                gender = random.choice(["男", "女"])

        # 生成病史
        disease_info = self.DISEASE_HISTORIES.get(disease, {})
        medical_history = {
            "primary_disease": disease,
            "symptoms": random.sample(disease_info.get("common_symptoms", ["不适"]), min(3, len(disease_info.get("common_symptoms", ["不适"])))),
            "current_medications": random.sample(disease_info.get("common_medications", ["未知药物"]), min(2, len(disease_info.get("common_medications", ["未知药物"])))) if disease_info else [],
            "duration": f"{random.randint(1, 10)}年" if age > 40 else f"{random.randint(1, 6)}个月",
            "risk_factors": random.sample(disease_info.get("risk_factors", ["未知"]), min(2, len(disease_info.get("risk_factors", ["未知"])))) if disease_info else []
        }

        return {
            "age": age,
            "gender": gender,
            "medical_history": medical_history,
            "occupation": random.choice(["教师", "工人", "退休", "职员", "自由职业"]),
            "emotional_state": random.choice(["担心", "焦虑", "平静", "积极配合"]),
            "education_level": random.choice(["初中", "高中", "大专", "本科"])
        }

    def enhance_evaluation_criteria(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强评估标准

        Args:
            task: 原始任务

        Returns:
            增强后的评估标准
        """
        original_criteria = task.get("evaluation_criteria", {})
        ticket = task.get("ticket", "")

        # 增强的评估标准
        enhanced = {
            "clinical_accuracy": {
                "required": True,
                "description": "医疗建议必须准确、符合临床指南",
                "check_points": [
                    "医学术语使用准确",
                    "建议符合循证医学",
                    "避免误导性信息",
                    "包含必要的注意事项"
                ],
                "weight": 0.33
            },
            "safety_check": {
                "required": True,
                "description": "必须包含安全性提示",
                "check_points": [
                    "禁忌症说明",
                    "药物副作用警告",
                    "何时需要就医",
                    "紧急情况处理"
                ],
                "weight": 0.25
            },
            "completeness": {
                "required": True,
                "description": "回答必须完整、全面",
                "check_points": [
                    "病因解释",
                    "治疗方案建议",
                    "生活方式指导",
                    "随访计划"
                ],
                "weight": 0.23
            },
            "empathy_and_communication": {
                "required": True,
                "description": "展现同理心和良好沟通",
                "check_points": [
                    "回应患者关切",
                    "语言通俗易懂",
                    "态度友善专业",
                    "鼓励患者配合治疗"
                ],
                "weight": 0.19
            },
            "original_criteria": original_criteria  # 保留原始标准
        }

        return enhanced

    def add_doctor_behaviors(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        添加医生行为建模

        Args:
            task: 原始任务

        Returns:
            医生行为列表
        """
        disease = self.detect_disease_from_text(task.get("ticket", ""))

        # 基础行为（所有任务都需要）
        required_behaviors = [
            {
                "action_id": "inquire_symptoms",
                "action_name": "询问症状详情",
                "required": True,
                "examples": [
                    "请问症状持续多久了？",
                    "有什么诱因吗？",
                    "伴随哪些不适？"
                ]
            },
            {
                "action_id": "provide_medical_advice",
                "action_name": "提供医疗建议",
                "required": True,
                "examples": [
                    "根据您的描述",
                    "建议您",
                    "一般情况下"
                ]
            }
        ]

        # 疾病特定行为
        if disease == "高血压":
            required_behaviors.extend([
                {
                    "action_id": "check_blood_pressure",
                    "action_name": "建议监测血压",
                    "required": True,
                    "examples": ["建议每天测量血压", "需要记录血压数值"]
                },
                {
                    "action_id": "medication_guidance",
                    "action_name": "用药指导",
                    "required": True,
                    "examples": ["按时服药", "不要随意停药"]
                }
            ])
        elif disease == "糖尿病":
            required_behaviors.extend([
                {
                    "action_id": "check_blood_sugar",
                    "action_name": "建议监测血糖",
                    "required": True,
                    "examples": ["建议监测空腹血糖", "需要记录血糖数值"]
                },
                {
                    "action_id": "diet_guidance",
                    "action_name": "饮食指导",
                    "required": True,
                    "examples": ["控制碳水化合物摄入", "少吃甜食"]
                }
            ])

        return required_behaviors

    def add_multi_turn_design(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加多轮交互设计

        Args:
            task: 原始任务

        Returns:
            多轮交互设计
        """
        return {
            "enabled": True,
            "rounds": [
                {
                    "round_number": 1,
                    "patient_action": "提出主诉问题",
                    "expected_doctor_response": "询问详细症状和病史",
                    "evaluation_focus": ["信息收集", "同理心"]
                },
                {
                    "round_number": 2,
                    "patient_action": "补充症状信息",
                    "expected_doctor_response": "提供初步诊断和治疗建议",
                    "evaluation_focus": ["诊断准确性", "建议合理性"]
                },
                {
                    "round_number": 3,
                    "patient_action": "询问具体治疗或用药问题",
                    "expected_doctor_response": "详细解答并提供指导",
                    "evaluation_focus": ["回答完整性", "安全性提示"]
                }
            ],
            "completion_criteria": {
                "min_rounds": 2,
                "max_rounds": 5,
                "required_elements": [
                    "症状询问",
                    "医疗建议",
                    "安全性提示",
                    "随访安排"
                ]
            }
        }

    def improve_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        改进单个任务

        Args:
            task: 原始任务

        Returns:
            改进后的任务
        """
        improved = task.copy()

        # 1. 补充患者基本信息
        patient_profile = self.generate_patient_profile(task)
        improved["patient_profile"] = patient_profile

        # 更新 initial_state 中的 age 和 gender
        if "initial_state" in improved and "initialization_actions" in improved["initial_state"]:
            for action in improved["initial_state"]["initialization_actions"]:
                if action.get("func_name") == "set_user_info":
                    if "arguments" in action:
                        action["arguments"]["age"] = patient_profile["age"]
                        action["arguments"]["gender"] = patient_profile["gender"]
                        action["arguments"]["occupation"] = patient_profile.get("occupation", "未知")
                        action["arguments"]["emotional_state"] = patient_profile.get("emotional_state", "平静")

        # 2. 增强 evaluation_criteria
        improved["evaluation_criteria_enhanced"] = self.enhance_evaluation_criteria(task)

        # 3. 添加医生行为建模
        improved["doctor_behaviors"] = self.add_doctor_behaviors(task)

        # 4. 添加多轮交互设计
        improved["multi_turn_design"] = self.add_multi_turn_design(task)

        # 5. 添加质量元数据
        improved["quality_metadata"] = {
            "improvement_version": "1.0",
            "improvement_date": datetime.now().isoformat(),
            "quality_dimensions": {
                "clinical_accuracy": {"target": 8, "max": 10},
                "scenario_realism": {"target": 7, "max": 8},
                "evaluation_completeness": {"target": 6, "max": 7},
                "difficulty_appropriateness": {"target": 4, "max": 5}
            },
            "expected_total_score": 25  # 目标总分
        }

        # 更新统计
        self.stats["improved_fields"]["age_gender"] += 1
        self.stats["improved_fields"]["medical_history"] += 1
        self.stats["improved_fields"]["evaluation_criteria"] += 1
        self.stats["improved_fields"]["doctor_behaviors"] += 1
        self.stats["improved_fields"]["multi_turn"] += 1

        return improved

    def run(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        运行改进流程

        Args:
            limit: 限制改进的任务数量（用于测试）

        Returns:
            改进结果统计
        """
        print("=" * 60)
        print("Tasks.json 改进工具")
        print("=" * 60)
        print(f"输入文件: {self.input_path}")
        print(f"输出文件: {self.output_path}")
        print()

        # 读取原始文件
        with open(self.input_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)

        self.stats["total_tasks"] = len(tasks)
        print(f"总任务数: {self.stats['total_tasks']}")

        if limit:
            tasks = tasks[:limit]
            print(f"限制改进数量: {limit}")

        print("\n开始改进任务...\n")

        # 改进每个任务
        improved_tasks = []
        for i, task in enumerate(tasks, 1):
            print(f"[{i}/{len(tasks)}] 改进任务: {task.get('id', 'unknown')}")
            improved_task = self.improve_task(task)
            improved_tasks.append(improved_task)

        # 保存改进后的文件
        print(f"\n保存改进后的文件到: {self.output_path}")
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(improved_tasks, f, indent=2, ensure_ascii=False)

        # 打印统计
        print("\n" + "=" * 60)
        print("改进完成统计")
        print("=" * 60)
        print(f"总任务数: {self.stats['total_tasks']}")
        print(f"改进字段数:")
        for field, count in self.stats["improved_fields"].items():
            print(f"  - {field}: {count}")
        print("=" * 60)

        return {
            "input_path": str(self.input_path),
            "output_path": str(self.output_path),
            "total_tasks": self.stats["total_tasks"],
            "improved_tasks": len(improved_tasks),
            "improved_fields": self.stats["improved_fields"]
        }


def main():
    """主函数"""
    # 配置路径
    input_path = "data/tau2/domains/clinical/chinese_internal_medicine/tasks.json"
    output_path = "chinese_internal_medicine_tasks_improved.json"

    # 创建改进器
    improver = TasksJsonImprover(input_path, output_path)

    # 运行改进（处理所有任务）
    result = improver.run()

    print(f"\n[OK] 改进完成！")
    print(f"输入文件: {result['input_path']}")
    print(f"输出文件: {result['output_path']}")
    print(f"改进任务数: {result['improved_tasks']}")


if __name__ == "__main__":
    main()
