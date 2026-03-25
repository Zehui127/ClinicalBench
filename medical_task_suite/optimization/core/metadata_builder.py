"""
元数据构建器 - 为任务添加完整的转换元数据
Metadata Builder - Add Complete Conversion Metadata to Tasks

功能：
1. 构建完整的转换元数据
2. 记录优化过程和细节
3. 添加质量评分
4. 确保可追溯性
"""

from typing import Dict, List, Any
from datetime import datetime


class MetadataBuilder:
    """元数据构建器 - 构建转换元数据"""

    def __init__(self, config: Dict[str, Any] = None):
        """初始化元数据构建器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.converter_version = "2.0"
        self.base_dataset = "Chinese MedDialog"

    def build_conversion_metadata(self, task: Dict[str, Any],
                                 task_index: int,
                                 optimizations: List[str] = None) -> Dict[str, Any]:
        """构建转换元数据

        Args:
            task: 任务字典
            task_index: 任务索引
            optimizations: 应用的优化列表

        Returns:
            转换元数据字典
        """
        if optimizations is None:
            optimizations = []

        metadata = {
            'converted_from': 'realistic_v3',
            'converter_version': self.converter_version,
            'conversion_index': task_index,
            'optimizations_applied': optimizations,
            'base_dataset': self.base_dataset,
            'optimization_timestamp': datetime.now().isoformat()
        }

        return metadata

    def add_quality_score(self, task: Dict[str, Any],
                         quality_score: float) -> Dict[str, Any]:
        """添加质量评分到元数据

        Args:
            task: 任务字典
            quality_score: 质量评分

        Returns:
            更新后的元数据字典
        """
        if 'conversion_metadata' not in task:
            task['conversion_metadata'] = {}

        task['conversion_metadata']['quality_score'] = quality_score

        # 添加质量等级
        if quality_score >= 9.0:
            task['conversion_metadata']['quality_level'] = 'excellent'
        elif quality_score >= 7.5:
            task['conversion_metadata']['quality_level'] = 'good'
        elif quality_score >= 6.0:
            task['conversion_metadata']['quality_level'] = 'acceptable'
        else:
            task['conversion_metadata']['quality_level'] = 'poor'

        return task

    def add_optimization_details(self, task: Dict[str, Any],
                                details: Dict[str, Any]) -> Dict[str, Any]:
        """添加优化详情

        Args:
            task: 任务字典
            details: 优化详情字典

        Returns:
            更新后的任务字典
        """
        if 'conversion_metadata' not in task:
            task['conversion_metadata'] = {}

        if 'optimization_details' not in task['conversion_metadata']:
            task['conversion_metadata']['optimization_details'] = {}

        task['conversion_metadata']['optimization_details'].update(details)

        return task

    def enrich_task_metadata(self, task: Dict[str, Any],
                           task_index: int,
                           quality_score: float = None,
                           optimizations: List[str] = None) -> Dict[str, Any]:
        """丰富任务元数据

        Args:
            task: 任务字典
            task_index: 任务索引
            quality_score: 质量评分
            optimizations: 应用的优化列表

        Returns:
            元数据丰富后的任务字典
        """
        enriched_task = task.copy()

        # 添加转换元数据
        if 'conversion_metadata' not in enriched_task:
            enriched_task['conversion_metadata'] = self.build_conversion_metadata(
                task, task_index, optimizations
            )

        # 添加质量评分
        if quality_score is not None:
            enriched_task = self.add_quality_score(enriched_task, quality_score)

        # 确保有original_task_id
        if 'original_task_id' not in enriched_task:
            enriched_task['original_task_id'] = task.get('id', '')

        return enriched_task

    def enrich_tasks_metadata(self, tasks: List[Dict[str, Any]],
                            quality_scores: List[float] = None,
                            optimizations: List[str] = None) -> List[Dict[str, Any]]:
        """批量丰富任务元数据

        Args:
            tasks: 任务列表
            quality_scores: 质量评分列表
            optimizations: 应用的优化列表

        Returns:
            元数据丰富后的任务列表
        """
        enriched_tasks = []

        for i, task in enumerate(tasks):
            quality_score = quality_scores[i] if quality_scores else None
            enriched_task = self.enrich_task_metadata(
                task, i + 1, quality_score, optimizations
            )
            enriched_tasks.append(enriched_task)

        return enriched_tasks

    def get_statistics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取元数据统计信息

        Args:
            tasks: 任务列表

        Returns:
            统计信息字典
        """
        with_metadata = sum(1 for t in tasks if 'conversion_metadata' in t)
        with_quality = sum(1 for t in tasks
                          if t.get('conversion_metadata', {}).get('quality_score'))

        # 统计质量分布
        quality_levels = {}
        for task in tasks:
            level = task.get('conversion_metadata', {}).get('quality_level', 'unknown')
            quality_levels[level] = quality_levels.get(level, 0) + 1

        # 统计优化应用情况
        optimization_counts = {}
        for task in tasks:
            opts = task.get('conversion_metadata', {}).get('optimizations_applied', [])
            for opt in opts:
                optimization_counts[opt] = optimization_counts.get(opt, 0) + 1

        return {
            'total_tasks': len(tasks),
            'with_metadata': with_metadata,
            'with_quality_score': with_quality,
            'metadata_coverage': with_metadata / len(tasks) if tasks else 0,
            'quality_coverage': with_quality / len(tasks) if tasks else 0,
            'quality_levels': quality_levels,
            'optimization_counts': optimization_counts
        }
