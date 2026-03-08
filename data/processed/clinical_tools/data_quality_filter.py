# 兼容版数据质量过滤脚本（支持字典/列表格式）
import json
import os
import datetime

# 配置项
RAW_TASKS_FILE = "tasks_raw.json"
FILTERED_TASKS_FILE = "tasks_filtered.json"
REVIEW_SCORES_FILE = "review_scores.json"
MIN_QUALITY_SCORE = 3.5

# 全局停留函数（确保无论是否报错都停留）
def pause_window():
    input("\n====================\n按任意键退出...\n====================")

print("="*50)
print("开始过滤高质量临床Task")
print("="*50)

try:
    # 1. 检查原始文件
    if not os.path.exists(RAW_TASKS_FILE):
        print(f"❌ 错误：未找到 {RAW_TASKS_FILE}")
        print("⚠️  请确认文件在当前目录：", os.getcwd())
        pause_window()  # 报错时停留
        exit(1)

    # 2. 加载原始task（兼容字典/列表格式）
    with open(RAW_TASKS_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # 核心修改：统一转为列表格式
    if isinstance(raw_data, dict):
        # 情况1：字典格式（需确认字典中存储task列表的key，常见为"tasks"/"data"）
        # 先尝试常见key，若没有则把整个字典作为单个task
        raw_tasks = raw_data.get("tasks", raw_data.get("data", [raw_data]))
        print(f"⚠️  检测到JSON为字典格式，已自动转换为列表（共{len(raw_tasks)}个task）")
    elif isinstance(raw_data, list):
        # 情况2：列表格式（原逻辑不变）
        raw_tasks = raw_data
    else:
        # 情况3：既不是字典也不是列表（转为空列表）
        print(f"❌ 错误：JSON内容类型为{type(raw_data).__name__}，无法解析为task列表")
        pause_window()
        exit(1)
    
    print(f"✅ 加载原始文件：{len(raw_tasks)}个task")

    # 3. 质量过滤（原逻辑不变，仅保留鲁棒性）
    review_scores = []
    filtered_tasks = []
    for idx, task in enumerate(raw_tasks):
        # 跳过非字典的task项
        if not isinstance(task, dict):
            print(f"⚠️  第{idx+1}个task不是字典格式，已跳过")
            continue
        
        task_id = task.get("task_id", f"task_{idx+1}")
        tool_count = len(task.get("tool_call_requirements", []))
        content_length = len(str(task.get("clinical_scenario", "")))
        quality_score = min(5.0, (tool_count * 0.6) + (content_length / 50))
        pass_filter = quality_score >= MIN_QUALITY_SCORE

        review_scores.append({
            "task_id": task_id,
            "quality_score": round(quality_score, 2),
            "tool_count": tool_count,
            "pass_filter": pass_filter,
            "difficulty_level": "easy" if quality_score < 2 else "moderate" if quality_score < 4 else "hard"
        })
        if pass_filter:
            filtered_tasks.append(task)

    # 4. 保存文件
    with open(FILTERED_TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered_tasks, f, ensure_ascii=False, indent=2)
    with open(REVIEW_SCORES_FILE, 'w', encoding='utf-8') as f:
        json.dump(review_scores, f, ensure_ascii=False, indent=2)

    # 5. 输出结果
    print(f"\n🔧 过滤完成：")
    print(f"   - 原始数量：{len(raw_tasks)}")
    print(f"   - 高质量数量：{len(filtered_tasks)}")
    print(f"   - 通过率：{round(len(filtered_tasks)/len(raw_tasks)*100, 1)}%")
    print(f"\n✅ 生成文件：")
    print(f"   - {FILTERED_TASKS_FILE}")
    print(f"   - {REVIEW_SCORES_FILE}")

except Exception as e:
    # 捕获所有报错，显示并停留
    print(f"❌ 运行出错：{str(e)}")
    pause_window()
    exit(1)

# 正常执行完也停留
print("\n="*50)
print("🎉 过滤脚本执行完成！")
pause_window()