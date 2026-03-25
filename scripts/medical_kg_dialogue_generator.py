#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗知识图谱对话生成系统

基于 PrimeKG 构建，使用 Random Walk + Task Generator 生成多轮医患对话

算法架构：
1. Knowledge Graph Builder - 从 PrimeKG 构建医疗知识图谱
2. Random Walk - 在知识图谱上游走，生成问诊路径
3. Task Generator - 根据路径生成多轮对话任务

作者：Claude Sonnet 4.5
日期：2025-03-21
"""

import json
import random
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
import requests


# ========================================
# 1. Knowledge Graph Builder
# ========================================

class MedicalKnowledgeGraph:
    """医疗知识图谱"""

    def __init__(self, primekg_url: Optional[str] = None):
        """
        初始化医疗知识图谱

        Args:
            primekg_url: PrimeKG 数据URL（如果为None，使用内置数据）
        """
        self.graph = nx.DiGraph()
        self.node_types = defaultdict(set)
        self.edge_types = defaultdict(set)

        # 如果没有提供PrimeKG URL，使用内置的简化医疗知识图谱
        if primekg_url is None:
            self._build_builtin_medical_kg()
        else:
            self._load_from_primekg(primekg_url)

    def _build_builtin_medical_kg(self):
        """构建内置的医疗知识图谱（简化版PrimeKG）"""
        print("[KG] 构建医疗知识图谱...")

        # ===== 节点定义 =====

        # 症状节点
        symptoms = [
            "头晕", "头痛", "胸痛", "腹痛", "发热",
            "咳嗽", "呼吸困难", "恶心呕吐", "腹泻", "便秘",
            "心悸", "水肿", "乏力", "消瘦", "肥胖",
            "失眠", "焦虑", "抑郁", "意识障碍", "抽搐"
        ]

        for symptom in symptoms:
            self.graph.add_node(symptom, type="symptom")
            self.node_types["symptom"].add(symptom)

        # 疾病节点（按系统分类）
        diseases = {
            "心血管系统": [
                ("高血压", "stage_1", 0.7),
                ("冠心病", "stable", 0.6),
                ("心律失常", "atrial_fibrillation", 0.5),
                ("心力衰竭", "nyha_2", 0.4),
                ("心肌梗死", "st_elevation", 0.3)
            ],
            "呼吸系统": [
                ("上呼吸道感染", "viral", 0.8),
                ("肺炎", "bacterial", 0.6),
                ("支气管哮喘", "moderate", 0.5),
                ("COPD", "moderate", 0.4),
                ("肺栓塞", "acute", 0.3)
            ],
            "消化系统": [
                ("急性胃炎", "erosive", 0.7),
                ("消化性溃疡", "gastric", 0.6),
                ("急性胆囊炎", "calculous", 0.5),
                ("急性胰腺炎", "mild", 0.4),
                ("肠梗阻", "partial", 0.3)
            ],
            "内分泌代谢": [
                ("2型糖尿病", "uncontrolled", 0.6),
                ("甲状腺功能亢进", "grave", 0.5),
                ("甲状腺功能减退", "primary", 0.5),
                ("痛风", "acute", 0.4),
                ("肥胖症", "class_1", 0.7)
            ],
            "神经系统": [
                ("偏头痛", "with_aura", 0.6),
                ("紧张性头痛", "chronic", 0.7),
                ("脑梗死", "acute", 0.3),
                ("癫痫", "generalized", 0.4),
                ("良性阵发性位置性眩晕", "posterior", 0.6)
            ],
            "血液系统": [
                ("缺铁性贫血", "moderate", 0.6),
                ("巨幼细胞贫血", "b12_deficiency", 0.5),
                ("再生障碍性贫血", "moderate", 0.3),
                ("白血病", "acute", 0.2)
            ],
            "泌尿系统": [
                ("尿路感染", "uncomplicated", 0.7),
                ("肾结石", "ureteral", 0.5),
                ("慢性肾病", "stage_3", 0.4),
                ("前列腺增生", "moderate", 0.6)
            ],
            "精神心理": [
                ("焦虑症", "generalized", 0.6),
                ("抑郁症", "moderate", 0.5),
                ("失眠症", "primary", 0.7),
                ("躯体化障碍", "mild", 0.4)
            ]
        }

        for system, disease_list in diseases.items():
            for disease_name, severity, prevalence in disease_list:
                self.graph.add_node(
                    disease_name,
                    type="disease",
                    system=system,
                    severity=severity,
                    prevalence=prevalence
                )
                self.node_types["disease"].add(disease_name)

        # 检查节点
        lab_tests = [
            "血常规", "尿常规", "生化全项",
            "心电图", "胸部X光", "胸部CT",
            "腹部B超", "腹部CT", "头颅CT",
            "颈动脉彩超", "心脏彩超", "肝胆胰脾彩超"
        ]

        for test in lab_tests:
            self.graph.add_node(test, type="lab_test")
            self.node_types["lab_test"].add(test)

        # 治疗节点
        treatments = [
            # 心血管药物
            ("氨氯地平", "medication", "钙通道阻滞剂"),
            ("缬沙坦", "medication", "ARB"),
            ("美托洛尔", "medication", "β受体阻滞剂"),
            ("阿司匹林", "medication", "抗血小板"),
            ("阿托伐他汀", "medication", "他汀类"),
            # 呼吸药物
            ("阿莫西林", "medication", "抗生素"),
            ("头孢呋辛", "medication", "抗生素"),
            ("沙丁胺醇", "medication", "支气管扩张剂"),
            ("布地奈德", "medication", "吸入糖皮质激素"),
            # 消化药物
            ("奥美拉唑", "medication", "PPI"),
            ("多潘立酮", "medication", "促胃动力"),
            ("蒙脱石散", "medication", "止泻"),
            # 内分泌药物
            ("二甲双胍", "medication", "双胍类"),
            ("格列吡嗪", "medication", "磺脲类"),
            ("左甲状腺素", "medication", "甲状腺激素"),
            ("别嘌醇", "medication", "抑制尿酸生成"),
            # 神经药物
            ("氟桂利嗪", "medication", "钙拮抗剂"),
            ("佐米曲普坦", "medication", "曲普坦类"),
            ("卡马西平", "medication", "抗癫痫"),
            # 其他
            ("琥珀酸亚铁", "medication", "补铁"),
            ("舍曲林", "medication", "SSRI"),
            ("艾司唑仑", "medication", "苯二氮卓类")
        ]

        for treatment, category, subcategory in treatments:
            self.graph.add_node(
                treatment,
                type="treatment",
                category=category,
                subcategory=subcategory
            )
            self.node_types["treatment"].add(treatment)

        # ===== 边定义 =====

        # 症状 → 疾病 (has_symptom 关系的反向)
        symptom_disease_edges = [
            ("头晕", "高血压", 0.6),
            ("头晕", "贫血", 0.5),
            ("头晕", "良性阵发性位置性眩晕", 0.7),
            ("头晕", "焦虑症", 0.4),
            ("头晕", "2型糖尿病", 0.3),
            ("头痛", "偏头痛", 0.7),
            ("头痛", "紧张性头痛", 0.6),
            ("头痛", "高血压", 0.4),
            ("头痛", "脑梗死", 0.5),
            ("胸痛", "冠心病", 0.7),
            ("胸痛", "心肌梗死", 0.6),
            ("胸痛", "肺炎", 0.4),
            ("胸痛", "焦虑症", 0.3),
            ("腹痛", "急性胃炎", 0.6),
            ("腹痛", "消化性溃疡", 0.7),
            ("腹痛", "急性胆囊炎", 0.8),
            ("腹痛", "急性胰腺炎", 0.7),
            ("腹痛", "肠梗阻", 0.6),
            ("发热", "上呼吸道感染", 0.8),
            ("发热", "肺炎", 0.7),
            ("发热", "尿路感染", 0.6),
            ("咳嗽", "上呼吸道感染", 0.8),
            ("咳嗽", "肺炎", 0.7),
            ("咳嗽", "支气管哮喘", 0.6),
            ("咳嗽", "COPD", 0.7),
            ("呼吸困难", "肺炎", 0.7),
            ("呼吸困难", "COPD", 0.8),
            ("呼吸困难", "肺栓塞", 0.6),
            ("呼吸困难", "心力衰竭", 0.7),
            ("恶心呕吐", "急性胃炎", 0.7),
            ("恶心呕吐", "消化性溃疡", 0.6),
            ("恶心呕吐", "急性胆囊炎", 0.8),
            ("腹泻", "急性胃炎", 0.6),
            ("腹泻", "肠梗阻", 0.5),
            ("心悸", "心律失常", 0.7),
            ("心悸", "焦虑症", 0.6),
            ("心悸", "甲状腺功能亢进", 0.5),
            ("水肿", "心力衰竭", 0.7),
            ("水肿", "慢性肾病", 0.6),
            ("乏力", "缺铁性贫血", 0.7),
            ("乏力", "2型糖尿病", 0.5),
            ("乏力", "甲状腺功能减退", 0.6),
            ("消瘦", "2型糖尿病", 0.6),
            ("消瘦", "甲状腺功能亢进", 0.7),
            ("消瘦", "恶性肿瘤", 0.5),
            ("失眠", "焦虑症", 0.6),
            ("失眠", "抑郁症", 0.5),
            ("焦虑", "焦虑症", 0.8),
            ("焦虑", "甲状腺功能亢进", 0.5),
            ("抑郁", "抑郁症", 0.8),
            ("意识障碍", "脑梗死", 0.7),
            ("意识障碍", "低血糖", 0.6),
            ("抽搐", "癫痫", 0.8)
        ]

        for symptom, disease, weight in symptom_disease_edges:
            if disease in [d[0] for diseases_list in diseases.values() for d in diseases_list]:
                self.graph.add_edge(symptom, disease, relation="suggests", weight=weight)
                self.edge_types["suggests"].add((symptom, disease))

        # 疾病 → 检查 (requires_test)
        disease_test_edges = [
            ("高血压", "心电图", 0.9),
            ("高血压", "心脏彩超", 0.7),
            ("高血压", "生化全项", 0.8),
            ("冠心病", "心电图", 0.9),
            ("冠心病", "胸部CT", 0.7),
            ("冠心病", "心脏彩超", 0.8),
            ("心律失常", "心电图", 0.9),
            ("肺炎", "胸部X光", 0.9),
            ("肺炎", "血常规", 0.8),
            ("肺炎", "胸部CT", 0.7),
            ("支气管哮喘", "胸部X光", 0.7),
            ("支气管哮喘", "血常规", 0.6),
            ("COPD", "胸部CT", 0.8),
            ("COPD", "肺功能", 0.9),
            ("消化性溃疡", "胃镜", 0.9),
            ("消化性溃疡", "幽门螺杆菌检测", 0.8),
            ("急性胆囊炎", "腹部B超", 0.9),
            ("急性胆囊炎", "血常规", 0.7),
            ("急性胰腺炎", "腹部CT", 0.9),
            ("急性胰腺炎", "血淀粉酶", 0.9),
            ("2型糖尿病", "生化全项", 0.9),
            ("2型糖尿病", "糖化血红蛋白", 0.9),
            ("甲状腺功能亢进", "甲状腺功能", 0.9),
            ("偏头痛", "头颅CT", 0.6),
            ("脑梗死", "头颅CT", 0.9),
            ("脑梗死", "MRI", 0.8),
            ("缺铁性贫血", "血常规", 0.9),
            ("缺铁性贫血", "铁代谢", 0.8),
            ("尿路感染", "尿常规", 0.9),
            ("尿路感染", "血常规", 0.7)
        ]

        for disease, test, weight in disease_test_edges:
            if test in self.node_types["lab_test"]:
                self.graph.add_edge(disease, test, relation="requires_test", weight=weight)
                self.edge_types["requires_test"].add((disease, test))

        # 疾病 → 治疗 (treated_with)
        disease_treatment_edges = [
            ("高血压", "氨氯地平", 0.9),
            ("高血压", "缬沙坦", 0.8),
            ("高血压", "美托洛尔", 0.7),
            ("冠心病", "阿司匹林", 0.9),
            ("冠心病", "阿托伐他汀", 0.8),
            ("心律失常", "美托洛尔", 0.8),
            ("心力衰竭", "美托洛尔", 0.9),
            ("上呼吸道感染", "阿莫西林", 0.7),
            ("肺炎", "头孢呋辛", 0.8),
            ("支气管哮喘", "沙丁胺醇", 0.8),
            ("支气管哮喘", "布地奈德", 0.8),
            ("COPD", "沙丁胺醇", 0.7),
            ("COPD", "布地奈德", 0.7),
            ("消化性溃疡", "奥美拉唑", 0.9),
            ("急性胃炎", "奥美拉唑", 0.8),
            ("2型糖尿病", "二甲双胍", 0.9),
            ("2型糖尿病", "格列吡嗪", 0.7),
            ("甲状腺功能减退", "左甲状腺素", 0.9),
            ("甲状腺功能亢进", "抗甲状腺药物", 0.9),
            ("痛风", "别嘌醇", 0.8),
            ("偏头痛", "氟桂利嗪", 0.7),
            ("偏头痛", "佐米曲普坦", 0.8),
            ("癫痫", "卡马西平", 0.8),
            ("缺铁性贫血", "琥珀酸亚铁", 0.9),
            ("焦虑症", "舍曲林", 0.7),
            ("抑郁症", "舍曲林", 0.8),
            ("失眠症", "艾司唑仑", 0.7)
        ]

        for disease, treatment, weight in disease_treatment_edges:
            if treatment in self.node_types["treatment"]:
                self.graph.add_edge(disease, treatment, relation="treated_with", weight=weight)
                self.edge_types["treated_with"].add((disease, treatment))

        # 统计信息
        print(f"[KG] 知识图谱构建完成")
        print(f"  - 节点总数: {self.graph.number_of_nodes()}")
        print(f"  - 边总数: {self.graph.number_of_edges()}")
        print(f"  - 症状节点: {len(self.node_types['symptom'])}")
        print(f"  - 疾病节点: {len(self.node_types['disease'])}")
        print(f"  - 检查节点: {len(self.node_types['lab_test'])}")
        print(f"  - 治疗节点: {len(self.node_types['treatment'])}")

    def _load_from_primekg(self, url: str):
        """从PrimeKG加载知识图谱（TODO: 实现完整版本）"""
        print(f"[KG] 从PrimeKG加载: {url}")
        # TODO: 实现PrimeKG数据加载
        # PrimeKG数据格式：https://github.com/mims-harvard/PrimeKG
        # 需要下载并解析PrimeKG的CSV/TSV文件
        pass

    def get_neighbors(self, node: str, edge_type: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        获取节点的邻居

        Args:
            node: 节点名称
            edge_type: 边类型过滤（可选）

        Returns:
            [(邻居节点, 权重), ...]
        """
        if node not in self.graph:
            return []

        neighbors = []
        for neighbor in self.graph.neighbors(node):
            edge_data = self.graph.get_edge_data(node, neighbor)
            if edge_type is None or edge_data.get("relation") == edge_type:
                weight = edge_data.get("weight", 0.5)
                neighbors.append((neighbor, weight))

        return neighbors

    def get_nodes_by_type(self, node_type: str) -> List[str]:
        """获取指定类型的所有节点"""
        return list(self.node_types.get(node_type, set()))

    def get_node_info(self, node: str) -> Dict[str, Any]:
        """获取节点信息"""
        if node not in self.graph:
            return {}
        return self.graph.nodes[node]


