#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真正的 PrimeKG 加载器

从 https://github.com/mims-harvard/PrimeKG 加载真实的医疗知识图谱

功能：
1. 下载 PrimeKG 数据
2. 解析 CSV 文件
3. 过滤医疗相关节点
4. 构建图结构
5. 优化 Random Walk 性能

作者：Claude Sonnet 4.5
日期：2025-03-21
"""

import os
import csv
import json
import requests
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
import networkx as nx
import numpy as np

# 缓存目录
CACHE_DIR = Path("data/primekg_cache")


class PrimeKGLoader:
    """PrimeKG 真实数据加载器"""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        初始化 PrimeKG 加载器

        Args:
            cache_dir: 缓存目录（默认为 data/primekg_cache）
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # PrimeKG 数据 URL（多个数据源）
        # 主要来源：Harvard Dataverse（官方）
        self.primekg_urls = {
            "harvard_dataverse": "https://dataverse.harvard.edu/api/access/datafile/6180620",
            "harvard_dataverse_alt": "https://dataverse.harvard.edu/api/access/datafile/6180620?format=original",
        }

        # 医疗相关的节点类型（基于 PrimeKG 实际类型）
        self.medical_node_types = {
            "disease",              # 疾病 (682K occurrences)
            "drug",                 # 药物 (5.6M occurrences)
            "gene/protein",         # 基因/蛋白质 (5.3M occurrences)
            "anatomy",              # 解剖 (3.1M occurrences)
            "effect/phenotype",     # 效应/表型 (514K occurrences)
            "pathway",              # 通路 (95K occurrences)
            "exposure",             # 暴露 (19K occurrences)
            "biological_process",   # 生物过程 (504K occurrences)
            "molecular_function",   # 分子功能 (193K occurrences)
            "cellular_component",   # 细胞成分 (186K occurrences)
        }

        # 医疗相关的边类型（基于 PrimeKG 实际边类型）
        self.medical_edge_types = {
            # PrimeKG 实际边类型
            "phenotype present",        # 表型存在
            "contraindication",         # 禁忌症
            "indication",               # 适应症
            "off-label use",           # 标签外使用
            "phenotype absent",        # 表型不存在
            "ppi",                     # protein-protein interaction
            "ddi",                     # drug-drug interaction
            "transporter",             # 转运体
            "target",                  # 靶向
            "enzyme",                  # 酶
            "carrier",                 # 载体
            "associates_with",         # 相关
            "interacts_with",          # 相互作用
            # 通用医疗边类型
            "treats",                  # 治疗
            "causes",                  # 导致
            "prevents",                # 预防
            "side_effect",             # 副作用
            "diagnoses",               # 诊断
            "palliates",               # 缓解
            "produces",                # 产生
            "targets",                 # 靶向
            "regulates",               # 调节
            "binds",                   # 结合
            "metabolizes",             # 代谢
            "expressed_in",            # 表达于
            "localized_in",            # 定位于
        }

        # 中文映射（英文→中文）
        self.node_type_translation = {
            "disease": "疾病",
            "drug/drug": "药物",
            "symptom": "症状",
            "phenotype": "表型",
            "anatomy": "解剖",
            "pathway": "通路",
            "gene": "基因",
            "protein": "蛋白质"
        }

    def download_primekg(self, version: str = "v2", force: bool = False) -> Path:
        """
        下载 PrimeKG 数据

        Args:
            version: PrimeKG 版本 (保留参数，但实际使用统一数据)
            force: 强制重新下载

        Returns:
            下载的文件路径
        """
        # PrimeKG 使用单一数据文件（kg.csv）
        filename = self.cache_dir / "primekg_kg.csv"

        if filename.exists() and not force:
            print(f"[PrimeKG] 使用缓存: {filename}")
            return filename

        print(f"[PrimeKG] 下载数据...")
        print(f"  来源: Harvard Dataverse")

        # 尝试所有可用的 URL
        for source_name, url in self.primekg_urls.items():
            print(f"  尝试: {source_name}")
            print(f"  URL: {url}")

            try:
                response = requests.get(url, stream=True, timeout=120)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))
                block_size = 8192
                downloaded = 0

                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=block_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = downloaded / total_size * 100
                                print(f"  进度: {progress:.1f}%", end='\r')

                file_size = os.path.getsize(filename) / 1024 / 1024
                print(f"\n[PrimeKG] [OK] Download complete: {file_size:.1f} MB")
                return filename

            except Exception as e:
                print(f"\n[PrimeKG] [FAIL] {source_name} failed: {e}")
                # 删除部分下载的文件
                if filename.exists():
                    filename.unlink()
                continue

        # 所有来源都失败
        raise Exception("所有数据源下载失败。请检查网络连接或稍后重试。")

    def parse_primekg_csv(self, csv_file: Path) -> Tuple[Dict, List[Dict]]:
        """
        解析 PrimeKG CSV 文件

        Args:
            csv_file: CSV 文件路径

        Returns:
            (节点字典, 边列表)
        """
        print(f"[PrimeKG] Parsing CSV file...")
        print(f"  File: {csv_file}")

        nodes = {}
        edges = []
        node_type_counts = defaultdict(int)
        edge_type_counts = defaultdict(int)

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # 读取头部
                sample = f.read(1024)
                f.seek(0)

                # 检测分隔符
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                # 使用 DictReader
                reader = csv.DictReader(f, delimiter=delimiter)

                # 读取列名
                fieldnames = reader.fieldnames
                print(f"  Columns: {fieldnames}")

                # 读取数据
                row_count = 0
                for row in reader:
                    row_count += 1

                    if row_count % 50000 == 0:
                        print(f"  Progress: {row_count} rows")

                    # PrimeKG CSV 格式：
                    # relation, display_relation, x_index, x_id, x_type, x_name, x_source,
                    # y_index, y_id, y_type, y_name, y_source

                    # 提取源节点
                    source_id = row.get("x_id", "")
                    source_name = row.get("x_name", "")
                    source_type = row.get("x_type", "")

                    # 提取目标节点
                    target_id = row.get("y_id", "")
                    target_name = row.get("y_name", "")
                    target_type = row.get("y_type", "")

                    # 提取边信息
                    edge_type = row.get("display_relation", row.get("relation", ""))

                    # 权重：PrimeKG 没有明确的权重，使用固定值
                    weight = 0.5

                    # 只处理医疗相关的节点和边
                    if not self._is_medical_node(source_type) or not self._is_medical_node(target_type):
                        continue

                    if not self._is_medical_edge(edge_type):
                        continue

                    # 添加节点
                    if source_id not in nodes:
                        nodes[source_id] = {
                            "id": source_id,
                            "name": source_name,
                            "type": source_type
                        }
                        node_type_counts[source_type] += 1

                    if target_id not in nodes:
                        nodes[target_id] = {
                            "id": target_id,
                            "name": target_name,
                            "type": target_type
                        }
                        node_type_counts[target_type] += 1

                    # 添加边
                    edges.append({
                        "source": source_id,
                        "target": target_id,
                        "edge_type": edge_type,
                        "weight": weight
                    })
                    edge_type_counts[edge_type] += 1

            print(f"\n[PrimeKG] [OK] Parsing complete")
            print(f"  Total rows: {row_count}")
            print(f"  Nodes: {len(nodes)}")
            print(f"  Edges: {len(edges)}")

            print(f"\nNode type distribution:")
            for node_type, count in sorted(node_type_counts.items(), key=lambda x: -x[1])[:10]:
                print(f"  {node_type}: {count}")

            print(f"\nEdge type distribution:")
            for edge_type, count in sorted(edge_type_counts.items(), key=lambda x: -x[1])[:10]:
                print(f"  {edge_type}: {count}")

            return nodes, edges

        except Exception as e:
            print(f"[PrimeKG] [FAIL] Parsing failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _is_medical_node(self, node_type: str) -> bool:
        """判断是否为医疗相关节点"""
        if not node_type:
            return False

        # 使用精确匹配（因为现在我们知道了 PrimeKG 的确切类型）
        return node_type in self.medical_node_types

    def _is_medical_edge(self, edge_type: str) -> bool:
        """判断是否为医疗相关边"""
        if not edge_type:
            return False

        # 使用精确匹配（因为现在我们知道了 PrimeKG 的确切边类型）
        return edge_type in self.medical_edge_types

    def filter_medical_subgraph(
        self,
        nodes: Dict,
        edges: List[Dict],
        focus_types: Optional[List[str]] = None
    ) -> Tuple[Dict, List[Dict]]:
        """
        过滤出医疗子图

        Args:
            nodes: 所有节点
            edges: 所有边
            focus_types: 重点关注节点类型（如 ["disease", "drug/drug", "symptom"]）

        Returns:
            (过滤后的节点, 过滤后的边)
        """
        print(f"\n[PrimeKG] 过滤医疗子图...")

        if focus_types is None:
            focus_types = ["disease", "drug/drug", "symptom", "phenotype"]

        print(f"  关注类型: {focus_types}")

        # 找出所有关注的节点
        focus_node_ids = set()
        for node_id, node_info in nodes.items():
            node_type = node_info["type"]
            if any(ft.lower() in node_type.lower() for ft in focus_types):
                focus_node_ids.add(node_id)

        print(f"  关注节点数: {len(focus_node_ids)}")

        # 找出这些节点的一跳邻居
        expanded_node_ids = set(focus_node_ids)
        for edge in edges:
            if edge["source"] in focus_node_ids:
                expanded_node_ids.add(edge["target"])
            if edge["target"] in focus_node_ids:
                expanded_node_ids.add(edge["source"])

        print(f"  扩展节点数: {len(expanded_node_ids)}")

        # 过滤节点
        filtered_nodes = {
            node_id: nodes[node_id]
            for node_id in expanded_node_ids
        }

        # 过滤边
        filtered_edges = [
            edge for edge in edges
            if edge["source"] in expanded_node_ids and edge["target"] in expanded_node_ids
        ]

        print(f"  过滤后节点数: {len(filtered_nodes)}")
        print(f"  过滤后边数: {len(filtered_edges)}")

        return filtered_nodes, filtered_edges

    def build_graph(
        self,
        nodes: Dict,
        edges: List[Dict],
        min_weight: float = 0.1
    ) -> nx.DiGraph:
        """
        构建NetworkX图

        Args:
            nodes: 节点字典
            edges: 边列表
            min_weight: 最小权重阈值

        Returns:
            NetworkX图对象
        """
        print(f"\n[PrimeKG] 构建图结构...")

        graph = nx.DiGraph()

        # 添加节点
        for node_id, node_info in nodes.items():
            graph.add_node(
                node_id,
                **node_info
            )

        # 添加边（过滤低权重边）
        for edge in edges:
            if edge["weight"] >= min_weight:
                graph.add_edge(
                    edge["source"],
                    edge["target"],
                    edge_type=edge["edge_type"],
                    weight=edge["weight"]
                )

        print(f"  图节点数: {graph.number_of_nodes()}")
        print(f"  图边数: {graph.number_of_edges()}")

        return graph

    def optimize_for_random_walk(
        self,
        graph: nx.DiGraph,
        keep_top_k: int = 10
    ) -> nx.DiGraph:
        """
        优化图结构以便 Random Walk

        优化策略：
        1. 移除孤立节点
        2. 只保留每个节点的前K个邻居
        3. 添加反向边（如果是DAG）

        Args:
            graph: 原始图
            keep_top_k: 每个节点保留的前K个邻居

        Returns:
            优化后的图
        """
        print(f"\n[PrimeKG] 优化图结构...")

        # 1. 移除孤立节点
        isolated_nodes = list(nx.isolates(graph))
        if isolated_nodes:
            graph.remove_nodes_from(isolated_nodes)
            print(f"  移除孤立节点: {len(isolated_nodes)}")

        # 2. 为每个节点只保留前K个邻居
        nodes_to_keep = set()

        for node in graph.nodes():
            # 获取所有出边
            out_edges = list(graph.out_edges(node, data=True))

            if not out_edges:
                continue

            # 按权重排序
            out_edges_sorted = sorted(out_edges, key=lambda x: x[2].get('weight', 0), reverse=True)

            # 只保留前K个
            for source, target, data in out_edges_sorted[:keep_top_k]:
                nodes_to_keep.add(source)
                nodes_to_keep.add(target)

        # 创建子图
        subgraph = graph.subgraph(nodes_to_keep).copy()

        print(f"  优化后节点数: {subgraph.number_of_nodes()}")
        print(f"  优化后边数: {subgraph.number_of_edges()}")

        return subgraph

    def save_cache(
        self,
        nodes: Dict,
        edges: List[Dict],
        graph: nx.DiGraph,
        cache_prefix: str = "primekg_filtered"
    ):
        """
        保存到缓存

        Args:
            nodes: 节点字典
            edges: 边列表
            graph: NetworkX图
            cache_prefix: 缓存文件前缀
        """
        print(f"\n[PrimeKG] 保存缓存...")

        # 保存节点
        nodes_file = self.cache_dir / f"{cache_prefix}_nodes.json"
        with open(nodes_file, 'w', encoding='utf-8') as f:
            json.dump(nodes, f, ensure_ascii=False, indent=2)
        print(f"  节点: {nodes_file}")

        # 保存边
        edges_file = self.cache_dir / f"{cache_prefix}_edges.json"
        with open(edges_file, 'w', encoding='utf-8') as f:
            json.dump(edges, f, ensure_ascii=False, indent=2)
        print(f"  边: {edges_file}")

        # 保存图
        graph_file = self.cache_dir / f"{cache_prefix}_graph.gml"
        nx.write_gml(graph, str(graph_file))
        print(f"  图: {graph_file}")

        print(f"  ✓ 缓存已保存")

    def load_cache(
        self,
        cache_prefix: str = "primekg_filtered"
    ) -> Tuple[Dict, List[Dict], nx.DiGraph]:
        """
        从缓存加载

        Args:
            cache_prefix: 缓存文件前缀

        Returns:
            (节点字典, 边列表, NetworkX图)
        """
        print(f"\n[PrimeKG] 加载缓存...")

        # 加载节点
        nodes_file = self.cache_dir / f"{cache_prefix}_nodes.json"
        with open(nodes_file, 'r', encoding='utf-8') as f:
            nodes = json.load(f)
        print(f"  节点: {len(nodes)}")

        # 加载边
        edges_file = self.cache_dir / f"{cache_prefix}_edges.json"
        with open(edges_file, 'r', encoding='utf-8') as f:
            edges = json.load(f)
        print(f"  边: {len(edges)}")

        # 加载图
        graph_file = self.cache_dir / f"{cache_prefix}_graph.gml"
        graph = nx.read_gml(str(graph_file))
        print(f"  图节点: {graph.number_of_nodes()}")
        print(f"  图边: {graph.number_of_edges()}")

        print(f"  ✓ 缓存已加载")

        return nodes, edges, graph

    def load(
        self,
        version: str = "v2",
        focus_types: Optional[List[str]] = None,
        min_weight: float = 0.1,
        keep_top_k: int = 10,
        force_download: bool = False,
        use_cache: bool = True
    ) -> Tuple[Dict, List[Dict], nx.DiGraph]:
        """
        完整加载流程

        Args:
            version: PrimeKG 版本（保留参数，实际使用统一数据）
            focus_types: 重点关注节点类型
            min_weight: 最小权重阈值
            keep_top_k: 每个节点保留的前K个邻居
            force_download: 强制重新下载
            use_cache: 使用缓存

        Returns:
            (节点字典, 边列表, NetworkX图)
        """
        # 检查缓存
        cache_prefix = "primekg_filtered"
        cache_files_exist = all([
            (self.cache_dir / f"{cache_prefix}_nodes.json").exists(),
            (self.cache_dir / f"{cache_prefix}_edges.json").exists(),
            (self.cache_dir / f"{cache_prefix}_graph.gml").exists()
        ])

        if use_cache and cache_files_exist and not force_download:
            print(f"[PrimeKG] 发现缓存，直接加载...")
            return self.load_cache(cache_prefix)

        # 下载
        csv_file = self.download_primekg(version=version, force=force_download)

        # 解析
        nodes, edges = self.parse_primekg_csv(csv_file)

        # 过滤
        filtered_nodes, filtered_edges = self.filter_medical_subgraph(
            nodes, edges, focus_types=focus_types
        )

        # 构建图
        graph = self.build_graph(filtered_nodes, filtered_edges, min_weight=min_weight)

        # 优化
        graph_optimized = self.optimize_for_random_walk(graph, keep_top_k=keep_top_k)

        # 保存缓存
        self.save_cache(filtered_nodes, filtered_edges, graph_optimized, cache_prefix)

        return filtered_nodes, filtered_edges, graph_optimized


class RealMedicalKnowledgeGraph:
    """基于PrimeKG的真实医疗知识图谱"""

    def __init__(self, primekg_loader: Optional[PrimeKGLoader] = None):
        """
        初始化真实医疗知识图谱

        Args:
            primekg_loader: PrimeKG加载器（可选）
        """
        self.loader = primekg_loader or PrimeKGLoader()

        # 图结构
        self.graph = nx.DiGraph()
        self.nodes = {}
        self.edges = []

        # 索引
        self.nodes_by_type = defaultdict(set)
        self.edges_by_type = defaultdict(set)

    def load_from_primekg(
        self,
        version: str = "v2",
        focus_types: Optional[List[str]] = None,
        min_weight: float = 0.1,
        keep_top_k: int = 10,
        use_cache: bool = True
    ):
        """
        从PrimeKG加载

        Args:
            version: PrimeKG 版本
            focus_types: 重点关注节点类型
            min_weight: 最小权重
            keep_top_k: 保留前K个邻居
            use_cache: 使用缓存
        """
        print("\n" + "="*60)
        print(" 从PrimeKG加载真实医疗知识图谱")
        print("="*60)

        # 使用加载器
        nodes, edges, graph = self.loader.load(
            version=version,
            focus_types=focus_types,
            min_weight=min_weight,
            keep_top_k=keep_top_k,
            force_download=False,
            use_cache=use_cache
        )

        # 保存到实例
        self.nodes = nodes
        self.edges = edges
        self.graph = graph

        # 构建索引
        self._build_indexes()

        print(f"\n[RealKG] 加载完成")
        self.print_statistics()

    def _build_indexes(self):
        """构建索引"""
        # 节点类型索引
        for node_id, node_info in self.nodes.items():
            node_type = node_info["type"]
            self.nodes_by_type[node_type].add(node_id)

        # 边类型索引
        for edge in self.edges:
            edge_type = edge["edge_type"]
            self.edges_by_type[edge_type].add((edge["source"], edge["target"]))

    def print_statistics(self):
        """打印统计信息"""
        print(f"\n统计信息:")
        print(f"  总节点数: {len(self.nodes)}")
        print(f"  总边数: {len(self.edges)}")

        print(f"\n节点类型分布:")
        for node_type, node_ids in sorted(self.nodes_by_type.items(), key=lambda x: -len(x[1]))[:15]:
            print(f"  {node_type}: {len(node_ids)}")

        print(f"\n边类型分布:")
        for edge_type, edge_pairs in sorted(self.edges_by_type.items(), key=lambda x: -len(x[1]))[:15]:
            print(f"  {edge_type}: {len(edge_pairs)}")

        # 图统计
        if self.graph.number_of_nodes() > 0:
            print(f"\n图结构:")
            print(f"  节点数: {self.graph.number_of_nodes()}")
            print(f"  边数: {self.graph.number_of_edges()}")
            print(f"  密度: {nx.density(self.graph):.4f}")

            # 连通性
            if nx.is_weakly_connected(self.graph):
                print(f"  连通性: 弱连通")
            else:
                components = list(nx.weakly_connected_components(self.graph))
                print(f"  连通性: {len(components)} 个弱连通分量")

    def get_neighbors(
        self,
        node: str,
        edge_type: Optional[str] = None,
        direction: str = "out"
    ) -> List[Tuple[str, float]]:
        """
        获取邻居节点

        Args:
            node: 节点ID
            edge_type: 边类型过滤
            direction: 方向 ("out", "in", "both")

        Returns:
            [(邻居节点ID, 权重), ...]
        """
        if node not in self.graph:
            return []

        neighbors = []

        if direction in ["out", "both"]:
            for neighbor in self.graph.successors(node):
                edge_data = self.graph.get_edge_data(node, neighbor)
                if edge_type is None or edge_data.get("edge_type") == edge_type:
                    weight = edge_data.get("weight", 0.5)
                    neighbors.append((neighbor, weight))

        if direction in ["in", "both"]:
            for neighbor in self.graph.predecessors(node):
                edge_data = self.graph.get_edge_data(neighbor, node)
                if edge_type is None or edge_data.get("edge_type") == edge_type:
                    weight = edge_data.get("weight", 0.5)
                    neighbors.append((neighbor, weight))

        return neighbors

    def get_node_info(self, node_id: str) -> Optional[Dict]:
        """获取节点信息"""
        return self.nodes.get(node_id)

    def search_nodes(
        self,
        keyword: str,
        node_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        搜索节点

        Args:
            keyword: 关键词
            node_type: 节点类型过滤
            limit: 返回数量限制

        Returns:
            匹配的节点列表
        """
        keyword_lower = keyword.lower()
        matches = []

        for node_id, node_info in self.nodes.items():
            # 类型过滤
            if node_type and node_type.lower() not in node_info["type"].lower():
                continue

            # 关键词匹配
            if keyword_lower in node_info["name"].lower():
                matches.append(node_info)

                if len(matches) >= limit:
                    break

        return matches

    def export_for_walk(
        self,
        output_file: str,
        max_nodes: int = 10000
    ):
        """
        导出为Random Walk格式

        Args:
            output_file: 输出文件路径
            max_nodes: 最大节点数
        """
        print(f"\n[RealKG] 导出Random Walk格式...")

        # 选择主要节点
        selected_nodes = set()

        # 优先级：疾病 > 药物 > 症状
        priority_types = ["disease", "drug/drug", "symptom"]

        for node_type in priority_types:
            nodes_of_type = list(self.nodes_by_type.get(node_type, set()))[:max_nodes//len(priority_types)]
            selected_nodes.update(nodes_of_type)

        # 导出
        output_data = {
            "nodes": {
                node_id: self.nodes[node_id]
                for node_id in selected_nodes
            },
            "edges": [
                edge for edge in self.edges
                if edge["source"] in selected_nodes and edge["target"] in selected_nodes
            ]
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"  ✓ 已导出到: {output_file}")
        print(f"  节点数: {len(output_data['nodes'])}")
        print(f"  边数: {len(output_data['edges'])}")


# ========================================
# 使用示例
# ========================================

def demo_load_primekg():
    """演示：加载PrimeKG"""
    print("\n" + "="*60)
    print(" 演示：加载真实的PrimeKG")
    print("="*60)

    # 创建加载器
    loader = PrimeKGLoader()

    # 加载（使用缓存如果存在）
    try:
        nodes, edges, graph = loader.load(
            version="v2",
            focus_types=["disease", "drug/drug", "symptom"],
            min_weight=0.2,
            keep_top_k=5,
            use_cache=True
        )

        print("\n✓ PrimeKG 加载成功")

        # 创建真实知识图谱
        real_kg = RealMedicalKnowledgeGraph(loader)
        real_kg.nodes = nodes
        real_kg.edges = edges
        real_kg.graph = graph
        real_kg._build_indexes()

        # 打印统计
        real_kg.print_statistics()

        # 搜索示例
        print("\n搜索示例:")
        results = real_kg.search_nodes("diabetes", node_type="disease", limit=5)
        for result in results:
            print(f"  - {result['name']} ({result['type']})")

        # 邻居示例
        if results:
            node_id = results[0]["id"]
            neighbors = real_kg.get_neighbors(node_id, direction="out")
            print(f"\n'{results[0]['name']}' 的邻居 (前5个):")
            for neighbor_id, weight in neighbors[:5]:
                neighbor_info = real_kg.get_node_info(neighbor_id)
                print(f"  - {neighbor_info['name']} (权重: {weight:.2f})")

        return real_kg

    except Exception as e:
        print(f"\n✗ 加载失败: {e}")
        print("\n提示：")
        print("1. 首次运行需要下载PrimeKG数据（约200MB），请耐心等待")
        print("2. 如果下载失败，请检查网络连接")
        print("3. 数据会缓存到本地，后续运行会很快")

        return None


if __name__ == "__main__":
    import sys
    import io

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 运行演示
    demo_load_primekg()
