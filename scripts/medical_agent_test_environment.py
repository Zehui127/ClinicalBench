#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗Agent测试环境 - Step 3 & 4

包含：
1. API模拟器（Step 3）
2. 临床环境管理器（Step 4）
3. Agent评估器（Step 4）

基于：
- MEDICAL_AGENT_ARCHITECTURE.md
- MEDICAL_AGENT_EVALUATION_FRAMEWORK.md

作者：Claude Sonnet 4.5
日期：2025-03-21
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy


# ========================================
# Step 3: API 模拟器
# ========================================

class MockEMRAPI:
    """电子病历查询API模拟器"""

    def __init__(self, patient_data: Dict[str, Any]):
        """
        初始化EMR API

        Args:
            patient_data: 患者数据，包含病史、用药、过敏等信息
        """
        self.patient_data = patient_data

    def query(self, patient_id: str, query_type: List[str]) -> Dict[str, Any]:
        """
        查询电子病历

        Args:
            patient_id: 患者ID
            query_type: 查询类型列表
                - past_medical_history: 既往病史
                - current_medications: 当前用药
                - allergies: 过敏史
                - past_surgical_history: 手术史
                - family_history: 家族史

        Returns:
            查询结果
        """
        result = {
            "patient_id": patient_id,
            "query_type": query_type,
            "timestamp": time.time(),
            "data": {}
        }

        # 根据查询类型返回相应数据
        for qt in query_type:
            if qt == "past_medical_history":
                result["data"]["past_medical_history"] = self.patient_data.get(
                    "past_medical_history", []
                )
            elif qt == "current_medications":
                result["data"]["current_medications"] = self.patient_data.get(
                    "current_medications", []
                )
            elif qt == "allergies":
                result["data"]["allergies"] = self.patient_data.get(
                    "allergies", []
                )
            elif qt == "past_surgical_history":
                result["data"]["past_surgical_history"] = self.patient_data.get(
                    "past_surgical_history", []
                )
            elif qt == "family_history":
                result["data"]["family_history"] = self.patient_data.get(
                    "family_history", []
                )

        return result


class MockMedicationAPI:
    """药物数据库查询API模拟器"""

    def __init__(self):
        """初始化药物数据库"""
        # 模拟药物数据库
        self.medication_db = {
            "氨氯地平": {
                "contraindications": ["严重低血压", "心动过缓", "对二氢吡啶类过敏"],
                "interactions": ["地高辛（可能增加地高辛血药浓度）", "西咪替丁（可能增加氨氯地平血药浓度）"],
                "side_effects": ["水肿", "头痛", "面部潮红", "头晕", "乏力"],
                "dosage": "初始剂量2.5-5mg，每日一次，最大剂量10mg/日",
                "precautions": ["肝功能不全者减量", "避免与葡萄柚汁同服"]
            },
            "阿司匹林": {
                "contraindications": ["活动性溃疡", "出血体质", "对阿司匹林过敏"],
                "interactions": ["华法林（增加出血风险）", "NSAIDs（增加胃肠道出血风险）"],
                "side_effects": ["胃肠道出血", "溃疡", "耳鸣", "皮疹"],
                "dosage": "预防心血管事件：75-100mg/日",
                "precautions": ["饭后服用", "监测出血征象"]
            },
            "二甲双胍": {
                "contraindications": ["严重肾功能不全", "乳酸酸中毒病史", "严重感染"],
                "interactions": ["碘造影剂（可能引起乳酸酸中毒）", "酒精（增加乳酸酸中毒风险）"],
                "side_effects": ["胃肠道反应", "乳酸酸中毒（罕见）", "维生素B12缺乏"],
                "dosage": "初始500mg，每日2-3次，逐渐增至1-2g/日",
                "precautions": ["定期监测肾功能", "手术前停药"]
            }
        }

    def query(self, medication_name: str, query_type: List[str]) -> Dict[str, Any]:
        """
        查询药物信息

        Args:
            medication_name: 药物名称
            query_type: 查询类型列表
                - contraindications: 禁忌症
                - interactions: 药物相互作用
                - side_effects: 副作用
                - dosage: 剂量信息
                - precautions: 注意事项

        Returns:
            查询结果
        """
        # 从数据库中获取药物信息
        med_info = self.medication_db.get(
            medication_name,
            {
                "contraindications": ["未知"],
                "interactions": ["未知"],
                "side_effects": ["未知"],
                "dosage": "请参考药品说明书",
                "precautions": ["请参考药品说明书"]
            }
        )

        result = {
            "medication_name": medication_name,
            "query_type": query_type,
            "timestamp": time.time(),
            "data": {}
        }

        # 根据查询类型返回相应数据
        for qt in query_type:
            if qt in med_info:
                result["data"][qt] = med_info[qt]

        return result