# ========================================
# 2. Random Walk 路径生成器
# ========================================

@dataclass
class WalkPath:
    """随机游走路径"""
    nodes: List[str] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    total_score: float = 0.0

    def add_step(self, node: str, edge: Dict[str, Any], score: float):
        """添加一步"""
        self.nodes.append(node)
        self.edges.append(edge)
        self.scores.append(score)
        self.total_score += score

    def get_length(self) -> int:
        """获取路径长度"""
        return len(self.nodes)


class RandomWalkGenerator:
    """Random Walk 路径生成器"""

    def __init__(self, knowledge_graph: MedicalKnowledgeGraph):
        """
        初始化Random Walk生成器

        Args:
            knowledge_graph: 医疗知识图谱
        """
        self.kg = knowledge_graph
        self.walk_configs = {
            "short": {"max_steps": 5, "exploration_prob": 0.2},
            "medium": {"max_steps": 8, "exploration_prob": 0.3},
            "long": {"max_steps": 12, "exploration_prob": 0.4}
        }

    def generate_walk(
        self,
        start_symptom: str,
        walk_type: str = "medium",
        seed: Optional[int] = None
    ) -> WalkPath:
        """
        生成Random Walk路径

        Args:
            start_symptom: 起始症状
            walk_type: 路径类型（short/medium/long）
            seed: 随机种子（用于可复现）

        Returns:
            WalkPath对象
        """
        if seed is not None:
            random.seed(seed)

        config = self.walk_configs.get(walk_type, self.walk_configs["medium"])
        max_steps = config["max_steps"]
        exploration_prob = config["exploration_prob"]

        path = WalkPath()
        current_node = start_symptom
        path.add_step(current_node, {}, 1.0)

        visited_types = set(["symptom"])

        for step in range(max_steps):
            # 获取当前节点的类型
            current_type = self.kg.graph.nodes[current_node].get("type", "unknown")

            # 根据当前类型决定下一步的节点类型
            if current_type == "symptom":
                # 症状 → 疾病
                neighbors = self.kg.get_neighbors(current_node, edge_type="suggests")
                if not neighbors:
                    break

                # 加权随机选择疾病
                next_node, weight = self._weighted_random_choice(neighbors)

            elif current_type == "disease":
                # 疾病 → 检查 或 疾病 → 治疗
                test_neighbors = self.kg.get_neighbors(current_node, edge_type="requires_test")
                treatment_neighbors = self.kg.get_neighbors(current_node, edge_type="treated_with")

                # 决定走哪条路
                if test_neighbors and treatment_neighbors:
                    if random.random() < 0.6:  # 60%概率去做检查
                        neighbors = test_neighbors
                        next_type = "lab_test"
                    else:
                        neighbors = treatment_neighbors
                        next_type = "treatment"
                elif test_neighbors:
                    neighbors = test_neighbors
                    next_type = "lab_test"
                elif treatment_neighbors:
                    neighbors = treatment_neighbors
                    next_type = "treatment"
                else:
                    break

                next_node, weight = self._weighted_random_choice(neighbors)

            elif current_type == "lab_test":
                # 检查 → 结束
                break

            elif current_type == "treatment":
                # 治疗 → 结束
                break

            else:
                break

            # 添加到路径
            edge_info = {
                "from": current_node,
                "to": next_node,
                "relation": self.kg.graph.get_edge_data(current_node, next_node).get("relation", "unknown")
            }
            path.add_step(next_node, edge_info, weight)

            # 更新当前节点
            current_node = next_node

            # 探索性提前终止
            if random.random() < exploration_prob and len(path.nodes) >= 3:
                break

        return path

    def _weighted_random_choice(self, neighbors: List[Tuple[str, float]]) -> Tuple[str, float]:
        """
        加权随机选择

        Args:
            neighbors: [(节点, 权重), ...]

        Returns:
            (选择的节点, 权重)
        """
        nodes, weights = zip(*neighbors)
        total_weight = sum(weights)

        if total_weight == 0:
            return random.choice(neighbors)

        # 归一化权重
        normalized_weights = [w / total_weight for w in weights]

        # 加权随机选择
        chosen_index = random.choices(range(len(nodes)), weights=normalized_weights, k=1)[0]

        return nodes[chosen_index], weights[chosen_index]

    def generate_multiple_walks(
        self,
        start_symptom: str,
        num_walks: int = 10,
        walk_type: str = "medium"
    ) -> List[WalkPath]:
        """
        生成多条Random Walk路径

        Args:
            start_symptom: 起始症状
            num_walks: 路径数量
            walk_type: 路径类型

        Returns:
            WalkPath列表
        """
        paths = []
        for i in range(num_walks):
            path = self.generate_walk(start_symptom, walk_type=walk_type, seed=i)
            paths.append(path)

        return paths


