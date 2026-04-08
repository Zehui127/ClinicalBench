#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrimeKG Random Walk 集成

将真实的 PrimeKG 知识图谱与 Random Walk 算法集成，
用于生成医疗问诊对话路径。

算法架构：
1. PrimeKG Loader - 加载真实的 PrimeKG 数据
2. PrimeKG Adapter - 将 PrimeKG 数据适配为 Random Walk 格式
3. Random Walk Generator - 在 PrimeKG 上进行 Random Walk
4. Task Generator - 将路径转换为医患对话任务

作者：Claude Sonnet 4.5
日期：2025-03-22
"""

import json
import random
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

# Import PrimeKG loader from same package
from .kg_loader import PrimeKGLoader, RealMedicalKnowledgeGraph


# ========================================
# Data Structures
# ========================================

@dataclass
class WalkPath:
    """Random Walk 路径"""
    nodes: List[str] = field(default_factory=list)
    edges: List[Dict] = field(default_factory=list)
    weights: List[float] = field(default_factory=list)

    def add_step(self, node: str, edge_info: Dict, weight: float):
        """添加一步"""
        self.nodes.append(node)
        self.edges.append(edge_info)
        self.weights.append(weight)

    def get_path_summary(self) -> str:
        """获取路径摘要"""
        if not self.nodes:
            return "Empty path"

        summary = []
        for i, node in enumerate(self.nodes):
            if i == 0:
                summary.append(f"Start: {node}")
            elif i < len(self.edges):
                edge = self.edges[i]
                edge_type = edge.get("edge_type", "unknown")
                summary.append(f" --[{edge_type}]--> {node}")

        return "\n".join(summary)


@dataclass
class ConsultationTask:
    """医患问诊任务"""
    task_id: str
    path: WalkPath
    patient_profile: Dict[str, Any]
    dialogue_turns: List[Dict[str, str]]
    metadata: Dict[str, Any]


# ========================================
# PrimeKG Adapter
# ========================================

class PrimeKGAdapter:
    """
    PrimeKG 适配器

    将 PrimeKG 的数据结构适配为 Random Walk 需要的格式：
    - 节点类型映射
    - 边类型映射
    - 路径模式定义
    """

    def __init__(self, real_kg: RealMedicalKnowledgeGraph):
        """
        初始化适配器

        Args:
            real_kg: 真实的 PrimeKG 知识图谱
        """
        self.real_kg = real_kg

        # Disease prevalence boost: common diseases get higher weight so the walk
        # prefers clinically realistic diagnoses over rare ones.
        self.COMMON_DISEASE_BOOST = {
            "hypertension": 5.0,
            "diabetes": 5.0,
            "type 2 diabetes": 5.0,
            "type 1 diabetes": 3.0,
            "coronary artery disease": 4.0,
            "heart failure": 2.5,
            "copd": 3.5,
            "asthma": 3.5,
            "depression": 3.0,
            "chronic kidney disease": 3.0,
            "obesity": 2.5,
            "pneumonia": 2.5,
            "anemia": 2.0,
            "hyperlipidemia": 2.5,
            "gout": 2.0,
            "osteoporosis": 2.0,
            "arthritis": 2.0,
            "migraine": 2.0,
            "anxiety": 2.0,
            "insomnia": 2.0,
            "stroke": 2.5,
        }

        # PrimeKG 节点类型到 Random Walk 类型的映射
        self.node_type_mapping = {
            "disease": "disease",
            "drug": "treatment",
            "effect/phenotype": "symptom",
            "anatomy": "anatomy",
            "gene/protein": "biological_marker"
        }

        # PrimeKG 边类型到 Random Walk 类型的映射
        self.edge_type_mapping = {
            "indication": "treats",              # 药物适应症
            "contraindication": "contraindicates",  # 禁忌症
            "phenotype present": "causes",       # 疾病导致症状
            "phenotype absent": "excludes",      # 排除症状
            "target": "targets",                 # 药物靶点
            "enzyme": "metabolizes",             # 酶代谢
            "transporter": "transports",         # 转运
            "ppi": "interacts_with",             # 蛋白质相互作用
        }

        # 路径模式定义（扩展版：多路径、双向遍历）
        self.path_patterns = {
            # === 原有路径 ===
            "symptom_to_disease": {
                "from_types": ["effect/phenotype"],
                "to_types": ["disease"],
                "edge_types": ["phenotype present"],
                "description": "症状到疾病"
            },
            "disease_to_drug": {
                "from_types": ["disease"],
                "to_types": ["drug"],
                "edge_types": ["indication"],
                "description": "疾病到治疗药物"
            },
            "disease_to_contraindication": {
                "from_types": ["disease"],
                "to_types": ["drug"],
                "edge_types": ["contraindication"],
                "description": "疾病禁忌药物"
            },
            # === 反向路径（双向遍历）===
            "disease_to_symptom": {
                "from_types": ["disease"],
                "to_types": ["effect/phenotype"],
                "edge_types": ["rev_phenotype present"],
                "description": "疾病到症状（反向：用于描述疾病表现）"
            },
            "symptom_to_other_disease": {
                "from_types": ["effect/phenotype"],
                "to_types": ["disease"],
                "edge_types": ["phenotype present"],
                "description": "症状到其他疾病（鉴别诊断）",
                "exclude_source": True  # 排除已确认的疾病
            },
            # === 药物分子机制路径 ===
            "drug_to_target": {
                "from_types": ["drug"],
                "to_types": ["gene/protein"],
                "edge_types": ["target"],
                "description": "药物到靶点蛋白"
            },
            "drug_to_enzyme": {
                "from_types": ["drug"],
                "to_types": ["gene/protein"],
                "edge_types": ["enzyme"],
                "description": "药物酶代谢"
            },
            "drug_to_transporter": {
                "from_types": ["drug"],
                "to_types": ["gene/protein"],
                "edge_types": ["transporter"],
                "description": "药物转运体"
            },
            # === 药物相互作用路径 ===
            "drug_to_drug_interaction": {
                "from_types": ["drug"],
                "to_types": ["drug"],
                "edge_types": ["ddi"],
                "description": "药物-药物相互作用"
            },
            # === 蛋白相互作用路径 ===
            "protein_to_protein": {
                "from_types": ["gene/protein"],
                "to_types": ["gene/protein"],
                "edge_types": ["ppi"],
                "description": "蛋白质-蛋白质相互作用"
            },
            # === 疾病通路路径 ===
            "disease_to_pathway": {
                "from_types": ["disease"],
                "to_types": ["pathway"],
                "edge_types": ["associates_with"],
                "description": "疾病到生物通路"
            },
            # === 标签外使用 ===
            "disease_to_offlabel_drug": {
                "from_types": ["disease"],
                "to_types": ["drug"],
                "edge_types": ["off-label use"],
                "description": "疾病到标签外用药"
            }
        }

    def get_symptoms(self) -> List[Dict]:
        """
        获取所有症状节点

        Returns:
            症状节点列表 [{"id": ..., "name": ..., "type": ...}, ...]
        """
        symptoms = []

        # PrimeKG 中的 "effect/phenotype" 节点对应症状
        for node_id, node_info in self.real_kg.nodes.items():
            if node_info["type"] == "effect/phenotype":
                symptoms.append({
                    "id": node_id,
                    "name": node_info["name"],
                    "type": node_info["type"]
                })

        return symptoms

    def get_diseases(self) -> List[Dict]:
        """
        获取所有疾病节点

        Returns:
            疾病节点列表
        """
        diseases = []

        for node_id, node_info in self.real_kg.nodes.items():
            if node_info["type"] == "disease":
                diseases.append({
                    "id": node_id,
                    "name": node_info["name"],
                    "type": node_info["type"]
                })

        return diseases

    def get_treatments(self) -> List[Dict]:
        """
        获取所有治疗（药物）节点

        Returns:
            药物节点列表
        """
        treatments = []

        for node_id, node_info in self.real_kg.nodes.items():
            if node_info["type"] == "drug":
                treatments.append({
                    "id": node_id,
                    "name": node_info["name"],
                    "type": node_info["type"]
                })

        return treatments

    def get_neighbors_by_pattern(
        self,
        node_id: str,
        pattern_name: str
    ) -> List[Tuple[str, float]]:
        """
        根据路径模式获取邻居节点

        Args:
            node_id: 当前节点ID
            pattern_name: 路径模式名称

        Returns:
            [(邻居节点ID, 权重), ...]
        """
        if pattern_name not in self.path_patterns:
            return []

        pattern = self.path_patterns[pattern_name]
        target_types = pattern["to_types"]
        edge_types = pattern["edge_types"]

        neighbors = []

        # 从 PrimeKG 获取邻居
        all_neighbors = self.real_kg.get_neighbors(
            node_id,
            edge_type=None,  # 不过滤边类型，下面手动过滤
            direction="out"
        )

        for neighbor_id, weight in all_neighbors:
            # 检查边类型是否符合模式
            edge_data = self.real_kg.graph.get_edge_data(node_id, neighbor_id)
            if edge_data is None:
                continue

            edge_type = edge_data.get("edge_type", "")

            if edge_type not in edge_types:
                continue

            # 检查目标节点类型是否符合模式
            neighbor_info = self.real_kg.get_node_info(neighbor_id)
            if neighbor_info is None:
                continue

            if neighbor_info["type"] not in target_types:
                continue

            # 符合模式！
            neighbors.append((neighbor_id, weight))

        return neighbors

    def find_symptom_to_disease_path(
        self,
        symptom_id: str,
        max_diseases: int = 5
    ) -> List[Tuple[str, float]]:
        """
        找到症状 → 疾病的路径（带常见疾病加权）

        Args:
            symptom_id: 症状节点ID
            max_diseases: 最多返回多少个疾病

        Returns:
            [(疾病ID, 权重), ...] 按加权后权重排序
        """
        neighbors = self.get_neighbors_by_pattern(
            symptom_id,
            "symptom_to_disease"
        )
        if not neighbors:
            return []

        boosted = []
        for node_id, weight in neighbors:
            info = self.real_kg.get_node_info(node_id)
            name = (info.get("name", "") or "").lower() if info else ""
            boost = 1.0
            for key, b in self.COMMON_DISEASE_BOOST.items():
                if key in name:
                    boost = b
                    break
            boosted.append((node_id, weight * boost))

        boosted.sort(key=lambda x: x[1], reverse=True)
        return boosted[:max_diseases]

    def find_disease_to_treatment_path(
        self,
        disease_id: str,
        max_treatments: int = 5
    ) -> List[Tuple[str, float]]:
        """
        找到疾病 → 治疗的路径

        Args:
            disease_id: 疾病节点ID
            max_treatments: 最多返回多少个治疗

        Returns:
            [(治疗ID, 权重), ...]
        """
        return self.get_neighbors_by_pattern(
            disease_id,
            "disease_to_drug"
        )[:max_treatments]

    def find_differential_diagnoses(
        self,
        symptom_id: str,
        exclude_disease_id: Optional[str] = None,
        max_results: int = 5
    ) -> List[Tuple[str, float]]:
        """
        通过症状找到鉴别诊断候选（排除已确认的疾病）

        带常见疾病加权，优先返回临床常见的鉴别诊断

        Args:
            symptom_id: 症状节点ID
            exclude_disease_id: 已确认的疾病ID（排除）
            max_results: 最多返回多少个候选

        Returns:
            [(疾病ID, 权重), ...]
        """
        candidates = self.get_neighbors_by_pattern(
            symptom_id,
            "symptom_to_disease"
        )
        if exclude_disease_id:
            candidates = [(nid, w) for nid, w in candidates if nid != exclude_disease_id]

        # Apply disease prevalence boost
        boosted = []
        for node_id, weight in candidates:
            info = self.real_kg.get_node_info(node_id)
            name = (info.get("name", "") or "").lower() if info else ""
            boost = 1.0
            for key, b in self.COMMON_DISEASE_BOOST.items():
                if key in name:
                    boost = b
                    break
            boosted.append((node_id, weight * boost))

        boosted.sort(key=lambda x: x[1], reverse=True)
        return boosted[:max_results]

    def find_disease_symptoms(
        self,
        disease_id: str,
        max_symptoms: int = 10
    ) -> List[Tuple[str, float]]:
        """
        找到疾病的所有症状（反向遍历）

        Args:
            disease_id: 疾病节点ID
            max_symptoms: 最多返回多少个症状

        Returns:
            [(症状ID, 权重), ...]
        """
        # 尝试反向边
        neighbors = self.get_neighbors_by_pattern(
            disease_id,
            "disease_to_symptom"
        )
        # 如果没有反向边，尝试正向边中的 phenotype present
        if not neighbors:
            all_neighbors = self.real_kg.get_neighbors(
                disease_id,
                edge_type=None,
                direction="out"
            )
            for neighbor_id, weight in all_neighbors:
                neighbor_info = self.real_kg.get_node_info(neighbor_id)
                if neighbor_info and neighbor_info["type"] == "effect/phenotype":
                    neighbors.append((neighbor_id, weight))
        return neighbors[:max_symptoms]

    def find_drug_interactions(
        self,
        drug_id: str,
        max_interactions: int = 5
    ) -> List[Tuple[str, float]]:
        """
        找到药物的相互作用

        Args:
            drug_id: 药物节点ID
            max_interactions: 最多返回多少个相互作用

        Returns:
            [(药物ID, 权重), ...]
        """
        return self.get_neighbors_by_pattern(
            drug_id,
            "drug_to_drug_interaction"
        )[:max_interactions]

    def get_neighbors_bidirectional(
        self,
        node_id: str,
        target_type: str,
        max_results: int = 10
    ) -> List[Tuple[str, float]]:
        """
        双向获取邻居节点（同时搜索正向和反向边）

        Args:
            node_id: 节点ID
            target_type: 目标节点类型
            max_results: 最多返回多少个邻居

        Returns:
            [(邻居ID, 权重), ...]
        """
        neighbors = []
        seen = set()

        # 正向邻居
        for neighbor_id, weight in self.real_kg.get_neighbors(node_id, direction="out"):
            if neighbor_id in seen:
                continue
            neighbor_info = self.real_kg.get_node_info(neighbor_id)
            if neighbor_info and neighbor_info["type"] == target_type:
                neighbors.append((neighbor_id, weight))
                seen.add(neighbor_id)

        # 反向邻居
        for neighbor_id, weight in self.real_kg.get_neighbors(node_id, direction="in"):
            if neighbor_id in seen:
                continue
            neighbor_info = self.real_kg.get_node_info(neighbor_id)
            if neighbor_info and neighbor_info["type"] == target_type:
                neighbors.append((neighbor_id, weight))
                seen.add(neighbor_id)

        return neighbors[:max_results]


# ========================================
# PrimeKG Random Walk Generator
# ========================================

class PrimeKGRandomWalkGenerator:
    """
    PrimeKG Random Walk 生成器

    在 PrimeKG 知识图谱上进行 Random Walk，生成医疗问诊路径。

    路径模式：
    1. symptom (effect/phenotype) → disease → drug (treatment)
    2. symptom → disease → drug (contraindication)
    """

    def __init__(self, real_kg: RealMedicalKnowledgeGraph):
        """
        初始化生成器

        Args:
            real_kg: 真实的 PrimeKG 知识图谱
        """
        self.real_kg = real_kg
        self.adapter = PrimeKGAdapter(real_kg)

        self.walk_configs = {
            "short": {"max_steps": 3, "exploration_prob": 0.1},
            "medium": {"max_steps": 5, "exploration_prob": 0.2},
            "long": {"max_steps": 7, "exploration_prob": 0.3}
        }

    def generate_walk(
        self,
        start_symptom_id: str,
        walk_type: str = "medium",
        seed: Optional[int] = None
    ) -> WalkPath:
        """
        生成 Random Walk 路径

        Args:
            start_symptom_id: 起始症状节点ID
            walk_type: 路径类型（short/medium/long）
            seed: 随机种子

        Returns:
            WalkPath 对象
        """
        if seed is not None:
            random.seed(seed)

        config = self.walk_configs.get(walk_type, self.walk_configs["medium"])
        max_steps = config["max_steps"]
        exploration_prob = config["exploration_prob"]

        path = WalkPath()
        current_node = start_symptom_id

        # 添加起始节点
        start_info = self.real_kg.get_node_info(current_node)
        path.add_step(current_node, {
            "node_type": start_info.get("type", "unknown"),
            "node_name": start_info.get("name", "unknown")
        }, 1.0)

        # 状态机
        state = "symptom"  # symptom → disease → treatment

        for step in range(max_steps):
            if state == "symptom":
                # 症状 → 疾病
                neighbors = self.adapter.find_symptom_to_disease_path(
                    current_node,
                    max_diseases=10
                )

                if not neighbors:
                    break

                # 加权随机选择
                next_node, weight = self._weighted_random_choice(neighbors)

                # 记录边
                edge_info = self._get_edge_info(current_node, next_node)
                path.add_step(next_node, edge_info, weight)

                state = "disease"
                current_node = next_node

            elif state == "disease":
                # 疾病 → 治疗
                # 随机选择：适应症 (70%) 或 禁忌症 (30%)
                if random.random() < 0.7:
                    neighbors = self.adapter.find_disease_to_treatment_path(
                        current_node,
                        max_treatments=10
                    )
                else:
                    # 找禁忌症
                    neighbors = self.adapter.get_neighbors_by_pattern(
                        current_node,
                        "disease_to_contraindication"
                    )[:10]

                if not neighbors:
                    break

                next_node, weight = self._weighted_random_choice(neighbors)

                edge_info = self._get_edge_info(current_node, next_node)
                path.add_step(next_node, edge_info, weight)

                state = "treatment"
                current_node = next_node

            elif state == "treatment":
                # 治疗 → 结束
                break

            # 探索性提前终止
            if random.random() < exploration_prob and len(path.nodes) >= 3:
                break

        return path

    def _weighted_random_choice(
        self,
        neighbors: List[Tuple[str, float]]
    ) -> Tuple[str, float]:
        """加权随机选择"""
        nodes, weights = zip(*neighbors)
        total_weight = sum(weights)

        if total_weight == 0:
            return random.choice(neighbors)

        normalized_weights = [w / total_weight for w in weights]
        chosen_index = random.choices(
            range(len(nodes)),
            weights=normalized_weights,
            k=1
        )[0]

        return nodes[chosen_index], weights[chosen_index]

    def _get_edge_info(self, source: str, target: str) -> Dict:
        """获取边信息"""
        edge_data = self.real_kg.graph.get_edge_data(source, target)

        if edge_data is None:
            return {
                "source": source,
                "target": target,
                "edge_type": "unknown",
                "weight": 0.5
            }

        return {
            "source": source,
            "target": target,
            "edge_type": edge_data.get("edge_type", "unknown"),
            "weight": edge_data.get("weight", 0.5)
        }

    def generate_multiple_walks(
        self,
        start_symptom_id: str,
        num_walks: int = 10,
        walk_type: str = "medium"
    ) -> List[WalkPath]:
        """
        生成多条 Random Walk 路径

        Args:
            start_symptom_id: 起始症状节点ID
            num_walks: 路径数量
            walk_type: 路径类型

        Returns:
            路径列表
        """
        paths = []

        for i in range(num_walks):
            # 使用不同的种子确保多样性
            path = self.generate_walk(
                start_symptom_id,
                walk_type=walk_type,
                seed=i
            )
            paths.append(path)

        return paths


# ========================================
# Multi-Path Walk Data Structures
# ========================================

@dataclass
class WalkState:
    """状态机中的节点状态"""
    state_type: str           # symptom, disease, differential, drug, interaction, comorbidity, target, enzyme, conclusion
    node_id: str
    node_info: Dict
    depth: int
    branch_id: int = 0       # 用于追踪并行分支
    metadata: Dict = field(default_factory=dict)


@dataclass
class MultiPathWalkResult:
    """多路径遍历结果"""
    main_path: WalkPath                                    # 主要诊断路径
    branch_paths: List[WalkPath] = field(default_factory=list)  # 分支路径（鉴别诊断、共病）
    comorbid_diseases: List[Dict] = field(default_factory=list)  # 共病信息
    differential_candidates: List[Dict] = field(default_factory=list)  # 鉴别诊断候选
    drug_interactions: List[Dict] = field(default_factory=list)   # 药物相互作用
    total_depth: int = 0
    walk_complexity: str = "simple"  # simple, moderate, complex, comorbid
    walk_type: str = "medium"


# ========================================
# Multi-Path Random Walk Generator
# ========================================

class MultiPathWalkGenerator:
    """
    多路径 Random Walk 生成器

    支持：
    1. 8+ 状态的状态机（非仅 symptom->disease->treatment）
    2. 分支路径（鉴别诊断、共病）
    3. 双向遍历
    4. 药物相互作用检测
    5. 多种复杂度级别

    状态转换：
    symptom -> disease -> differential_search -> related_symptoms
           -> drug_indication -> drug_interaction_check -> drug_target
           -> drug_contraindication -> comorbidity_disease -> conclusion
    """

    def __init__(self, real_kg: RealMedicalKnowledgeGraph):
        """
        初始化

        Args:
            real_kg: 真实的 PrimeKG 知识图谱
        """
        self.real_kg = real_kg
        self.adapter = PrimeKGAdapter(real_kg)

        self.walk_configs = {
            "short": {
                "max_steps": 4,
                "exploration_prob": 0.1,
                "branch_prob": 0.0,
                "comorbidity_prob": 0.0,
                "max_differentials": 0,
                "max_drug_interactions": 0
            },
            "medium": {
                "max_steps": 7,
                "exploration_prob": 0.2,
                "branch_prob": 0.3,
                "comorbidity_prob": 0.0,
                "max_differentials": 2,
                "max_drug_interactions": 1
            },
            "long": {
                "max_steps": 10,
                "exploration_prob": 0.3,
                "branch_prob": 0.3,
                "comorbidity_prob": 0.2,
                "max_differentials": 3,
                "max_drug_interactions": 2
            },
            "complex": {
                "max_steps": 14,
                "exploration_prob": 0.3,
                "branch_prob": 0.4,
                "comorbidity_prob": 0.4,
                "max_differentials": 4,
                "max_drug_interactions": 3
            },
            "comorbid": {
                "max_steps": 16,
                "exploration_prob": 0.2,
                "branch_prob": 0.5,
                "comorbidity_prob": 0.6,
                "max_differentials": 3,
                "max_drug_interactions": 4
            }
        }

        # Minimum walk depth per walk type — prevents shallow walks
        self.MIN_WALK_DEPTH = {
            "short": 3, "medium": 5, "long": 7,
            "complex": 9, "comorbid": 11,
        }

    def generate_complex_walk(
        self,
        start_symptom_id: str,
        walk_type: str = "medium",
        seed: Optional[int] = None
    ) -> MultiPathWalkResult:
        """
        生成复杂的多路径 Random Walk

        Args:
            start_symptom_id: 起始症状节点ID
            walk_type: 路径类型（short/medium/long/complex/comorbid）
            seed: 随机种子

        Returns:
            MultiPathWalkResult 对象
        """
        if seed is not None:
            random.seed(seed)

        config = self.walk_configs.get(walk_type, self.walk_configs["medium"])
        max_steps = config["max_steps"]
        branch_prob = config["branch_prob"]
        comorbidity_prob = config["comorbidity_prob"]

        # 初始化主路径
        main_path = WalkPath()
        start_info = self.real_kg.get_node_info(start_symptom_id)
        main_path.add_step(start_symptom_id, {
            "node_type": start_info.get("type", "unknown"),
            "node_name": start_info.get("name", "unknown"),
            "state": "symptom"
        }, 1.0)

        # 状态机
        state = "symptom"
        current_node = start_symptom_id
        visited_nodes = {start_symptom_id}
        primary_disease_id = None
        drug_interactions = []
        differential_candidates = []
        branch_paths = []
        comorbid_diseases = []
        min_depth = self.MIN_WALK_DEPTH.get(walk_type, 4)

        for step in range(max_steps):
            next_state = None
            next_node = None

            if state == "symptom":
                # 症状 -> 疾病
                neighbors = self.adapter.find_symptom_to_disease_path(
                    current_node, max_diseases=10
                )
                if neighbors:
                    next_node, weight = self._weighted_random_choice(neighbors)
                    next_state = "disease"
                    primary_disease_id = next_node

                    # 概率性分支：鉴别诊断
                    if random.random() < branch_prob:
                        differentials = self.adapter.find_differential_diagnoses(
                            current_node,
                            exclude_disease_id=next_node,
                            max_results=config["max_differentials"]
                        )
                        for diff_id, diff_weight in differentials:
                            diff_info = self.real_kg.get_node_info(diff_id)
                            if diff_info:
                                differential_candidates.append({
                                    "id": diff_id,
                                    "name": diff_info.get("name", "Unknown"),
                                    "weight": diff_weight
                                })

            elif state == "disease":
                # 疾病 -> 多种可能
                roll = random.random()
                if roll < 0.6:
                    # 疾病 -> 治疗药物
                    neighbors = self.adapter.find_disease_to_treatment_path(
                        current_node, max_treatments=10
                    )
                    if neighbors:
                        next_node, weight = self._weighted_random_choice(neighbors)
                        next_state = "drug_indication"
                elif roll < 0.8:
                    # 疾病 -> 禁忌药物
                    neighbors = self.adapter.get_neighbors_by_pattern(
                        current_node, "disease_to_contraindication"
                    )[:10]
                    if neighbors:
                        next_node, weight = self._weighted_random_choice(neighbors)
                        next_state = "drug_contraindication"
                else:
                    # 疾病 -> 相关症状（扩展症状描述）
                    symptoms = self.adapter.find_disease_symptoms(
                        current_node, max_symptoms=10
                    )
                    unvisited = [(sid, w) for sid, w in symptoms if sid not in visited_nodes]
                    if unvisited:
                        next_node, weight = random.choice(unvisited)
                        next_state = "related_symptom"

                # 概率性分支：共病
                if random.random() < comorbidity_prob and primary_disease_id:
                    comorbid = self._find_comorbid_simple(
                        primary_disease_id,
                        exclude=visited_nodes
                    )
                    if comorbid:
                        comorbid_diseases.append(comorbid)

            elif state == "drug_indication":
                # 药物 -> 检查相互作用/靶点/酶
                roll = random.random()
                if roll < 0.4:
                    # 药物 -> 药物相互作用
                    interactions = self.adapter.find_drug_interactions(
                        current_node, max_interactions=config["max_drug_interactions"]
                    )
                    if interactions:
                        next_node, weight = random.choice(interactions)
                        next_state = "drug_interaction"
                        drug1_info = self.real_kg.get_node_info(current_node)
                        drug2_info = self.real_kg.get_node_info(next_node)
                        drug_interactions.append({
                            "drug1": drug1_info.get("name", "Unknown") if drug1_info else "Unknown",
                            "drug2": drug2_info.get("name", "Unknown") if drug2_info else "Unknown",
                            "severity": "moderate"
                        })
                    else:
                        next_state = "conclusion"
                elif roll < 0.7:
                    # 药物 -> 靶点
                    targets = self.adapter.get_neighbors_by_pattern(
                        current_node, "drug_to_target"
                    )[:5]
                    if targets:
                        next_node, weight = random.choice(targets)
                        next_state = "target"
                else:
                    next_state = "conclusion"

            elif state == "drug_contraindication":
                next_state = "conclusion"

            elif state == "drug_interaction":
                next_state = "conclusion"

            elif state == "target":
                # 靶点 -> 可以继续探索蛋白质相互作用
                ppi = self.adapter.get_neighbors_by_pattern(
                    current_node, "protein_to_protein"
                )[:3]
                if ppi and random.random() < 0.3:
                    next_node, weight = random.choice(ppi)
                    next_state = "enzyme"
                else:
                    next_state = "conclusion"

            elif state == "related_symptom":
                # 相关症状 -> 可能回到疾病发现
                next_state = "conclusion"

            elif state == "enzyme":
                next_state = "conclusion"

            elif state == "conclusion":
                break

            # 添加步骤
            if next_node and next_state and next_state != "conclusion":
                edge_info = self._get_edge_info(current_node, next_node)
                edge_info["state"] = next_state
                main_path.add_step(next_node, edge_info, 1.0)
                visited_nodes.add(next_node)
                current_node = next_node
                state = next_state
            elif next_state == "conclusion":
                # Only terminate if we've reached minimum depth
                if len(main_path.nodes) >= min_depth:
                    break
                # Otherwise try alternate transition to extend walk
                alt_state, alt_node = self._try_alternate_transition(
                    state, current_node, visited_nodes
                )
                if alt_node and alt_state:
                    edge_info = self._get_edge_info(current_node, alt_node)
                    edge_info["state"] = alt_state
                    main_path.add_step(alt_node, edge_info, 1.0)
                    visited_nodes.add(alt_node)
                    current_node = alt_node
                    state = alt_state
                else:
                    break
            else:
                break

            # 探索性提前终止（遵守最小深度）
            if (random.random() < config["exploration_prob"]
                    and len(main_path.nodes) >= min_depth):
                break

        # 确定复杂度标签
        complexity = self._determine_complexity(
            walk_type, main_path, differential_candidates,
            comorbid_diseases, drug_interactions
        )

        return MultiPathWalkResult(
            main_path=main_path,
            branch_paths=branch_paths,
            comorbid_diseases=comorbid_diseases,
            differential_candidates=differential_candidates,
            drug_interactions=drug_interactions,
            total_depth=len(main_path.nodes),
            walk_complexity=complexity,
            walk_type=walk_type
        )

    def generate_multiple_complex_walks(
        self,
        start_symptom_id: str,
        num_walks: int = 10,
        walk_type: str = "medium"
    ) -> List[MultiPathWalkResult]:
        """生成多条复杂路径"""
        results = []
        for i in range(num_walks):
            result = self.generate_complex_walk(
                start_symptom_id,
                walk_type=walk_type,
                seed=i
            )
            results.append(result)
        return results

    def _weighted_random_choice(
        self,
        neighbors: List[Tuple[str, float]]
    ) -> Tuple[str, float]:
        """加权随机选择"""
        nodes, weights = zip(*neighbors)
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(neighbors)
        normalized = [w / total_weight for w in weights]
        idx = random.choices(range(len(nodes)), weights=normalized, k=1)[0]
        return nodes[idx], weights[idx]

    def _get_edge_info(self, source: str, target: str) -> Dict:
        """获取边信息（含目标节点名称）"""
        edge_data = self.real_kg.graph.get_edge_data(source, target)
        if edge_data is None:
            result = {"source": source, "target": target, "edge_type": "unknown", "weight": 0.5}
        else:
            result = {
                "source": source,
                "target": target,
                "edge_type": edge_data.get("edge_type", "unknown"),
                "weight": edge_data.get("weight", 0.5)
            }
        # Add target node name for downstream consumers (tau2_converter)
        target_info = self.real_kg.get_node_info(target)
        if target_info:
            result["target_name"] = target_info.get("name", "")
            result["target_type"] = target_info.get("type", "")
        return result

    def _try_alternate_transition(
        self, state: str, current_node: str, visited_nodes: Set[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        When the state machine would hit "conclusion" before MIN_WALK_DEPTH,
        try alternate transitions to extend the walk.

        Returns (next_state, next_node) or (None, None).
        """
        if state == "drug_indication" or state == "drug_contraindication":
            # Try drug → target
            targets = self.adapter.get_neighbors_by_pattern(
                current_node, "drug_to_target"
            )[:5]
            unvisited = [(n, w) for n, w in targets if n not in visited_nodes]
            if unvisited:
                node, w = random.choice(unvisited)
                return "target", node
            # Try drug → enzyme
            enzymes = self.adapter.get_neighbors_by_pattern(
                current_node, "drug_to_enzyme"
            )[:3]
            unvisited = [(n, w) for n, w in enzymes if n not in visited_nodes]
            if unvisited:
                node, w = random.choice(unvisited)
                return "enzyme", node

        elif state == "drug_interaction":
            # Try drug → target
            targets = self.adapter.get_neighbors_by_pattern(
                current_node, "drug_to_target"
            )[:3]
            unvisited = [(n, w) for n, w in targets if n not in visited_nodes]
            if unvisited:
                node, w = random.choice(unvisited)
                return "target", node

        elif state == "related_symptom":
            # Try symptom → disease (different from primary)
            diseases = self.adapter.find_symptom_to_disease_path(
                current_node, max_diseases=5
            )
            unvisited = [(n, w) for n, w in diseases if n not in visited_nodes]
            if unvisited:
                node, w = self._weighted_random_choice(unvisited)
                return "disease", node

        elif state == "target" or state == "enzyme":
            # Try target → protein interaction
            ppi = self.adapter.get_neighbors_by_pattern(
                current_node, "protein_to_protein"
            )[:5]
            unvisited = [(n, w) for n, w in ppi if n not in visited_nodes]
            if unvisited:
                node, w = random.choice(unvisited)
                return "target", node

        return None, None

    def _find_comorbid_simple(
        self,
        disease_id: str,
        exclude: Set[str]
    ) -> Optional[Dict]:
        """简化版共病查找（不依赖 ComorbidityEngine）"""
        # 获取该疾病的症状
        symptoms = self.adapter.find_disease_symptoms(disease_id, max_symptoms=10)
        if not symptoms:
            return None

        # 对每个症状找其他疾病
        for symptom_id, weight in symptoms:
            other_diseases = self.adapter.find_differential_diagnoses(
                symptom_id,
                exclude_disease_id=disease_id,
                max_results=3
            )
            for other_id, other_weight in other_diseases:
                if other_id not in exclude:
                    info = self.real_kg.get_node_info(other_id)
                    if info:
                        return {
                            "id": other_id,
                            "name": info.get("name", "Unknown"),
                            "overlap_symptom": self.real_kg.get_node_info(symptom_id).get("name", "") if self.real_kg.get_node_info(symptom_id) else ""
                        }
        return None

    def _determine_complexity(
        self,
        walk_type: str,
        main_path: WalkPath,
        differentials: List,
        comorbidities: List,
        interactions: List
    ) -> str:
        """确定复杂度标签"""
        if walk_type in ("short",) or len(main_path.nodes) <= 4:
            return "simple"
        elif comorbidities:
            return "comorbid"
        elif differentials or interactions or len(main_path.nodes) >= 8:
            return "complex"
        else:
            return "moderate"


