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

# Import PrimeKG loader
from primekg_loader import PrimeKGLoader, RealMedicalKnowledgeGraph


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

        # 路径模式定义（症状 → 疾病 → 治疗）
        self.path_patterns = {
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
        找到症状 → 疾病的路径

        Args:
            symptom_id: 症状节点ID
            max_diseases: 最多返回多少个疾病

        Returns:
            [(疾病ID, 权重), ...]
        """
        return self.get_neighbors_by_pattern(
            symptom_id,
            "symptom_to_disease"
        )[:max_diseases]

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

class PrimeKGRandomWalkPipeline:
    """
    完整的 PrimeKG Random Walk 流程

    1. 加载 PrimeKG
    2. 生成 Random Walk 路径
    3. 生成对话任务
    4. 导出为 Tau2 格式
    """

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
            focus_types = ["disease", "drug", "effect/phenotype"]

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
        # 搜索症状节点
        results = self.real_kg.search_nodes(
            symptom_keyword,
            node_type="effect/phenotype",
            limit=1
        )

        if not results:
            raise ValueError(f"Symptom '{symptom_keyword}' not found in PrimeKG")

        symptom_id = results[0]["id"]

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


if __name__ == "__main__":
    import sys
    import io

    # 设置 UTF-8 编码
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 运行演示
    demo_primekg_random_walk()