class MockLabOrderAPI:
    """检查开具API模拟器"""

    def __init__(self):
        """初始化检查系统"""
        self.order_counter = 0

    def order_test(self, test_type: List[str], urgency: str, clinical_indication: str) -> Dict[str, Any]:
        """
        开具检查单

        Args:
            test_type: 检查类型列表（如["心电图", "血常规"]）
            urgency: 紧急程度（routine/urgent/emergency）
            clinical_indication: 临床指征

        Returns:
            检查单信息
        """
        self.order_counter += 1
        order_id = f"LAB{self.order_counter:06d}"

        # 根据紧急程度估算等待时间
        urgency_wait_times = {
            "routine": "30-60分钟",
            "urgent": "15-30分钟",
            "emergency": "立即"
        }

        result = {
            "order_id": order_id,
            "test_type": test_type,
            "urgency": urgency,
            "clinical_indication": clinical_indication,
            "estimated_time": urgency_wait_times.get(urgency, "30-60分钟"),
            "status": "pending",
            "timestamp": time.time()
        }

        return result


class MockLabResultAPI:
    """检查结果查询API模拟器"""

    def __init__(self):
        """初始化检查结果数据库"""
        # 模拟检查结果数据库
        self.result_db = {
            "LAB000001": {  # 心电图
                "test_type": "心电图",
                "results": {
                    "rhythm": "窦性心律",
                    "rate": "88次/分",
                    "axis": "正常",
                    "findings": "左室高电压",
                    "interpretation": "提示长期高血压导致的左心室肥厚"
                },
                "available_when": "30分钟后"
            },
            "LAB000002": {  # 颈动脉彩超
                "test_type": "颈动脉彩超",
                "results": {
                    "left_imt": "0.9mm",
                    "right_imt": "1.1mm",
                    "plaques": "右侧颈动脉分叉处可见低回声斑块",
                    "interpretation": "提示颈动脉粥样硬化"
                },
                "available_when": "60分钟后"
            },
            "LAB000003": {  # 血常规
                "test_type": "血常规",
                "results": {
                    "wbc": "6.5×10^9/L",
                    "rbc": "4.5×10^12/L",
                    "hb": "135g/L",
                    "plt": "220×10^9/L",
                    "interpretation": "正常范围"
                },
                "available_when": "30分钟后"
            }
        }

    def get_result(self, order_id: str) -> Dict[str, Any]:
        """
        获取检查结果

        Args:
            order_id: 检查单号

        Returns:
            检查结果
        """
        # 从数据库中获取结果
        result_data = self.result_db.get(
            order_id,
            {
                "test_type": "未知检查",
                "results": {},
                "interpretation": "结果未出或检查单不存在",
                "available_when": "请稍后查询"
            }
        )

        result = {
            "order_id": order_id,
            "timestamp": time.time(),
            "data": result_data
        }

        return result


class MockPrescriptionAPI:
    """处方开具API模拟器"""

    def __init__(self):
        """初始化处方系统"""
        self.prescription_counter = 0

    def prescribe(self, medication: str, dose: str, frequency: str,
                  duration: Optional[str] = None) -> Dict[str, Any]:
        """
        开具处方

        Args:
            medication: 药物名称
            dose: 剂量（如"5mg"）
            frequency: 用药频率（如"qd"表示每日一次）
            duration: 疗程（如"7天"）

        Returns:
            处方信息
        """
        self.prescription_counter += 1
        prescription_id = f"RX{self.prescription_counter:06d}"

        result = {
            "prescription_id": prescription_id,
            "medication": medication,
            "dose": dose,
            "frequency": frequency,
            "duration": duration,
            "status": "active",
            "timestamp": time.time()
        }

        # 检查参数完整性
        warnings = []
        if not dose:
            warnings.append("缺少剂量信息")
        if not frequency:
            warnings.append("缺少用药频率")
        if not duration:
            warnings.append("缺少疗程信息")

        if warnings:
            result["warnings"] = warnings
            result["status"] = "incomplete"

        return result