# ========================================
# PrimeKG Task Generator
# ========================================

class PrimeKGTaskGenerator:
    """
    PrimeKG 任务生成器

    将 Random Walk 路径转换为医患对话任务
    """

    def __init__(self, real_kg: RealMedicalKnowledgeGraph):
        """
        初始化任务生成器

        Args:
            real_kg: 真实的 PrimeKG 知识图谱
        """
        self.real_kg = real_kg

    def generate_task(
        self,
        path: WalkPath,
        task_id: str
    ) -> ConsultationTask:
        """
        生成医患对话任务

        Args:
            path: Random Walk 路径
            task_id: 任务ID

        Returns:
            ConsultationTask 对象
        """
        # 生成患者档案
        patient_profile = self._generate_patient_profile(path)

        # 生成对话轮次
        dialogue_turns = self._generate_dialogue_turns(path, patient_profile)

        # 生成元数据
        metadata = self._generate_metadata(path)

        return ConsultationTask(
            task_id=task_id,
            path=path,
            patient_profile=patient_profile,
            dialogue_turns=dialogue_turns,
            metadata=metadata
        )

    def _generate_patient_profile(self, path: WalkPath) -> Dict:
        """生成患者档案"""
        if not path.nodes:
            return {}

        # 第一个节点是症状
        symptom_id = path.nodes[0]
        symptom_info = self.real_kg.get_node_info(symptom_id)

        # 第二个节点是疾病
        disease_id = path.nodes[1] if len(path.nodes) > 1 else None
        disease_info = self.real_kg.get_node_info(disease_id) if disease_id else None

        profile = {
            "age": random.randint(30, 75),
            "gender": random.choice(["male", "female"]),
            "chief_complaint": symptom_info.get("name", "Unknown symptom"),
            "duration_days": random.randint(1, 30),
            "severity": random.choice(["mild", "moderate", "severe"])
        }

        if disease_info:
            profile["underlying_condition"] = disease_info.get("name", "Unknown")

        return profile

    def _generate_dialogue_turns(
        self,
        path: WalkPath,
        patient_profile: Dict
    ) -> List[Dict[str, str]]:
        """生成对话轮次"""
        turns = []

        if not path.nodes:
            return turns

        # Turn 1: 患者主诉
        symptom = self.real_kg.get_node_info(path.nodes[0])
        turns.append({
            "role": "patient",
            "content": f"Doctor, I've been experiencing {symptom.get('name', 'symptoms')} for about {patient_profile['duration_days']} days."
        })

        # Turn 2: 医生询问
        turns.append({
            "role": "doctor",
            "content": f"I see. Can you describe the {symptom.get('name', 'symptoms')} in more detail? Is it {patient_profile['severity']}?"
        })

        # Turn 3: 患者回答
        turns.append({
            "role": "patient",
            "content": f"Yes, it's quite {patient_profile['severity']}. I'm worried about what might be causing this."
        })

        # 如果有疾病节点，添加诊断
        if len(path.nodes) > 1:
            disease = self.real_kg.get_node_info(path.nodes[1])
            turns.append({
                "role": "doctor",
                "content": f"Based on your symptoms, I suspect you may have {disease.get('name', 'a condition')}. Let me explain the treatment options."
            })

        # 如果有治疗节点，添加治疗建议
        if len(path.nodes) > 2:
            treatment = self.real_kg.get_node_info(path.nodes[2])
            edge = path.edges[2] if len(path.edges) > 2 else {}

            edge_type = edge.get("edge_type", "")

            if edge_type == "indication":
                turns.append({
                    "role": "doctor",
                    "content": f"I recommend {treatment.get('name', 'a medication')} which is indicated for your condition."
                })
            elif edge_type == "contraindication":
                turns.append({
                    "role": "doctor",
                    "content": f"Important note: {treatment.get('name', 'a medication')} is contraindicated for your condition, so we'll avoid that."
                })

        # 最后的总结
        turns.append({
            "role": "doctor",
            "content": "Do you have any questions about your diagnosis or treatment plan?"
        })

        return turns

    def _generate_metadata(self, path: WalkPath) -> Dict:
        """生成元数据"""
        return {
            "path_length": len(path.nodes),
            "node_types": [
                self.real_kg.get_node_info(n).get("type", "unknown")
                for n in path.nodes
                if self.real_kg.get_node_info(n) is not None
            ],
            "edge_types": [
                e.get("edge_type", "unknown")
                for e in path.edges
            ]
        }