# ========================================
# 3. Task Generator (多轮对话生成)
# ========================================

@dataclass
class DialogueTurn:
    """对话轮次"""
    turn_id: int
    role: str  # "patient" or "doctor"
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsultationTask:
    """问诊任务"""
    task_id: str
    symptom: str
    dialogue_turns: List[DialogueTurn]
    patient_profile: Dict[str, Any]
    expected_diagnosis: Optional[str] = None
    expected_tests: List[str] = field(default_factory=list)
    expected_treatments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskGenerator:
    """任务生成器 - 将路径转换为对话任务"""

    def __init__(self, knowledge_graph: MedicalKnowledgeGraph):
        """
        初始化任务生成器

        Args:
            knowledge_graph: 医疗知识图谱
        """
        self.kg = knowledge_graph

        # 对话模板
        self.dialogue_templates = {
            "symptom_to_disease": {
                "patient": [
                    "医生，我{symptom_desc}已经{duration}了",
                    "我主要的问题是{symptom}，{duration}开始",
                    "{duration}前我开始出现{symptom}"
                ],
                "doctor": [
                    "{symptom}持续多久了？",
                    "能详细描述一下{symptom}的情况吗？",
                    "除了{symptom}，还有其他不舒服吗？"
                ]
            },
            "disease_inquiry": {
                "patient": [
                    "这个{previous_symptom}和{disease}有关系吗？",
                    "那我这个情况严重吗？",
                    "是什么原因导致的呢？"
                ],
                "doctor": [
                    "根据您的{symptoms}，我怀疑可能是{disease}",
                    "我们需要做一些检查来确认是否是{disease}",
                    "{disease}的可能性比较大，但需要排除其他原因"
                ]
            },
            "test_order": {
                "patient": [
                    "需要做哪些检查？",
                    "这些检查痛不痛？",
                    "多久能出结果？"
                ],
                "doctor": [
                    "我建议您做个{test}",
                    "需要做{test_list}来明确诊断",
                    "先做个{test}，根据结果再决定下一步"
                ]
            },
            "test_result": {
                "patient": [
                    "结果怎么样？",
                    "有问题吗？",
                    "严重吗？"
                ],
                "doctor": [
                    "{test}结果显示{result}",
                    "从{test}来看，{interpretation}",
                    "检查提示{finding}"
                ]
            },
            "treatment": {
                "patient": [
                    "需要吃什么药？",
                    "这个病能治好吗？",
                    "平时需要注意什么？"
                ],
                "doctor": [
                    "建议使用{treatment}",
                    "可以用{treatment_list}来治疗",
                    "除了{treatment}，还需要注意{precautions}"
                ]
            }
        }

    def generate_task(self, path: WalkPath, task_id: str) -> ConsultationTask:
        """
        根据路径生成对话任务

        Args:
            path: Random Walk路径
            task_id: 任务ID

        Returns:
            ConsultationTask对象
        """
        dialogue_turns = []
        turn_id = 0

        # 提取路径信息
        symptom = path.nodes[0] if path.nodes else "不适"
        diseases = [n for n in path.nodes if self.kg.graph.nodes[n].get("type") == "disease"]
        tests = [n for n in path.nodes if self.kg.graph.nodes[n].get("type") == "lab_test"]
        treatments = [n for n in path.nodes if self.kg.graph.nodes[n].get("type") == "treatment"]

        # 生成患者档案
        patient_profile = self._generate_patient_profile(path)

        # 第1轮：患者主诉
        turn_id += 1
        dialogue_turns.append(DialogueTurn(
            turn_id=turn_id,
            role="patient",
            content=self._generate_patient_complaint(symptom),
            context={"phase": "chief_complaint"},
            metadata={"symptom": symptom}
        ))

        # 第2轮：医生问诊
        turn_id += 1
        dialogue_turns.append(DialogueTurn(
            turn_id=turn_id,
            role="doctor",
            content=self._generate_doctor_inquiry(symptom),
            context={"phase": "inquiry"},
            metadata={"target_symptom": symptom}
        ))

        # 第3轮：患者详细描述
        turn_id += 1
        dialogue_turns.append(DialogueTurn(
            turn_id=turn_id,
            role="patient",
            content=self._generate_patient_description(symptom, patient_profile),
            context={"phase": "description"},
            metadata=patient_profile
        ))

        # 如果有疾病假设
        if diseases:
            disease = diseases[0]

            # 第4轮：医生提出初步判断
            turn_id += 1
            dialogue_turns.append(DialogueTurn(
                turn_id=turn_id,
                role="doctor",
                content=self._generate_diagnosis_inquiry(symptom, disease),
                context={"phase": "diagnosis_inquiry"},
                metadata={"suspected_disease": disease}
            ))

            # 第5轮：患者响应
            turn_id += 1
            dialogue_turns.append(DialogueTurn(
                turn_id=turn_id,
                role="patient",
                content=self._generate_patient_response_to_diagnosis(disease),
                context={"phase": "confirmation"},
                metadata={}
            ))

        # 如果有检查
        if tests:
            test = tests[0]

            # 第6轮：医生开检查
            turn_id += 1
            dialogue_turns.append(DialogueTurn(
                turn_id=turn_id,
                role="doctor",
                content=self._generate_test_order(test, tests),
                context={"phase": "test_order"},
                metadata={"ordered_tests": tests}
            ))

            # 第7轮：患者同意
            turn_id += 1
            dialogue_turns.append(DialogueTurn(
                turn_id=turn_id,
                role="patient",
                content=self._generate_patient_agreement_to_test(test),
                context={"phase": "test_agreement"},
                metadata={}
            ))

        # 如果有治疗
        if treatments:
            treatment = treatments[0]

            # 第8轮：医生建议治疗
            turn_id += 1
            dialogue_turns.append(DialogueTurn(
                turn_id=turn_id,
                role="doctor",
                content=self._generate_treatment_recommendation(treatment, treatments),
                context={"phase": "treatment"},
                metadata={"recommended_treatments": treatments}
            ))

            # 第9轮：患者询问
            turn_id += 1
            dialogue_turns.append(DialogueTurn(
                turn_id=turn_id,
                role="patient",
                content=self._generate_patient_treatment_inquiry(treatment),
                context={"phase": "treatment_inquiry"},
                metadata={}
            ))

        # 构建任务
        return ConsultationTask(
            task_id=task_id,
            symptom=symptom,
            dialogue_turns=dialogue_turns,
            patient_profile=patient_profile,
            expected_diagnosis=diseases[0] if diseases else None,
            expected_tests=tests,
            expected_treatments=treatments,
            metadata={
                "path_length": path.get_length(),
                "path_score": path.total_score,
                "path_nodes": path.nodes
            }
        )

    def _generate_patient_profile(self, path: WalkPath) -> Dict[str, Any]:
        """生成患者档案"""
        symptom = path.nodes[0] if path.nodes else "不适"

        # 基于症状生成相关档案
        profiles = {
            "头晕": {"age": 55, "gender": "female", "duration": "3天", "severity": "moderate"},
            "头痛": {"age": 42, "gender": "male", "duration": "1周", "severity": "mild"},
            "胸痛": {"age": 65, "gender": "male", "duration": "2小时", "severity": "severe"},
            "腹痛": {"age": 38, "gender": "female", "duration": "1天", "severity": "moderate"},
            "发热": {"age": 28, "gender": "female", "duration": "3天", "severity": "moderate"},
            "咳嗽": {"age": 45, "gender": "male", "duration": "5天", "severity": "mild"},
        }

        profile = profiles.get(symptom, {
            "age": random.randint(30, 70),
            "gender": random.choice(["male", "female"]),
            "duration": f"{random.randint(1, 7)}天",
            "severity": random.choice(["mild", "moderate", "severe"])
        })

        return profile

    def _generate_patient_complaint(self, symptom: str) -> str:
        """生成患者主诉"""
        templates = [
            f"医生，我{symptom}",
            f"我主要是{symptom}，已经好几天了",
            f"我{symptom}，很难受",
        ]
        return random.choice(templates)

    def _generate_doctor_inquiry(self, symptom: str) -> str:
        """生成医生问询"""
        templates = [
            f"{symptom}持续多久了？",
            f"能详细描述一下{symptom}的情况吗？",
            f"{symptom}在什么情况下会加重或缓解？",
            f"除了{symptom}，还有其他不舒服吗？"
        ]
        return random.choice(templates)

    def _generate_patient_description(self, symptom: str, profile: Dict[str, Any]) -> str:
        """生成患者详细描述"""
        duration = profile.get("duration", "几天")
        severity = profile.get("severity", "moderate")

        severity_desc = {
            "mild": "还能忍受",
            "moderate": "有点难受",
            "severe": "非常难受"
        }

        templates = [
            f"已经{duration}了，{severity_desc.get(severity, '')}",
            f"从{duration}前开始的，{severity_desc.get(severity, '')}",
            f"{duration}了，越来越{severity_desc.get(severity, '')}"
        ]
        return random.choice(templates)

    def _generate_diagnosis_inquiry(self, symptom: str, disease: str) -> str:
        """生成诊断问询"""
        templates = [
            f"根据您的{symptom}，我怀疑可能是{disease}",
            f"从症状来看，{disease}的可能性比较大",
            f"需要排除一下{disease}"
        ]
        return random.choice(templates)

    def _generate_patient_response_to_diagnosis(self, disease: str) -> str:
        """生成患者对诊断的响应"""
        templates = [
            f"{disease}严重吗？",
            f"那需要怎么治疗{disease}？",
            f"这是{disease}吗？我还以为是其他问题"
        ]
        return random.choice(templates)

    def _generate_test_order(self, test: str, tests: List[str]) -> str:
        """生成检查单"""
        if len(tests) == 1:
            return f"我建议您做个{test}"
        else:
            return f"我建议您做个{test}等检查"

    def _generate_patient_agreement_to_test(self, test: str) -> str:
        """生成患者对检查的同意"""
        templates = [
            "好的，需要做哪些准备？",
            "这个检查痛吗？",
            "多久能出结果？",
            "好的，我去做"
        ]
        return random.choice(templates)

    def _generate_treatment_recommendation(self, treatment: str, treatments: List[str]) -> str:
        """生成治疗建议"""
        if len(treatments) == 1:
            return f"针对您的情况，我建议使用{treatment}"
        else:
            return f"可以用{treatment}等药物来治疗"

    def _generate_patient_treatment_inquiry(self, treatment: str) -> str:
        """生成患者对治疗的询问"""
        templates = [
            f"这个{treatment}需要吃多久？",
            f"有什么副作用吗？",
            f"平时需要注意什么？"
        ]
        return random.choice(templates)

    def generate_batch_tasks(
        self,
        paths: List[WalkPath],
        task_id_prefix: str = "kg_task"
    ) -> List[ConsultationTask]:
        """
        批量生成任务

        Args:
            paths: WalkPath列表
            task_id_prefix: 任务ID前缀

        Returns:
            ConsultationTask列表
        """
        tasks = []
        for i, path in enumerate(paths):
            task_id = f"{task_id_prefix}_{i:04d}"
            task = self.generate_task(path, task_id)
            tasks.append(task)

        return tasks