# ========================================
# Step 4: 临床环境管理器
# ========================================

@dataclass
class ToolCallResult:
    """工具调用结果"""
    success: bool
    tool_name: str
    result: Any
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class DialogueMessage:
    """对话消息"""
    role: str  # "agent" or "patient"
    content: str
    timestamp: float = field(default_factory=time.time)


class ClinicalEnvironment:
    """
    临床环境管理器

    负责管理：
    1. 可用工具（API模拟器）
    2. 环境状态
    3. Agent动作执行
    4. 患者响应生成
    """

    def __init__(self, task_config: Dict[str, Any]):
        """
        初始化临床环境

        Args:
            task_config: 任务配置（来自tasks_with_agent_workflow.json）
        """
        self.task_config = task_config
        self.task_id = task_config["id"]

        # 初始化可用工具
        self.available_tools = self._initialize_tools()

        # 初始化环境状态
        self.state = {
            "step": 0,
            "tool_calls": [],
            "dialogue_history": [],
            "pending_lab_orders": [],
            "completed_lab_orders": [],
            "prescriptions": [],
            "emr_queried": False,
            "medication_queried": False
        }

        # 患者信息（从ticket和initial_state推断）
        self.patient_info = self._initialize_patient_info()

    def _initialize_tools(self) -> Dict[str, Any]:
        """初始化可用工具"""
        tools = {}

        # 获取任务定义的可用工具
        env_tools = self.task_config.get("environment", {}).get("available_tools", {})

        # 创建工具实例
        for tool_name, tool_config in env_tools.items():
            if tool_name == "emr_query":
                # 创建患者数据
                patient_data = self._create_patient_data()
                tools[tool_name] = MockEMRAPI(patient_data)

            elif tool_name == "medication_query":
                tools[tool_name] = MockMedicationAPI()

            elif tool_name == "lab_order":
                tools[tool_name] = MockLabOrderAPI()

            elif tool_name == "lab_result_query":
                tools[tool_name] = MockLabResultAPI()

            elif tool_name == "prescription_order":
                tools[tool_name] = MockPrescriptionAPI()

        return tools

    def _create_patient_data(self) -> Dict[str, Any]:
        """创建患者数据（模拟EMR内容）"""
        # 这里可以根据任务配置生成相关的患者数据
        # 简化版：使用默认数据
        return {
            "past_medical_history": ["高血压3年", "2型糖尿病5年"],
            "current_medications": ["氨氯地平 5mg qd", "二甲双胍 500mg bid"],
            "allergies": ["青霉素"],
            "past_surgical_history": ["阑尾切除术（2010年）"],
            "family_history": ["父亲有高血压", "母亲有糖尿病"]
        }

    def _initialize_patient_info(self) -> Dict[str, Any]:
        """初始化患者信息"""
        return {
            "chief_complaint": self.task_config.get("ticket", ""),
            "difficulty": self.task_config.get("difficulty", "L1"),
            "patient_behavior": self.task_config.get("patient_behavior", {}),
            "cooperation_level": self.task_config.get("patient_behavior", {}).get("cooperation", "good")
        }

    def reset(self):
        """重置环境"""
        self.state = {
            "step": 0,
            "tool_calls": [],
            "dialogue_history": [],
            "pending_lab_orders": [],
            "completed_lab_orders": [],
            "prescriptions": [],
            "emr_queried": False,
            "medication_queried": False
        }

    def step(self, agent_action: Dict[str, Any]) -> ToolCallResult:
        """
        执行Agent动作

        Args:
            agent_action: Agent动作
                - type: "tool_call" or "dialogue"
                - tool: 工具名称（如果type是tool_call）
                - parameters: 工具参数
                - content: 对话内容（如果type是dialogue）

        Returns:
            执行结果
        """
        self.state["step"] += 1

        action_type = agent_action.get("type", "tool_call")

        if action_type == "tool_call":
            return self._execute_tool_call(agent_action)
        elif action_type == "dialogue":
            return self._execute_dialogue(agent_action)
        else:
            return ToolCallResult(
                success=False,
                tool_name="unknown",
                result=None,
                error=f"Unknown action type: {action_type}"
            )

    def _execute_tool_call(self, action: Dict[str, Any]) -> ToolCallResult:
        """执行工具调用"""
        tool_name = action.get("tool")
        parameters = action.get("parameters", {})

        # 检查工具是否可用
        if tool_name not in self.available_tools:
            return ToolCallResult(
                success=False,
                tool_name=tool_name,
                result=None,
                error=f"Tool '{tool_name}' not available"
            )

        # 调用工具
        tool = self.available_tools[tool_name]

        try:
            if tool_name == "emr_query":
                patient_id = parameters.get("patient_id", "P001")
                query_type = parameters.get("query_type", [])
                result = tool.query(patient_id, query_type)
                self.state["emr_queried"] = True

            elif tool_name == "medication_query":
                medication_name = parameters.get("medication_name", "")
                query_type = parameters.get("query_type", [])
                result = tool.query(medication_name, query_type)
                self.state["medication_queried"] = True

            elif tool_name == "lab_order":
                test_type = parameters.get("test_type", [])
                urgency = parameters.get("urgency", "routine")
                clinical_indication = parameters.get("clinical_indication", "")
                result = tool.order_test(test_type, urgency, clinical_indication)
                self.state["pending_lab_orders"].append(result["order_id"])

            elif tool_name == "lab_result_query":
                order_id = parameters.get("order_id", "")
                result = tool.get_result(order_id)
                if order_id in self.state["pending_lab_orders"]:
                    self.state["pending_lab_orders"].remove(order_id)
                    self.state["completed_lab_orders"].append(order_id)

            elif tool_name == "prescription_order":
                medication = parameters.get("medication", "")
                dose = parameters.get("dose", "")
                frequency = parameters.get("frequency", "")
                duration = parameters.get("duration", "")
                result = tool.prescribe(medication, dose, frequency, duration)
                self.state["prescriptions"].append(result["prescription_id"])

            else:
                return ToolCallResult(
                    success=False,
                    tool_name=tool_name,
                    result=None,
                    error=f"Tool '{tool_name}' not implemented"
                )

            # 记录工具调用
            self.state["tool_calls"].append({
                "step": self.state["step"],
                "tool": tool_name,
                "parameters": parameters,
                "result": result
            })

            return ToolCallResult(
                success=True,
                tool_name=tool_name,
                result=result
            )

        except Exception as e:
            return ToolCallResult(
                success=False,
                tool_name=tool_name,
                result=None,
                error=str(e)
            )

    def _execute_dialogue(self, action: Dict[str, Any]) -> ToolCallResult:
        """执行对话动作"""
        content = action.get("content", "")

        # 记录对话
        message = DialogueMessage(role="agent", content=content)
        self.state["dialogue_history"].append(message)

        # 生成患者响应（简化版）
        patient_response = self._generate_patient_response(content)

        response_message = DialogueMessage(role="patient", content=patient_response)
        self.state["dialogue_history"].append(response_message)

        return ToolCallResult(
            success=True,
            tool_name="dialogue",
            result={"patient_response": patient_response}
        )

    def _generate_patient_response(self, agent_message: str) -> str:
        """
        生成患者响应

        简化版：根据合作程度生成不同类型的响应
        """
        cooperation = self.patient_info.get("cooperation_level", "good")

        # 简化版响应逻辑
        if cooperation == "good":
            return "好的，我明白了。还有什么需要了解的吗？"
        elif cooperation == "partial":
            return "嗯...有时候是这样，有时候不是。"
        else:  # poor
            return "我不太确定，我记不清了。"

    def get_observation(self) -> Dict[str, Any]:
        """获取当前观察"""
        return {
            "step": self.state["step"],
            "dialogue_history": [
                {"role": msg.role, "content": msg.content}
                for msg in self.state["dialogue_history"]
            ],
            "pending_lab_orders": self.state["pending_lab_orders"],
            "completed_lab_orders": self.state["completed_lab_orders"],
            "prescriptions": self.state["prescriptions"],
            "emr_queried": self.state["emr_queried"],
            "medication_queried": self.state["medication_queried"]
        }