# ========================================
# Complete Pipeline
# ========================================

# Lazy imports for complex task generation
_ComplexTaskComponents = None

def _get_complex_components():
    """延迟加载复杂任务组件"""
    global _ComplexTaskComponents
    if _ComplexTaskComponents is None:
        try:
            from .comorbidity_engine import ComorbidityEngine
            from .dialogue_builder import BehaviorAwareDialogueBuilder
            _ComplexTaskComponents = {
                'ComorbidityEngine': ComorbidityEngine,
                'BehaviorAwareDialogueBuilder': BehaviorAwareDialogueBuilder
            }
        except ImportError:
            _ComplexTaskComponents = {}
    return _ComplexTaskComponents

class PrimeKGRandomWalkPipeline:
    """
    完整的 PrimeKG Random Walk 流程

    1. 加载 PrimeKG
    2. 生成 Random Walk 路径
    3. 生成对话任务
    4. 导出为 Tau2 格式
    """

    # Symptom aliases: common lay terms → PrimeKG node names
    SYMPTOM_ALIASES = {
        "nausea": "abdominal symptom",
        "vomiting": "abdominal symptom",
        "dizziness": "vertigo",
        "shortness of breath": "dyspnea",
        "breathing difficulty": "dyspnea",
        "breathlessness": "dyspnea",
        "stomach pain": "abdominal pain",
        "belly pain": "abdominal pain",
        "tummy ache": "abdominal pain",
        "throwing up": "abdominal symptom",
        "being sick": "vomiting",
        "puking": "vomiting",
        "feeling sick": "nausea/vomiting",
        "passing out": "syncope",
        "fainting": "syncope",
        "blackout": "syncope",
        "heart beating fast": "palpitation",
        "racing heart": "palpitation",
        "heart pounding": "palpitation",
        "palpitations": "arrhythmia",
        "palpitation": "arrhythmia",
        "irregular heartbeat": "arrhythmia",
        "can't sleep": "insomnia",
        "trouble sleeping": "insomnia",
        "sleep problems": "insomnia",
        "feeling down": "depressed mood",
        "feeling sad": "depressed mood",
        "feeling blue": "depressed mood",
        "anxious": "anxiety",
        "worried": "anxiety",
        "nervous": "anxiety",
        "joint pain": "arthralgia",
        "aching joints": "arthralgia",
        "muscle pain": "myalgia",
        "muscle ache": "myalgia",
        "sore muscles": "myalgia",
        "earache": "otalgia",
        "ear pain": "otalgia",
        "sore throat": "pharyngitis",
        "throat pain": "pharyngitis",
        "runny nose": "rhinorrhea",
        "stuffy nose": "nasal congestion",
        "blocked nose": "nasal congestion",
        "thirst": "polydipsia",
        "excessive thirst": "polydipsia",
        "increased thirst": "polydipsia",
        "drinking a lot": "polydipsia",
        "numbness": "paresthesia",
        "tingling": "paresthesia",
        "pins and needles": "paresthesia",
        "swelling": "edema",
        "puffy": "edema",
        "water retention": "edema",
        "rash": "exanthem",
        "skin rash": "exanthem",
        "hives": "urticaria",
        "itching": "pruritus",
        "itchy skin": "pruritus",
        "blood in stool": "hematochezia",
        "blood in urine": "hematuria",
        "peeing blood": "hematuria",
        "constipated": "constipation",
        "can't poop": "constipation",
        "diarrhea": "diarrhea",
        "loose stools": "diarrhea",
        "weight loss": "weight loss",
        "losing weight": "weight loss",
        "gained weight": "weight gain",
        "gaining weight": "weight gain",
        "blurry vision": "blurred vision",
        "can't see clearly": "blurred vision",
        "vision problems": "visual impairment",
        "back pain": "back pain",
        "lower back pain": "back pain",
        "neck pain": "neck pain",
        "arm pain": "limb pain",
        "leg pain": "limb pain",
        "chest tightness": "chest discomfort",
        "chest pressure": "chest discomfort",
    }

    def __init__(
        self,
        use_cache: bool = True,
        focus_types: Optional[List[str]] = None
    ):
        """
        初始化流程

        Args:
            use_cache: 是否使用缓存
            focus_types: 关注的节点类型
        """
        print("\n" + "="*60)
        print(" PrimeKG Random Walk Pipeline")
        print("="*60)

        # 1. 加载 PrimeKG
        print("\n[Step 1/4] Loading PrimeKG...")

        if focus_types is None:
            focus_types = ["disease", "drug", "effect/phenotype", "gene/protein", "pathway"]

        self.loader = PrimeKGLoader()
        self.real_kg = RealMedicalKnowledgeGraph(self.loader)

        self.real_kg.load_from_primekg(
            version="v2",
            focus_types=focus_types,
            min_weight=0.0,
            keep_top_k=20,
            use_cache=use_cache
        )

        # 2. 初始化 Random Walk 生成器
        print("\n[Step 2/4] Initializing Random Walk Generator...")
        self.walk_generator = PrimeKGRandomWalkGenerator(self.real_kg)

        # 3. 初始化任务生成器
        print("\n[Step 3/4] Initializing Task Generator...")
        self.task_generator = PrimeKGTaskGenerator(self.real_kg)

        print("\n[Step 4/4] Pipeline ready!")

    def _resolve_symptom_keyword(self, symptom_keyword: str) -> Tuple[str, str]:
        """
        Resolve a symptom keyword to a PrimeKG node ID.

        Tries: exact match → alias → substring match → fuzzy fallback.

        Returns:
            (node_id, resolved_name)

        Raises:
            ValueError if no match found
        """
        # 1. Direct search
        results = self.real_kg.search_nodes(
            symptom_keyword, node_type="effect/phenotype", limit=1
        )
        if results:
            return results[0]["id"], results[0].get("name", symptom_keyword)

        # 2. Try alias
        alias = self.SYMPTOM_ALIASES.get(symptom_keyword.lower().strip())
        if alias:
            results = self.real_kg.search_nodes(
                alias, node_type="effect/phenotype", limit=1
            )
            if results:
                return results[0]["id"], results[0].get("name", alias)

        # 3. Try individual words
        words = [w for w in symptom_keyword.lower().split() if len(w) > 3]
        for word in words:
            results = self.real_kg.search_nodes(
                word, node_type="effect/phenotype", limit=1
            )
            if results:
                return results[0]["id"], results[0].get("name", word)
            # Try alias for individual word
            word_alias = self.SYMPTOM_ALIASES.get(word)
            if word_alias:
                results = self.real_kg.search_nodes(
                    word_alias, node_type="effect/phenotype", limit=1
                )
                if results:
                    return results[0]["id"], results[0].get("name", word_alias)

        raise ValueError(f"Symptom '{symptom_keyword}' not found in PrimeKG (tried aliases and partial matches)")

    def generate_consultation_task(
        self,
        symptom_keyword: str,
        walk_type: str = "medium",
        task_id: Optional[str] = None
    ) -> ConsultationTask:
        """
        生成完整的问诊任务

        Args:
            symptom_keyword: 症状关键词（用于搜索起始节点）
            walk_type: Random Walk 类型
            task_id: 任务ID

        Returns:
            ConsultationTask 对象
        """
        # 搜索症状节点（with alias resolution）
        symptom_id, symptom_name = self._resolve_symptom_keyword(symptom_keyword)

        # 生成 Random Walk 路径
        path = self.walk_generator.generate_walk(
            symptom_id,
            walk_type=walk_type
        )

        # 生成任务
        if task_id is None:
            task_id = f"primekg_task_{random.randint(1000, 9999)}"

        task = self.task_generator.generate_task(path, task_id)

        return task

    def _extract_disease_from_walk(self, walk_result) -> Tuple[str, Optional[str]]:
        """
        从 walk result 中提取疾病名称（多策略回退）

        Returns:
            (disease_name, disease_id)
        """
        # Strategy 1: Check main_path nodes for type "disease"
        for node_id in walk_result.main_path.nodes[1:]:
            info = self.real_kg.get_node_info(node_id)
            if info and info.get("type") == "disease":
                return info.get("name", "Unknown"), node_id

        # Strategy 2: Broader type check (some nodes may have variant types)
        for node_id in walk_result.main_path.nodes[1:]:
            info = self.real_kg.get_node_info(node_id)
            if info:
                node_type = info.get("type", "")
                if node_type in ("disease", "disease_or_phenotype"):
                    return info.get("name", "Unknown"), node_id

        # Strategy 3: Check edge metadata for disease states
        for edge in walk_result.main_path.edges:
            if edge.get("state") == "disease":
                target = edge.get("target", "")
                if target:
                    info = self.real_kg.get_node_info(target)
                    if info:
                        return info.get("name", "Unknown"), target

        # Strategy 4: Use comorbid diseases
        if walk_result.comorbid_diseases:
            first = walk_result.comorbid_diseases[0]
            return first.get("name", "Unknown"), first.get("id")

        # Strategy 5: Use differential candidates
        if walk_result.differential_candidates:
            first = walk_result.differential_candidates[0]
            return first.get("name", "Unknown"), first.get("id")

        return "Unknown", None

    def export_to_tau2(
        self,
        task: ConsultationTask,
        output_file: str
    ):
        """
        导出为 Tau2 格式

        Args:
            task: 问诊任务
            output_file: 输出文件路径
        """
        tau2_data = {
            "task_id": task.task_id,
            "patient_profile": task.patient_profile,
            "dialogue": task.dialogue_turns,
            "metadata": task.metadata,
            "path": {
                "nodes": task.path.nodes,
                "edges": task.path.edges
            }
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tau2_data, f, ensure_ascii=False, indent=2)

        print(f"\n[Export] Task saved to: {output_file}")

    def generate_complex_task(
        self,
        symptom_keyword: str,
        walk_type: str = "complex",
        difficulty: str = "L2",
        behavior_type: Optional[str] = None,
        task_id: Optional[str] = None
    ):
        """
        生成复杂的问诊任务（多路径、多轮对话、工具调用）

        Args:
            symptom_keyword: 症状关键词
            walk_type: 路径类型（short/medium/long/complex/comorbid）
            difficulty: 难度级别（L1/L2/L3）
            behavior_type: 患者行为类型（cooperative/forgetful/confused/concealing/pressuring/refusing）
            task_id: 任务ID

        Returns:
            ComplexConsultationTask 对象
        """
        components = _get_complex_components()

        if not components:
            raise ImportError(
                "Complex task components not available. "
                "Ensure comorbidity_engine.py and dialogue_builder.py exist."
            )

        # 搜索症状节点（with alias resolution）
        symptom_id, symptom_name = self._resolve_symptom_keyword(symptom_keyword)

        # 使用 MultiPathWalkGenerator
        walk_gen = MultiPathWalkGenerator(self.real_kg)
        walk_result = walk_gen.generate_complex_walk(
            symptom_id,
            walk_type=walk_type
        )

        # 生成患者档案
        disease_name, disease_id = self._extract_disease_from_walk(walk_result)

        patient_profile = {
            "age": random.randint(25, 80),
            "gender": random.choice(["male", "female"]),
            "chief_complaint": symptom_name,
            "duration_days": random.randint(3, 60),
            "severity": random.choice(["mild", "moderate", "severe"]),
            "underlying_condition": disease_name
        }

        # 使用 BehaviorAwareDialogueBuilder
        builder = components['BehaviorAwareDialogueBuilder'](self.real_kg)
        complex_task = builder.build_dialogue(
            walk_result=walk_result,
            patient_profile=patient_profile,
            difficulty_level=difficulty,
            behavior_type=behavior_type
        )

        if task_id:
            complex_task.task_id = task_id

        return complex_task

    def export_complex_task_to_tau2(
        self,
        complex_task,
        output_file: str
    ):
        """
        导出复杂任务为 tau2 格式

        Args:
            complex_task: ComplexConsultationTask 对象
            output_file: 输出文件路径
        """
        try:
            from ..utils.tau2_converter import convert_complex_task_to_tau2
        except ImportError:
            from generation.utils.tau2_converter import convert_complex_task_to_tau2

        tau2_data = convert_complex_task_to_tau2(complex_task)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tau2_data, f, ensure_ascii=False, indent=2)

        print(f"\n[Export] Complex task saved to: {output_file}")