# ========================================
# 4. 完整流程：KG → Random Walk → Task
# ========================================

class MedicalDialoguePipeline:
    """完整的医疗对话生成流程"""

    def __init__(self, primekg_url: Optional[str] = None):
        """
        初始化流程

        Args:
            primekg_url: PrimeKG数据URL（可选）
        """
        print("="*60)
        print(" 医疗知识图谱对话生成系统")
        print("="*60)

        # 1. 构建知识图谱
        self.kg = MedicalKnowledgeGraph(primekg_url)

        # 2. 初始化Random Walk生成器
        self.walk_generator = RandomWalkGenerator(self.kg)

        # 3. 初始化Task生成器
        self.task_generator = TaskGenerator(self.kg)

        print("\n[Pipeline] 初始化完成")

    def generate_dialogue_task(
        self,
        symptom: str,
        walk_type: str = "medium",
        seed: Optional[int] = None,
        task_id: Optional[str] = None
    ) -> ConsultationTask:
        """
        生成单个对话任务

        Args:
            symptom: 起始症状
            walk_type: Random Walk类型
            seed: 随机种子
            task_id: 任务ID

        Returns:
            ConsultationTask
        """
        print(f"\n[Pipeline] 生成对话任务")
        print(f"  症状: {symptom}")
        print(f"  Walk类型: {walk_type}")

        # Step 1: Random Walk
        path = self.walk_generator.generate_walk(symptom, walk_type=walk_type, seed=seed)
        print(f"  路径长度: {path.get_length()}")
        print(f"  路径节点: {' → '.join(path.nodes)}")

        # Step 2: 生成任务
        if task_id is None:
            task_id = f"kg_task_{symptom}_{seed or 0}"
        task = self.task_generator.generate_task(path, task_id)

        print(f"  对话轮次: {len(task.dialogue_turns)}")
        print(f"  预期诊断: {task.expected_diagnosis}")
        print(f"  预期检查: {task.expected_tests}")
        print(f"  预期治疗: {task.expected_treatments}")

        return task

    def generate_batch_tasks(
        self,
        symptoms: List[str],
        num_walks_per_symptom: int = 5,
        walk_type: str = "medium"
    ) -> List[ConsultationTask]:
        """
        批量生成对话任务

        Args:
            symptoms: 症状列表
            num_walks_per_symptom: 每个症状生成多少条路径
            walk_type: Random Walk类型

        Returns:
            ConsultationTask列表
        """
        print(f"\n[Pipeline] 批量生成任务")
        print(f"  症状数量: {len(symptoms)}")
        print(f"  每个症状路径数: {num_walks_per_symptom}")

        all_paths = []

        for symptom in symptoms:
            paths = self.walk_generator.generate_multiple_walks(
                symptom,
                num_walks=num_walks_per_symptom,
                walk_type=walk_type
            )
            all_paths.extend(paths)

        print(f"  总路径数: {len(all_paths)}")

        tasks = self.task_generator.generate_batch_tasks(all_paths)

        print(f"  生成任务数: {len(tasks)}")

        return tasks

    def export_to_tau2_format(
        self,
        tasks: List[ConsultationTask],
        output_file: str
    ):
        """
        导出为tau2格式

        Args:
            tasks: ConsultationTask列表
            output_file: 输出文件路径
        """
        print(f"\n[Pipeline] 导出为tau2格式")
        print(f"  输出文件: {output_file}")

        tau2_tasks = []
        for task in tasks:
            tau2_task = self._convert_to_tau2_format(task)
            tau2_tasks.append(tau2_task)

        # 保存
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tau2_tasks, f, ensure_ascii=False, indent=2)

        print(f"  ✓ 已保存 {len(tau2_tasks)} 个任务")

    def _convert_to_tau2_format(self, task: ConsultationTask) -> Dict[str, Any]:
        """转换为tau2格式"""
        # 构建对话文本
        dialogue_text = "\n".join([
            f"{'患者' if turn.role == 'patient' else '医生'}: {turn.content}"
            for turn in task.dialogue_turns
        ])

        tau2_task = {
            "id": task.task_id,
            "description": {
                "purpose": f"医患问诊 - {task.symptom}",
                "notes": f"基于知识图谱+Random Walk生成的动态对话"
            },
            "user_scenario": {
                "persona": f"{task.patient_profile.get('age', 'N/A')}-year-old {task.patient_profile.get('gender', 'N/A')} patient with {task.symptom}",
                "instructions": {
                    "domain": "internal_medicine",
                    "reason_for_call": task.symptom,
                    "dialogue": dialogue_text
                }
            },
            "ticket": task.dialogue_turns[0].content if task.dialogue_turns else task.symptom,
            "initial_state": {
                "initialization_actions": [
                    {
                        "env_type": "user",
                        "func_name": "set_user_info",
                        "arguments": {
                            "name": f"Patient_{task.task_id}",
                            "age": task.patient_profile.get("age"),
                            "gender": task.patient_profile.get("gender")
                        }
                    }
                ]
            },
            "metadata": {
                "source": "knowledge_graph_random_walk",
                "generation_method": "KG + Random Walk + Task Generator",
                "symptom": task.symptom,
                "expected_diagnosis": task.expected_diagnosis,
                "expected_tests": task.expected_tests,
                "expected_treatments": task.expected_treatments,
                "path_length": task.metadata.get("path_length"),
                "path_score": task.metadata.get("path_score")
            }
        }

        return tau2_task


