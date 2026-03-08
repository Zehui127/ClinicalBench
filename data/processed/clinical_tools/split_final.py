# 极简版标准化Task拆分脚本
import json
import random
import os

# 基础配置（固定不变）
SEED = 42
TARGET_COUNT = 100  # 每个类别目标100个task
INPUT_TASKS = "tasks_filtered.json"  # 过滤后的高质量task
INPUT_SCORES = "review_scores.json"   # 评分文件

# 科室关键词（简单匹配）
DEPARTMENTS = {
    "nephrology": ["CKD", "eGFR", "肾", "尿蛋白", "肾功能"],
    "cardiology": ["高血压", "心梗", "心电图", "心", "troponin"],
    "gastro": ["胃溃疡", "消化", "腹痛", "胃", "peptic ulcer"]
}

# 难度规则（按工具数量）
DIFFICULTIES = {
    "easy": (1, 3),    # 简单：1-3个工具
    "moderate": (4, 6),# 中等：4-6个工具
    "hard": (7, 8)     # 复杂：7-8个工具
}

# 初始化随机种子（结果可复现）
random.seed(SEED)

# -------------------------- 核心逻辑开始 --------------------------
print("="*50)
print("开始拆分标准化Task（无错版）")
print("="*50)

# 1. 加载输入文件（必选）
try:
    with open(INPUT_TASKS, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    with open(INPUT_SCORES, 'r', encoding='utf-8') as f:
        scores = json.load(f)
    print(f"✅ 成功加载文件：{len(tasks)}个过滤后task")
except FileNotFoundError as e:
    print(f"❌ 错误：缺少文件 {e.filename}，请先运行data_quality_filter.py")
    input("\n按任意键退出...")
    exit(1)

# 2. 按科室+难度拆分
print("\n🔧 开始拆分（科室+难度）...")
total_generated = 0
for dept_name, dept_keys in DEPARTMENTS.items():
    for diff_name, (min_tool, max_tool) in DIFFICULTIES.items():
        # 筛选符合条件的task
        filtered_tasks = []
        for task in tasks:
            # 匹配科室关键词
            task_text = str(task).lower()
            if any(key.lower() in task_text for key in dept_keys):
                # 匹配工具数量
                tool_count = len(task.get("tool_call_requirements", []))
                if min_tool <= tool_count <= max_tool:
                    filtered_tasks.append(task)
        
        # 抽样（不足100个则取全部）
        sample_count = min(TARGET_COUNT, len(filtered_tasks))
        sampled_tasks = random.sample(filtered_tasks, sample_count) if sample_count > 0 else []
        
        # 保存文件
        output_file = f"tasks_{dept_name}_{diff_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sampled_tasks, f, ensure_ascii=False, indent=2)
        
        # 打印结果
        print(f"✅ {output_file} | 生成{len(sampled_tasks)}个task（目标{TARGET_COUNT}个）")
        total_generated += len(sampled_tasks)

# 3. 完成提示
print("\n="*50)
print(f"🎉 拆分完成！总共生成{total_generated}个task")
print(f"📁 所有文件已保存到：{os.getcwd()}")
print("⚠️  数量不足是因为原始数据少，补充数据后可生成各100个")
print("="*50)

# 窗口停留（关键：不会闪现）
input("\n按任意键关闭窗口...")