# ========================================
# Demo / Testing
# ========================================

def demo_primekg_random_walk():
    """演示 PrimeKG Random Walk"""
    print("\n" + "="*60)
    print(" Demo: PrimeKG Random Walk Integration")
    print("="*60)

    # 1. 初始化流程
    pipeline = PrimeKGRandomWalkPipeline(
        use_cache=True,
        focus_types=["disease", "drug", "effect/phenotype"]
    )

    # 2. 生成任务
    print("\n" + "-"*60)
    print(" Generating consultation task...")
    print("-"*60)

    # 搜索可用的症状
    print("\nSearching for symptoms related to 'hypertension'...")
    symptoms = pipeline.real_kg.search_nodes(
        "hypertension",
        node_type="effect/phenotype",
        limit=5
    )

    if symptoms:
        print("Found symptoms:")
        for s in symptoms[:3]:
            print(f"  - {s['name']} (ID: {s['id'][:20]}...)")

        # 使用第一个症状生成任务
        symptom_name = symptoms[0]["name"]
        print(f"\nUsing symptom: {symptom_name}")

        task = pipeline.generate_consultation_task(
            symptom_keyword=symptom_name,
            walk_type="medium"
        )

        # 3. 打印结果
        print("\n" + "-"*60)
        print(" Generated Task:")
        print("-"*60)

        print(f"\nTask ID: {task.task_id}")
        print(f"\nPatient Profile:")
        for k, v in task.patient_profile.items():
            print(f"  {k}: {v}")

        print(f"\nPath Summary:")
        print(task.path.get_path_summary())

        print(f"\nDialogue Turns ({len(task.dialogue_turns)}):")
        for i, turn in enumerate(task.dialogue_turns, 1):
            role = turn["role"].capitalize()
            content = turn["content"][:80] + "..." if len(turn["content"]) > 80 else turn["content"]
            print(f"  {i}. [{role}] {content}")

        # 4. 导出
        output_file = "data/primekg_tasks/demo_task.json"
        pipeline.export_to_tau2(task, output_file)

        print("\n" + "="*60)
        print(" Demo Complete!")
        print("="*60)

        return task

    else:
        print("\nNo symptoms found matching 'hypertension'")
        print("Try different keywords like:")
        print("  - 'pain'")
        print("  - 'fever'")
        print("  - 'nausea'")

        return None