# ========================================
# Step 4: Agent 评估器
# ========================================

@dataclass
class EvaluationResult:
    """评估结果"""
    overall_score: float
    grading: str  # "A", "B", "C", "D", "F"

    timing_score: float
    timing_penalties: List[str]

    quality_score: float
    quality_errors: List[Dict[str, Any]]

    decision_score: float
    decision_issues: List[str]

    red_line_violations: List[str]

    improvement_suggestions: List[Dict[str, str]]


class ToolTimingEvaluator:
    """工具调用时机评估器"""

    def __init__(self):
        """初始化评估器"""
        self.required_tools = {
            "emr_query": {
                "must_call_before": 3,  # 必须在前3步调用
                "penalty": 2.0
            },
            "medication_query": {
                "must_call_before": "prescription_order",
                "penalty": 1.5
            },
            "lab_result_query": {
                "must_call_after": "lab_order",
                "penalty": 1.0
            }
        }

    def evaluate(self, agent_trace: List[Dict], task_requirements: Dict) -> Tuple[float, List[str]]:
        """
        评估工具调用时机

        Args:
            agent_trace: Agent行为轨迹
            task_requirements: 任务要求

        Returns:
            (分数, 扣分项列表)
        """
        score = 5.0
        penalties = []

        required_tools = task_requirements.get("required_tools", [])
        tool_calls = [step for step in agent_trace if step.get("action") == "tool_call"]

        # 检查必需工具是否调用
        for tool in required_tools:
            tool_call_steps = [i for i, step in enumerate(tool_calls) if step.get("tool") == tool]

            if not tool_call_steps:
                # 工具未调用
                penalty = self.required_tools.get(tool, {}).get("penalty", 1.0)
                score -= penalty
                penalties.append(f"未调用必需工具: {tool}")
            else:
                first_call_position = tool_call_steps[0]

                # 检查 emr_query 是否在早期调用
                if tool == "emr_query" and first_call_position > 2:
                    score -= 1.0
                    penalties.append(f"emr_query 调用过晚（第{first_call_position + 1}步）")

        # 检查调用顺序
        tool_sequence = [step.get("tool") for step in tool_calls]
        if "lab_order" in tool_sequence and "lab_result_query" in tool_sequence:
            lab_order_pos = tool_sequence.index("lab_order")
            lab_result_pos = tool_sequence.index("lab_result_query")

            if lab_result_pos <= lab_order_pos:
                score -= 1.0
                penalties.append("lab_result_query 应该在 lab_order 之后调用")

        if "medication_query" in tool_sequence and "prescription_order" in tool_sequence:
            med_query_pos = tool_sequence.index("medication_query")
            rx_pos = tool_sequence.index("prescription_order")

            if rx_pos <= med_query_pos:
                score -= 1.0
                penalties.append("medication_query 应该在 prescription_order 之前调用")

        return max(0.0, score), penalties


