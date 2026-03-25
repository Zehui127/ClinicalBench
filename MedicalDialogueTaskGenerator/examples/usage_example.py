#!/usr/bin/env python3
"""
医学对话任务生成器使用示例
Medical Dialogue Task Generator - Usage Examples
"""

import json
from pathlib import Path
from typing import List, Dict, Any

# 示例1: 基础使用
def example_basic_usage():
    """基础使用示例：生成单个任务"""
    print("=" * 60)
    print("示例1: 基础使用 - 生成单个任务")
    print("=" * 60)

    from src.core.task_generator import TaskGenerator
    from src.models.data_models import RawDialogueData

    # 初始化生成器
    generator = TaskGenerator(config_path="config/")

    # 准备输入数据
    raw_data = RawDialogueData(
        id="dialogue_001",
        ticket="高血压患者能吃党参吗？",
        known_info="我有高血压这两天女婿来的时候给我拿了些党参泡水喝，您好高血压可以吃党参吗？",
        department_cn="内科",
        source="Chinese MedDialog",
        original_title="高血压患者能吃党参吗？"
    )

    # 生成任务
    task = generator.generate(raw_data)

    # 打印结果
    print(f"任务ID: {task.id}")
    print(f"难度级别: {task.difficulty}")
    print(f"患者配合度: {task.patient_behavior.cooperation}")
    print(f"场景类型: {task.metadata.get('scenario_type')}")

    # 保存结果
    output_path = Path("examples/output/sample_task.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"\n任务已保存到: {output_path}")


# 示例2: 批量生成
def example_batch_generation():
    """批量生成示例：处理多个原始对话"""
    print("\n" + "=" * 60)
    print("示例2: 批量生成 - 处理多个原始对话")
    print("=" * 60)

    from src.core.task_generator import TaskGenerator
    from src.models.data_models import RawDialogueData

    # 模拟批量数据
    raw_data_list = [
        {
            "id": "dialogue_001",
            "ticket": "高血压患者能吃党参吗？",
            "known_info": "我有高血压这两天女婿来的时候给我拿了些党参泡水喝，您好高血压可以吃党参吗？",
            "department_cn": "内科",
            "source": "Chinese MedDialog",
            "original_title": "高血压患者能吃党参吗？"
        },
        {
            "id": "dialogue_002",
            "ticket": "糖尿病还会进行遗传吗？",
            "known_info": "糖尿病有隔代遗传吗？我妈是糖尿病，很多年了，也没养好，我现在也是，我妹子也是",
            "department_cn": "内科",
            "source": "Chinese MedDialog",
            "original_title": "糖尿病还会进行遗传吗？"
        },
        {
            "id": "dialogue_003",
            "ticket": "高血压心速过缓是怎么回事？",
            "known_info": "从年轻时就爱喝啤酒，每天嗜酒如命，无酒不欢，但是致使了我高血压心脏病等一连串病症",
            "department_cn": "内科",
            "source": "Chinese MedDialog",
            "original_title": "高血压心速过缓是怎么回事？"
        }
    ]

    # 初始化生成器
    generator = TaskGenerator()

    # 批量生成
    tasks = []
    for raw_item in raw_data_list:
        try:
            raw_data = RawDialogueData(**raw_item)
            task = generator.generate(raw_data)
            tasks.append(task.to_dict())
            print(f"✓ 成功生成任务: {task.id} (难度: {task.difficulty})")
        except Exception as e:
            print(f"✗ 生成失败: {raw_item.get('id')}, 错误: {e}")

    # 保存结果
    output_path = Path("examples/output/batch_tasks.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f"\n共生成 {len(tasks)} 个任务")
    print(f"任务已保存到: {output_path}")

    # 统计难度分布
    difficulty_dist = {}
    for task in tasks:
        diff = task.get("difficulty")
        difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1

    print("\n难度分布:")
    for diff, count in sorted(difficulty_dist.items()):
        print(f"  {diff}: {count} ({count/len(tasks)*100:.1f}%)")


# 示例3: 自定义配置
def example_custom_config():
    """自定义配置示例：调整难度分布"""
    print("\n" + "=" * 60)
    print("示例3: 自定义配置 - 调整难度分布")
    print("=" * 60)

    from src.core.task_generator import TaskGenerator
    from src.models.data_models import RawDialogueData

    # 使用自定义配置
    generator = TaskGenerator(config_path="config/custom_config.yaml")

    # 生成任务
    raw_data = RawDialogueData(
        id="dialogue_custom",
        ticket="我最近总是头痛，是怎么回事？",
        known_info="我最近总是头痛，特别是下午，有时候还会恶心",
        department_cn="内科",
        source="Custom Source",
        original_title="头痛咨询"
    )

    task = generator.generate(raw_data)
    print(f"任务ID: {task.id}")
    print(f"难度级别: {task.difficulty}")
    print(f"场景类型: {task.metadata.get('scenario_type')}")


# 示例4: 验证任务
def example_validate_tasks():
    """任务验证示例：验证生成的任务"""
    print("\n" + "=" * 60)
    print("示例4: 任务验证 - 验证生成的任务")
    print("=" * 60)

    from src.utils.validator import TaskValidator

    # 加载生成的任务
    tasks_path = Path("examples/output/batch_tasks.json")
    if not tasks_path.exists():
        print("请先运行批量生成示例")
        return

    with open(tasks_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    # 验证任务
    validator = TaskValidator()
    valid_count = 0
    invalid_count = 0

    for task_dict in tasks:
        from src.models.data_models import MedicalDialogueTask
        task = MedicalDialogueTask.from_dict(task_dict)

        if validator.validate(task):
            valid_count += 1
        else:
            invalid_count += 1
            errors = validator.get_errors(task)
            print(f"✗ 任务验证失败: {task.id}")
            for error in errors:
                print(f"  - {error}")

    print(f"\n验证结果:")
    print(f"  有效任务: {valid_count}")
    print(f"  无效任务: {invalid_count}")
    print(f"  通过率: {valid_count/(valid_count+invalid_count)*100:.1f}%")


# 示例5: 统计分析
def example_statistics():
    """统计分析示例：分析任务分布"""
    print("\n" + "=" * 60)
    print("示例5: 统计分析 - 分析任务分布")
    print("=" * 60)

    from pathlib import Path
    import json
    from collections import Counter

    # 加载任务
    tasks_path = Path("examples/output/batch_tasks.json")
    if not tasks_path.exists():
        print("请先运行批量生成示例")
        return

    with open(tasks_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    # 统计分析
    print(f"总任务数: {len(tasks)}")

    # 难度分布
    difficulty_dist = Counter(t.get("difficulty") for t in tasks)
    print("\n难度分布:")
    for diff, count in difficulty_dist.most_common():
        print(f"  {diff}: {count} ({count/len(tasks)*100:.1f}%)")

    # 场景类型分布
    scenario_dist = Counter(t.get("metadata", {}).get("scenario_type") for t in tasks)
    print("\n场景类型分布:")
    for scenario, count in scenario_dist.most_common():
        print(f"  {scenario}: {count} ({count/len(tasks)*100:.1f}%)")

    # 患者行为分布
    behavior_counts = Counter()
    for task in tasks:
        behaviors = task.get("patient_behavior", {}).get("behaviors", [])
        for behavior in behaviors:
            behavior_counts[behavior] += 1

    print("\n患者行为分布:")
    for behavior, count in behavior_counts.most_common():
        print(f"  {behavior}: {count}")


# 示例6: 从真实数据生成
def example_from_real_data():
    """从真实数据生成示例"""
    print("\n" + "=" * 60)
    print("示例6: 从真实数据生成 - 从MedDialog数据生成任务")
    print("=" * 60)

    from src.core.task_generator import TaskGenerator
    from src.models.data_models import RawDialogueData

    # 假设从Chinese MedDialog数据集加载
    # 这里使用示例数据
    medialog_sample = {
        "id": "medialog_001",
        "ticket": "医生，我最近总是感觉头晕，特别是站起来的时候",
        "known_info": "我最近总是感觉头晕，特别是站起来的时候，有时候还会眼前发黑",
        "department_cn": "内科",
        "source": "Chinese MedDialog Dataset",
        "original_title": "头晕咨询"
    }

    generator = TaskGenerator()
    raw_data = RawDialogueData(**medialog_sample)
    task = generator.generate(raw_data)

    print(f"生成的任务:")
    print(f"  ID: {task.id}")
    print(f"  难度: {task.difficulty}")
    print(f"  场景: {task.metadata.get('scenario_name')}")
    print(f"  配合度: {task.patient_behavior.cooperation}")

    # 打印完整的inquiry_requirements
    inquiry_req = task.metadata.get("inquiry_requirements", {})
    if inquiry_req:
        print(f"\n问诊要求:")
        for category, items in inquiry_req.items():
            print(f"  {category}:")
            for key, value in items.items():
                print(f"    {key}: {value.get('question', '')}")


# 主函数
def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("医学对话任务生成器使用示例")
    print("Medical Dialogue Task Generator - Usage Examples")
    print("=" * 60)

    # 运行示例
    example_basic_usage()
    example_batch_generation()
    # example_custom_config()  # 需要自定义配置文件
    example_validate_tasks()
    example_statistics()
    example_from_real_data()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
