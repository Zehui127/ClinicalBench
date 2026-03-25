#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱任务生成器 - 从PrimeKG生成医学对话任务
KG Task Generator - Generate Medical Dialogue Tasks from PrimeKG

整合版本：包含PrimeKGRandomWalkPipeline的功能
"""

import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# 导入random_walk模块
try:
    from .random_walk import PrimeKGRandomWalkPipeline, ConsultationTask
except ImportError:
    # 如果无法导入，说明random_walk.py还需要原始导入
    import primekg_random_walk
    PrimeKGRandomWalkPipeline = primekg_random_walk.PrimeKGRandomWalkPipeline
    ConsultationTask = primekg_random_walk.ConsultationTask


class KGTaskGenerator:
    """
    知识图谱任务生成器
    Knowledge Graph Task Generator

    整合了PrimeKG加载、Random Walk生成和任务转换功能
    """

    def __init__(self, use_cache: bool = True, cache_dir: str = None):
        """
        初始化KG任务生成器

        Args:
            use_cache: 是否使用缓存
            cache_dir: 缓存目录路径
        """
        self.use_cache = use_cache
        self.cache_dir = cache_dir or "data/primekg_cache"

        # 初始化Random Walk Pipeline
        try:
            self.pipeline = PrimeKGRandomWalkPipeline(use_cache=use_cache)
            print(f"      Pipeline初始化成功")
        except Exception as e:
            print(f"      Pipeline初始化失败: {e}")
            raise

    def generate(
        self,
        symptom_keyword: str,
        walk_type: str = "medium",
        max_attempts: int = 10
    ) -> Optional[ConsultationTask]:
        """
        生成单个任务

        Args:
            symptom_keyword: 症状关键词
            walk_type: 路径类型 (short/medium/long)
            max_attempts: 最大尝试次数

        Returns:
            ConsultationTask对象，失败返回None
        """
        for attempt in range(max_attempts):
            try:
                # 搜索症状节点
                results = self.pipeline.real_kg.search_nodes(
                    symptom_keyword,
                    node_type="effect/phenotype",
                    limit=1
                )

                if not results:
                    # 尝试直接使用关键词
                    symptom_name = symptom_keyword
                else:
                    symptom_name = results[0]['name']

                # 生成任务
                task = self.pipeline.generate_consultation_task(
                    symptom_keyword=symptom_name,
                    walk_type=walk_type
                )

                return task

            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                continue

        return None

    def batch_generate(
        self,
        symptom_keywords: List[str],
        walk_type: str = "medium"
    ) -> List[ConsultationTask]:
        """
        批量生成任务

        Args:
            symptom_keywords: 症状关键词列表
            walk_type: 路径类型

        Returns:
            任务列表
        """
        tasks = []

        for keyword in symptom_keywords:
            try:
                task = self.generate(keyword, walk_type)
                tasks.append(task)
            except Exception as e:
                print(f"Skip {keyword}: {str(e)[:50]}")
                continue

        return tasks

    def export_to_tau2(self, task: ConsultationTask, output_file: str) -> None:
        """
        导出任务为tau2格式

        Args:
            task: ConsultationTask对象
            output_file: 输出文件路径
        """
        # 使用pipeline的导出功能
        self.pipeline.export_to_tau2(task, output_file)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识图谱统计信息

        Returns:
            统计信息字典
        """
        stats = {
            'cache_enabled': self.use_cache,
            'cache_dir': self.cache_dir
        }

        if hasattr(self.pipeline, 'real_kg'):
            kg = self.pipeline.real_kg
            stats['node_count'] = len(kg.nodes) if hasattr(kg, 'nodes') else 0
            stats['edge_count'] = len(kg.edges) if hasattr(kg, 'edges') else 0

        return stats


# 为了向后兼容，也保留原来的函数
def main():
    """测试函数"""
    print("=" * 70)
    print(" KG Task Generator - Test")
    print("=" * 70)

    try:
        generator = KGTaskGenerator(use_cache=True)

        # 测试生成单个任务
        print("\n[1/2] 测试生成单个任务...")
        task = generator.generate("头痛", walk_type="short")
        if task:
            print(f"  [OK] 成功生成任务: {task.task_id}")
            print(f"       患者: {task.patient_profile['age']}岁 {task.patient_profile['gender']}")
            print(f"       主诉: {task.patient_profile['chief_complaint']}")

        # 导出测试
        print("\n[2/2] 测试导出tau2格式...")
        output_file = "data/primekg_tasks/test_output.json"
        generator.export_to_tau2(task, output_file)
        print(f"  [OK] 导出成功: {output_file}")

        # 统计信息
        stats = generator.get_statistics()
        print(f"\n知识图谱统计:")
        print(f"  节点数: {stats.get('node_count', 'N/A')}")
        print(f"  边数: {stats.get('edge_count', 'N/A')}")

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