class ToolQualityEvaluator:
    """工具使用质量评估器"""

    def evaluate(self, agent_trace: List[Dict], task_requirements: Dict) -> Tuple[float, List[Dict]]:
        """
        评估工具使用质量

        Args:
            agent_trace: Agent行为轨迹
            task_requirements: 任务要求

        Returns:
            (分数, 错误列表)
        """
        score = 5.0
        errors = []

        tool_calls = [step for step in agent_trace if step.get("action") == "tool_call"]

        # 检查每个工具调用的参数质量
        for step in tool_calls:
            tool = step.get("tool")
            parameters = step.get("parameters", {})

            if tool == "emr_query":
                query_type = parameters.get("query_type", [])
                if not query_type:
                    score -= 0.5
                    errors.append({
                        "tool": tool,
                        "issue": "query_type 参数为空",
                        "severity": "low"
                    })

            elif tool == "prescription_order":
                dose = parameters.get("dose")
                frequency = parameters.get("frequency")
                duration = parameters.get("duration")

                if not dose:
                    score -= 0.5
                    errors.append({
                        "tool": tool,
                        "issue": "缺少 dose 参数",
                        "severity": "medium"
                    })
                if not frequency:
                    score -= 0.5
                    errors.append({
                        "tool": tool,
                        "issue": "缺少 frequency 参数",
                        "severity": "medium"
                    })
                if not duration:
                    score -= 0.3
                    errors.append({
                        "tool": tool,
                        "issue": "缺少 duration 参数",
                        "severity": "low"
                    })

        # 检查是否使用了工具返回的结果
        for i, step in enumerate(agent_trace):
            if step.get("action") == "tool_call":
                tool = step.get("tool")
                # 检查后续步骤是否使用了这个工具的结果
                next_steps = agent_trace[i+1:i+3]
                used = any(
                    "based_on" in s and tool in str(s.get("based_on", ""))
                    for s in next_steps
                )

                if not used and tool in ["emr_query", "lab_result_query"]:
                    score -= 0.5
                    errors.append({
                        "tool": tool,
                        "issue": "工具返回结果未被使用",
                        "severity": "medium"
                    })

        return max(0.0, score), errors