# ========================================
# 5. 使用示例
# ========================================

def demo_single_task():
    """演示：生成单个对话任务"""
    print("\n" + "="*60)
    print(" 演示1：生成单个对话任务")
    print("="*60)

    # 创建流程
    pipeline = MedicalDialoguePipeline()

    # 生成任务
    task = pipeline.generate_dialogue_task(
        symptom="头晕",
        walk_type="medium",
        seed=42
    )

    # 打印对话
    print("\n" + "="*60)
    print(" 对话内容")
    print("="*60)
    for turn in task.dialogue_turns:
        role_name = "患者" if turn.role == "patient" else "医生"
        print(f"\n{role_name}: {turn.content}")

    return task


def demo_batch_tasks():
    """演示：批量生成对话任务"""
    print("\n" + "="*60)
    print(" 演示2：批量生成对话任务")
    print("="*60)

    # 创建流程
    pipeline = MedicalDialoguePipeline()

    # 批量生成
    tasks = pipeline.generate_batch_tasks(
        symptoms=["头晕", "头痛", "胸痛", "腹痛", "发热"],
        num_walks_per_symptom=3,
        walk_type="medium"
    )

    # 导出
    pipeline.export_to_tau2_format(
        tasks,
        "data/tau2/domains/clinical/kg_generated_tasks.json"
    )

    return tasks


