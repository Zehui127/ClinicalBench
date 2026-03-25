"""
任务生成器测试
Medical Dialogue Task Generator - Tests
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.task_generator import TaskGenerator
from src.models.data_models import RawDialogueData
from src.utils.validator import TaskValidator


class TestTaskGenerator:
    """任务生成器测试"""

    def setup_method(self):
        """测试前设置"""
        self.generator = TaskGenerator()

    def test_generate_l1_task(self):
        """测试生成L1任务"""
        raw_data = RawDialogueData(
            id="test_001",
            ticket="高血压患者能吃党参吗？",
            known_info="我有高血压这两天女婿来的时候给我拿了些党参泡水喝",
            department_cn="内科",
            source="Test",
            original_title="高血压患者能吃党参吗？"
        )

        task = self.generator.generate(raw_data)

        assert task.id == "test_001"
        assert task.difficulty in ["L1", "L2", "L3"]
        assert task.patient_behavior is not None
        assert task.evaluation_criteria is not None

    def test_generate_batch(self):
        """测试批量生成"""
        raw_data_list = [
            RawDialogueData(
                id=f"test_{i:03d}",
                ticket=f"测试问题{i}",
                known_info=f"测试信息{i}",
                department_cn="内科",
                source="Test",
                original_title=f"测试{i}"
            )
            for i in range(1, 6)
        ]

        tasks = self.generator.generate_batch(raw_data_list)

        assert len(tasks) == 5
        assert all(task.id.startswith("test_") for task in tasks)

    def test_scenario_detection(self):
        """测试场景检测"""
        # 信息查询
        raw_data1 = RawDialogueData(
            id="test_001",
            ticket="高血压患者能吃党参吗？",
            known_info="测试",
            department_cn="内科",
            source="Test",
            original_title="测试"
        )

        task1 = self.generator.generate(raw_data1)
        assert task1.metadata.scenario_type in ["INFORMATION_QUERY", "SYMPTOM_ANALYSIS", "CHRONIC_MANAGEMENT"]

        # 症状分析
        raw_data2 = RawDialogueData(
            id="test_002",
            ticket="头痛是什么原因引起的？",
            known_info="测试",
            department_cn="内科",
            source="Test",
            original_title="头痛原因"
        )

        task2 = self.generator.generate(raw_data2)
        assert task2.metadata.scenario_type in ["INFORMATION_QUERY", "SYMPTOM_ANALYSIS"]


class TestTaskValidator:
    """任务验证器测试"""

    def setup_method(self):
        """测试前设置"""
        self.validator = TaskValidator()
        self.generator = TaskGenerator()

    def test_validate_l1_task(self):
        """测试验证L1任务"""
        raw_data = RawDialogueData(
            id="test_l1",
            ticket="简单问题",
            known_info="简单信息",
            department_cn="内科",
            source="Test",
            original_title="简单"
        )

        # 生成任务（可能是L1/L2/L3）
        task = self.generator.generate(raw_data)

        # 如果是L1任务，验证应该通过
        if task.difficulty == "L1":
            assert self.validator.validate(task) == True

    def test_validate_required_fields(self):
        """测试验证必需字段"""
        raw_data = RawDialogueData(
            id="test_fields",
            ticket="测试字段",
            known_info="测试",
            department_cn="内科",
            source="Test",
            original_title="测试"
        )

        task = self.generator.generate(raw_data)

        # 检查必需字段
        assert hasattr(task, 'id')
        assert hasattr(task, 'description')
        assert hasattr(task, 'user_scenario')
        assert hasattr(task, 'ticket')
        assert hasattr(task, 'initial_state')
        assert hasattr(task, 'evaluation_criteria')
        assert hasattr(task, 'metadata')
        assert hasattr(task, 'difficulty')
        assert hasattr(task, 'patient_behavior')

    def test_validate_scenario_type(self):
        """测试验证场景类型"""
        raw_data = RawDialogueData(
            id="test_scenario",
            ticket="测试场景",
            known_info="测试",
            department_cn="内科",
            source="Test",
            original_title="测试"
        )

        task = self.generator.generate(raw_data)

        # 验证场景类型
        valid_types = {
            "INFORMATION_QUERY", "SYMPTOM_ANALYSIS", "CHRONIC_MANAGEMENT",
            "MEDICATION_CONSULTATION", "LIFESTYLE_ADVICE", "EMERGENCY_CONCERN",
            "FOLLOW_UP", "SECOND_OPINION"
        }

        assert task.metadata.scenario_type in valid_types


class TestDifficultyLevels:
    """难度级别测试"""

    def setup_method(self):
        """测试前设置"""
        self.generator = TaskGenerator()

    def test_l1_characteristics(self):
        """测试L1级别特征"""
        # 简单问题通常生成L1
        raw_data = RawDialogueData(
            id="test_l1",
            ticket="高血压能吃党参吗？",
            known_info="我有高血压",
            department_cn="内科",
            source="Test",
            original_title="高血压能吃党参吗？"
        )

        task = self.generator.generate(raw_data)

        if task.difficulty == "L1":
            assert task.patient_behavior.cooperation == "good"
            assert len(task.patient_behavior.behaviors) == 0

    def test_l2_characteristics(self):
        """测试L2级别特征"""
        # 中等复杂度问题可能生成L2
        raw_data = RawDialogueData(
            id="test_l2",
            ticket="我最近总是头痛，还在吃阿司匹林，这是怎么回事？",
            known_info="我最近头痛，吃阿司匹林",
            department_cn="内科",
            source="Test",
            original_title="头痛咨询"
        )

        task = self.generator.generate(raw_data)

        if task.difficulty == "L2":
            assert task.patient_behavior.cooperation in ["partial", "poor"]
            assert len(task.patient_behavior.behaviors) > 0
            assert "contradicting" not in task.patient_behavior.behaviors

    def test_l3_characteristics(self):
        """测试L3级别特征"""
        # 复杂问题可能生成L3
        raw_data = RawDialogueData(
            id="test_l3",
            ticket="我邻居因为头痛脑出血走了，我很害怕，我最近头痛，但我平时身体健康",
            known_info="我邻居脑出血走了，我很害怕，最近头痛",
            department_cn="内科",
            source="Test",
            original_title="头痛恐惧"
        )

        task = self.generator.generate(raw_data)

        if task.difficulty == "L3":
            assert task.patient_behavior.cooperation == "poor"
            assert len(task.patient_behavior.behaviors) >= 3
            assert "emotional" in task.patient_behavior.behaviors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