class DecisionFlowEvaluator:
    """决策流程质量评估器"""

    def evaluate(self, agent_trace: List[Dict], task_requirements: Dict) -> Tuple[float, List[str]]:
        """
        评估决策流程质量

        Args:
            agent_trace: Agent行为轨迹
            task_requirements: 任务要求

        Returns:
            (分数, 问题列表)
        """
        score = 5.0
        issues = []

        # 检查是否基于所有可用信息做决策
        tool_calls = [s for s in agent_trace if s.get("action") == "tool_call"]
        tools_used = [s.get("tool") for s in tool_calls]

        required_tools = task_requirements.get("required_tools", [])
        missing_tools = [t for t in required_tools if t not in tools_used]

        if missing_tools:
            score -= 2.0
            issues.append(f"决策缺少关键信息：未使用工具 {missing_tools}")

        # 检查决策逻辑
        for i, step in enumerate(agent_trace):
            if step.get("action") == "decision_update":
                # 检查是否有"基于"信息
                if "based_on" not in step:
                    score -= 0.5
                    issues.append("决策调整未说明依据")

        # 检查是否有红线违规
        red_line_conditions = task_requirements.get("red_line_conditions", [])
        for condition in red_line_conditions:
            # 简化版：假设没有违规
            pass

        return max(0.0, score), issues


class AgentEvaluator:
    """Agent评估器（集成三个评估维度）"""

    def __init__(self):
        """初始化评估器"""
        self.timing_evaluator = ToolTimingEvaluator()
        self.quality_evaluator = ToolQualityEvaluator()
        self.decision_evaluator = DecisionFlowEvaluator()

    def evaluate(self, agent_trace: List[Dict], task_config: Dict) -> EvaluationResult:
        """
        综合评估Agent表现

        Args:
            agent_trace: Agent行为轨迹
            task_config: 任务配置

        Returns:
            评估结果
        """
        # 获取评估标准
        evaluation_criteria = task_config.get("tool_evaluation_criteria", {})

        # 评估三个维度
        timing_score, timing_penalties = self.timing_evaluator.evaluate(
            agent_trace, evaluation_criteria
        )

        quality_score, quality_errors = self.quality_evaluator.evaluate(
            agent_trace, evaluation_criteria
        )

        decision_score, decision_issues = self.decision_evaluator.evaluate(
            agent_trace, evaluation_criteria
        )

        # 获取评分权重
        weights = evaluation_criteria.get("scoring_weights", {
            "tool_timing": 0.3,
            "tool_quality": 0.3,
            "decision_flow": 0.4
        })

        # 计算总分
        overall_score = (
            timing_score * weights["tool_timing"] +
            quality_score * weights["tool_quality"] +
            decision_score * weights["decision_flow"]
        )

        # 评级
        grading = self._calculate_grading(overall_score)

        # 检查红线违规
        red_line_violations = self._check_red_lines(agent_trace, evaluation_criteria)

        if red_line_violations:
            overall_score = 0.0
            grading = "F"

        # 生成改进建议
        improvement_suggestions = self._generate_suggestions(
            timing_penalties, quality_errors, decision_issues
        )

        return EvaluationResult(
            overall_score=round(overall_score, 2),
            grading=grading,
            timing_score=round(timing_score, 2),
            timing_penalties=timing_penalties,
            quality_score=round(quality_score, 2),
            quality_errors=quality_errors,
            decision_score=round(decision_score, 2),
            decision_issues=decision_issues,
            red_line_violations=red_line_violations,
            improvement_suggestions=improvement_suggestions
        )

    def _calculate_grading(self, score: float) -> str:
        """计算评级"""
        if score >= 4.5:
            return "A"
        elif score >= 4.0:
            return "B"
        elif score >= 3.0:
            return "C"
        elif score >= 2.0:
            return "D"
        else:
            return "F"

    def _check_red_lines(self, agent_trace: List[Dict], criteria: Dict) -> List[str]:
        """检查红线违规"""
        violations = []

        # 检查是否做了确定性诊断
        for step in agent_trace:
            if step.get("action") == "definitive_diagnosis":
                violations.append("确定性诊断 - 超出全科初诊Agent能力边界")
                break

        # 检查是否开了处方药（在没有查询药物信息的情况下）
        tool_calls = [s for s in agent_trace if s.get("action") == "tool_call"]
        medication_queried = any(s.get("tool") == "medication_query" for s in tool_calls)
        prescribed = any(s.get("tool") == "prescription_order" for s in tool_calls)

        if prescribed and not medication_queried:
            violations.append("开处方前未查询药物信息 - 存在安全风险")

        return violations

    def _generate_suggestions(self, timing_penalties: List[str],
                             quality_errors: List[Dict],
                             decision_issues: List[str]) -> List[Dict[str, str]]:
        """生成改进建议"""
        suggestions = []

        if timing_penalties:
            suggestions.append({
                "type": "tool_timing",
                "suggestion": "改善工具调用时机，确保在正确阶段调用必需工具"
            })

        if quality_errors:
            suggestions.append({
                "type": "tool_quality",
                "suggestion": "完善工具参数，确保必填参数都有值"
            })

        if decision_issues:
            suggestions.append({
                "type": "decision_flow",
                "suggestion": "基于所有可用信息做出决策，明确说明决策依据"
            })

        return suggestions