def demo_statistics():
    """演示：统计分析"""
    print("\n" + "="*60)
    print(" 演示3：统计分析")
    print("="*60)

    # 创建流程
    pipeline = MedicalDialoguePipeline()

    # 生成大量任务
    tasks = pipeline.generate_batch_tasks(
        symptoms=pipeline.kg.get_nodes_by_type("symptom")[:10],  # 前10个症状
        num_walks_per_symptom=5,
        walk_type="medium"
    )

    # 统计
    print("\n" + "="*60)
    print(" 统计信息")
    print("="*60)

    # 症状分布
    symptom_dist = defaultdict(int)
    for task in tasks:
        symptom_dist[task.symptom] += 1

    print("\n症状分布:")
    for symptom, count in sorted(symptom_dist.items(), key=lambda x: -x[1]):
        print(f"  {symptom}: {count}")

    # 疾病分布
    disease_dist = defaultdict(int)
    for task in tasks:
        if task.expected_diagnosis:
            disease_dist[task.expected_diagnosis] += 1

    print("\n疾病分布 (Top 10):")
    for disease, count in sorted(disease_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"  {disease}: {count}")

    # 对话轮次分布
    turn_dist = defaultdict(int)
    for task in tasks:
        turn_dist[len(task.dialogue_turns)] += 1

    print("\n对话轮次分布:")
    for turns, count in sorted(turn_dist.items()):
        print(f"  {turns}轮: {count}")

    return tasks


if __name__ == "__main__":
    import sys
    import io

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 运行演示
    print("\n选择演示:")
    print("1. 生成单个对话任务")
    print("2. 批量生成对话任务")
    print("3. 统计分析")
    print("4. 全部运行")

    choice = input("\n请选择 (1-4): ").strip()

    if choice == "1":
        demo_single_task()
    elif choice == "2":
        demo_batch_tasks()
    elif choice == "3":
        demo_statistics()
    elif choice == "4":
        demo_single_task()
        demo_batch_tasks()
        demo_statistics()
    else:
        print("运行全部演示...")
        demo_single_task()
        demo_batch_tasks()
        demo_statistics()

    print("\n" + "="*60)
    print(" ✓ 演示完成")
    print("="*60)
