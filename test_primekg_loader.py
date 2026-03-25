#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实的 PrimeKG 加载器

测试流程：
1. 下载 PrimeKG 数据
2. 解析 CSV 文件
3. 过滤医疗子图
4. 构建图结构
5. 优化 Random Walk 性能
6. 验证功能

作者：Claude Sonnet 4.5
日期：2025-03-21
"""

import sys
import io
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from primekg_loader import (
    PrimeKGLoader,
    RealMedicalKnowledgeGraph
)


def test_download_primekg():
    """测试1：下载PrimeKG"""
    print("\n" + "="*60)
    print(" [测试 1/6] 下载 PrimeKG")
    print("="*60)

    loader = PrimeKGLoader()

    try:
        # 下载v2版本（最新的）
        csv_file = loader.download_primekg(version="v2", force=False)

        print(f"\n✓ 下载成功")
        print(f"  文件大小: {csv_file.stat().size() / 1024 / 1024:.1f} MB")

        return csv_file

    except Exception as e:
        print(f"\n✗ 下载失败: {e}")
        return None


def test_parse_primekg():
    """测试2：解析PrimeKG CSV"""
    print("\n" + "="*60)
    print(" [测试 2/6] 解析 PrimeKG CSV")
    print("="*60)

    loader = PrimeKGLoader()

    # 尝试从缓存加载
    csv_file = loader.cache_dir / "primekg_v2.csv"

    if not csv_file.exists():
        print(f"\n⚠️  CSV文件不存在，需要先下载")
        print(f"  请运行测试1或使用完整加载流程")
        return None, None

    try:
        nodes, edges = loader.parse_primekg_csv(csv_file)

        print(f"\n✓ 解析成功")
        print(f"  节点数: {len(nodes)}")
        print(f"  边数: {len(edges)}")

        return nodes, edges

    except Exception as e:
        print(f"\n✗ 解析失败: {e}")
        return None, None


def test_filter_subgraph(nodes, edges):
    """测试3：过滤医疗子图"""
    print("\n" + "="*60)
    print(" [测试 3/6] 过滤医疗子图")
    print("="*60)

    if nodes is None or edges is None:
        print("\n⚠️  跳过（测试2未通过）")
        return None, None

    loader = PrimeKGLoader()

    try:
        # 过滤出疾病、药物、症状
        filtered_nodes, filtered_edges = loader.filter_medical_subgraph(
            nodes, edges,
            focus_types=["disease", "drug/drug", "symptom", "phenotype"]
        )

        print(f"\n✓ 过滤成功")
        print(f"  原始节点: {len(nodes)}")
        print(f"  过滤节点: {len(filtered_nodes)}")
        print(f"  原始边: {len(edges)}")
        print(f"  过滤边: {len(filtered_edges)}")

        return filtered_nodes, filtered_edges

    except Exception as e:
        print(f"\n✗ 过滤失败: {e}")
        return None, None


def test_build_graph(nodes, edges):
    """测试4：构建图结构"""
    print("\n" + "="*60)
    print(" [测试 4/6] 构建图结构")
    print("="*60)

    if nodes is None or edges is None:
        print("\n⚠️  跳过（测试3未通过）")
        return None

    loader = PrimeKGLoader()

    try:
        graph = loader.build_graph(nodes, edges, min_weight=0.2)

        print(f"\n✓ 图构建成功")
        print(f"  节点数: {graph.number_of_nodes()}")
        print(f"  边数: {graph.number_of_edges()}")
        print(f"  密度: {graph.density():.4f}")

        return graph

    except Exception as e:
        print(f"\n✗ 图构建失败: {e}")
        return None


def test_optimize_graph(graph):
    """测试5：优化图"""
    print("\n" + "="*60)
    print(" [测试 5/6] 优化图结构")
    print("="*60)

    if graph is None:
        print("\n⚠️  跳过（测试4未通过）")
        return None

    loader = PrimeKGLoader()

    try:
        optimized_graph = loader.optimize_for_random_walk(graph, keep_top_k=10)

        print(f"\n✓ 优化成功")
        print(f"  原始节点: {graph.number_of_nodes()}")
        print(f"  优化节点: {optimized_graph.number_of_nodes()}")
        print(f"  原始边: {graph.number_of_edges()}")
        print(f"  优化边: {optimized_graph.number_of_edges()}")

        return optimized_graph

    except Exception as e:
        print(f"\n✗ 优化失败: {e}")
        return None


def test_real_kg_usage():
    """测试6：真实知识图谱使用"""
    print("\n" + "="*60)
    print(" [测试 6/6] 真实知识图谱使用")
    print("="*60)

    try:
        # 创建加载器
        loader = PrimeKGLoader()

        # 完整加载流程
        nodes, edges, graph = loader.load(
            version="v2",
            focus_types=["disease", "drug", "anatomy", "effect/phenotype"],
            min_weight=0.2,
            keep_top_k=10,
            use_cache=True
        )

        # 创建真实知识图谱
        real_kg = RealMedicalKnowledgeGraph(loader)
        real_kg.nodes = nodes
        real_kg.edges = edges
        real_kg.graph = graph
        real_kg._build_indexes()

        print("\n✓ 真实知识图谱创建成功")

        # 打印统计
        real_kg.print_statistics()

        # 测试搜索功能
        print("\n测试搜索功能:")

        # 搜索"hypertension"
        results = real_kg.search_nodes("hypertension", node_type="disease", limit=3)
        print(f"\n搜索 'hypertension':")
        for result in results:
            print(f"  - {result['name']} (ID: {result['id'][:10]}...)")

        # 搜索"diabetes"
        results = real_kg.search_nodes("diabetes", node_type="disease", limit=3)
        print(f"\n搜索 'diabetes':")
        for result in results:
            print(f"  - {result['name']} (ID: {result['id'][:10]}...)")

        # 测试邻居查询
        if results:
            first_disease = results[0]
            print(f"\n测试邻居查询: '{first_disease['name']}'")

            neighbors = real_kg.get_neighbors(
                first_disease["id"],
                edge_type=None,
                direction="out"
            )

            print(f"  出度邻居数: {len(neighbors)}")
            print(f"  前5个邻居:")
            for neighbor_id, weight in neighbors[:5]:
                neighbor_info = real_kg.get_node_info(neighbor_id)
                if neighbor_info:
                    print(f"    - {neighbor_info['name']} ({neighbor_info['type'][:20]}) 权重:{weight:.2f}")

        # 测试边类型查询
        print(f"\n测试边类型统计:")
        for edge_type, edge_pairs in sorted(
            real_kg.edges_by_type.items(),
            key=lambda x: -len(x[1])
        )[:5]:
            print(f"  {edge_type}: {len(edge_pairs)} 条边")

        print("\n✓ 所有功能测试通过")

        return real_kg

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主测试函数"""
    print("="*60)
    print(" PrimeKG 真实加载器测试")
    print("="*60)

    print("\n测试说明:")
    print("  测试1: 下载 PrimeKG 数据（首次运行需要时间）")
    print("  测试2: 解析 CSV 文件")
    print("  测试3: 过滤医疗子图")
    print("  测试4: 构建图结构")
    print("  测试5: 优化图结构")
    print("  测试6: 完整流程和使用")

    print("\n注意事项:")
    print("  - 首次运行需要下载 ~200MB 数据，请耐心等待")
    print("  - 数据会缓存到本地，后续运行很快")
    print("  - 如果下载失败，请检查网络连接")

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 选择测试模式
    print("\n选择测试模式:")
    print("1. 单独测试下载")
    print("2. 单独测试解析")
    print("3. 完整流程测试（推荐）")

    choice = input("\n请选择 (1-3): ").strip()

    try:
        if choice == "1":
            test_download_primekg()

        elif choice == "2":
            nodes, edges = test_parse_primekg()
            if nodes and edges:
                filtered_nodes, filtered_edges = test_filter_subgraph(nodes, edges)
                if filtered_nodes and filtered_edges:
                    graph = test_build_graph(filtered_nodes, filtered_edges)
                    if graph:
                        test_optimize_graph(graph)

        elif choice == "3":
            real_kg = test_real_kg_usage()

            if real_kg:
                print("\n" + "="*60)
                print(" ✓ 真实 PrimeKG 加载成功！")
                print("="*60)
                print("\n下一步:")
                print("  1. 在 medical_kg_dialogue_generator.py 中集成")
                print("  2. 使用真实PrimeKG替换简化版")
                print("  3. 测试Random Walk和Task Generator")

        else:
            print("\n默认运行完整流程...")
            test_real_kg_usage()

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        return 1
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