# ========================================
# 使用示例
# ========================================

def demo_usage():
    """演示如何使用测试环境"""
    print("="*60)
    print(" 医疗Agent测试环境使用示例")
    print("="*60)

    # 1. 加载任务配置
    task_config = {
        "id": "demo_task",
        "ticket": "我头晕三天了",
        "difficulty": "L2",
        "environment": {
            "available_tools": {
                "emr_query": {...},
                "medication_query": {...},
                "lab_order": {...},
                "lab_result_query": {...},
                "prescription_order": {...}
            },
            "scenario_type": "SYMPTOM_ANALYSIS"
        },
        "expected_agent_workflow": [...],
        "tool_evaluation_criteria": {...}
    }

    # 2. 创建环境
    env = ClinicalEnvironment(task_config)

    # 3. Agent与环境交互
    agent_trace = []

    # Step 1: 查询EMR
    action = {
        "type": "tool_call",
        "tool": "emr_query",
        "parameters": {
            "patient_id": "P001",
            "query_type": ["past_medical_history", "current_medications"]
        }
    }
    result = env.step(action)
    agent_trace.append({
        "step": 1,
        "action": "tool_call",
        "tool": "emr_query",
        "parameters": action["parameters"]
    })
    print(f"\nStep 1: 调用 emr_query")
    print(f"  Result: {result.result}")

    # Step 2: 对话
    action = {
        "type": "dialogue",
        "content": "我看到您有高血压，最近在吃药吗？"
    }
    result = env.step(action)
    agent_trace.append({
        "step": 2,
        "action": "dialogue",
        "content": action["content"],
        "based_on": "emr_query_result"
    })
    print(f"\nStep 2: 对话")
    print(f"  Patient: {result.result['patient_response']}")

    # Step 3: 开检查
    action = {
        "type": "tool_call",
        "tool": "lab_order",
        "parameters": {
            "test_type": ["心电图"],
            "urgency": "routine",
            "clinical_indication": "头晕待查"
        }
    }
    result = env.step(action)
    agent_trace.append({
        "step": 3,
        "action": "tool_call",
        "tool": "lab_order",
        "parameters": action["parameters"]
    })
    print(f"\nStep 3: 调用 lab_order")
    print(f"  Order ID: {result.result['order_id']}")

    # 4. 评估Agent表现
    evaluator = AgentEvaluator()
    eval_result = evaluator.evaluate(agent_trace, task_config)

    print(f"\n{'='*60}")
    print(" 评估结果")
    print(f"{'='*60}")
    print(f"总分: {eval_result.overall_score}/5.0")
    print(f"评级: {eval_result.grading}")
    print(f"\n工具调用时机: {eval_result.timing_score}/5.0")
    print(f"工具使用质量: {eval_result.quality_score}/5.0")
    print(f"决策流程质量: {eval_result.decision_score}/5.0")

    if eval_result.timing_penalties:
        print(f"\n时机扣分:")
        for penalty in eval_result.timing_penalties:
            print(f"  - {penalty}")

    if eval_result.improvement_suggestions:
        print(f"\n改进建议:")
        for suggestion in eval_result.improvement_suggestions:
            print(f"  - [{suggestion['type']}] {suggestion['suggestion']}")


if __name__ == "__main__":
    import sys
    import io

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 运行示例
    demo_usage()