def demo_complex_generation():
    """演示复杂任务生成"""
    print("\n" + "="*60)
    print(" Demo: Complex Task Generation")
    print("="*60)

    pipeline = PrimeKGRandomWalkPipeline(
        use_cache=True,
        focus_types=["disease", "drug", "effect/phenotype", "gene/protein", "pathway"]
    )

    # 测试不同复杂度级别
    test_configs = [
        {"symptom": "headache", "walk_type": "medium", "difficulty": "L1", "behavior": "cooperative"},
        {"symptom": "chest pain", "walk_type": "complex", "difficulty": "L2", "behavior": "forgetful"},
        {"symptom": "fever", "walk_type": "comorbid", "difficulty": "L3", "behavior": "pressuring"},
    ]

    for config in test_configs:
        print(f"\n{'-'*60}")
        print(f" Config: {config}")
        print(f"{'-'*60}")

        try:
            task = pipeline.generate_complex_task(
                symptom_keyword=config["symptom"],
                walk_type=config["walk_type"],
                difficulty=config["difficulty"],
                behavior_type=config["behavior"]
            )

            print(f"\nTask ID: {task.task_id}")
            print(f"Walk Complexity: {task.walk_result.walk_complexity}")
            print(f"Path Depth: {task.walk_result.total_depth}")
            print(f"Differentials: {len(task.walk_result.differential_candidates)}")
            print(f"Comorbidities: {len(task.walk_result.comorbid_diseases)}")
            print(f"Drug Interactions: {len(task.walk_result.drug_interactions)}")
            print(f"Dialogue Turns: {len(task.all_turns)}")
            print(f"Required Tools: {task.required_tools}")
            print(f"Behavior: {task.behavior_type}")

            print(f"\nDialogue:")
            for i, turn in enumerate(task.all_turns, 1):
                role = turn["role"].capitalize()
                content = turn["content"][:100] + "..." if len(turn["content"]) > 100 else turn["content"]
                print(f"  {i}. [{role}] {content}")

        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "="*60)
    print(" Complex Generation Demo Complete!")
    print("="*60)
    import sys
    import io

    # 设置 UTF-8 编码
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 运行演示
    demo_primekg_random_walk()

    # 运行复杂任务生成演示
    demo_complex_generation()
