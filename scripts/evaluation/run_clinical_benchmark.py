#!/usr/bin/env python3
"""
Tau2-Bench Clinical Domains Evaluation Script

运行所有 5 个临床科室的 tau2-bench 评测：
- Cardiology (心脏科) - 758 tasks
- Endocrinology (内分泌科) - 176 tasks
- Gastroenterology (胃肠科) - 475 tasks
- Nephrology (肾病科) - 300 tasks
- Neurology (神经科) - 741 tasks
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add tau2 to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tau2.run import run_tasks, get_environment_info
from tau2.registry import registry
from tau2.data_model.tasks import Task


# 临床域配置
CLINICAL_DOMAINS = {
    "clinical_cardiology": {
        "name": "Cardiology",
        "name_cn": "心脏科",
        "task_count": 758,
        "description": "心血管疾病、心电图、血压、胸痛"
    },
    "clinical_endocrinology": {
        "name": "Endocrinology",
        "name_cn": "内分泌科",
        "task_count": 176,
        "description": "糖尿病、甲状腺、激素代谢"
    },
    "clinical_gastroenterology": {
        "name": "Gastroenterology",
        "name_cn": "胃肠科",
        "task_count": 475,
        "description": "消化系统、肝脏、内镜检查"
    },
    "clinical_nephrology": {
        "name": "Nephrology",
        "name_cn": "肾病科",
        "task_count": 300,
        "description": "肾脏疾病、CKD 分期、透析"
    },
    "clinical_neurology": {
        "name": "Neurology",
        "name_cn": "神经科",
        "task_count": 741,
        "description": "脑血管、癫痫、头痛、认知障碍"
    }
}


def print_banner():
    """打印横幅"""
    print("=" * 80)
    print(" " * 20 + "TAU2-BENCH CLINICAL EVALUATION")
    print("=" * 80)
    print()


def check_api_key():
    """检查 API 密钥配置"""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    if not api_key or api_key in ["your_openai_api_key_here", "your_anthropic_api_key_here"]:
        print("[ERROR] 错误: 未找到有效的 API 密钥")
        print()
        print("请配置以下环境变量之一：")
        print("  - OPENAI_API_KEY (用于 GPT-4, GPT-3.5)")
        print("  - ANTHROPIC_API_KEY (用于 Claude)")
        print()
        print("配置方法：")
        print("  1. 编辑 .env 文件，填入你的 API 密钥")
        print("  2. 或设置环境变量: export OPENAI_API_KEY=your_key")
        print()
        return False

    print("[OK] API 密钥已配置")
    return True


def list_domains():
    """列出所有可用的临床域"""
    print("可用的临床域：")
    print()

    for domain_id, info in CLINICAL_DOMAINS.items():
        print(f"  {domain_id}")
        print(f"    名称: {info['name_cn']} ({info['name']})")
        print(f"    任务数: {info['task_count']}")
        print(f"    描述: {info['description']}")
        print()

    print(f"总任务数: {sum(info['task_count'] for info in CLINICAL_DOMAINS.values())}")
    print()


def run_evaluation(
    domain: str,
    max_tasks: int = 5,
    max_rounds: int = 3,
    agent_model: str = "gpt-4",
    user_model: str = "gpt-4",
    output_dir: str = "outputs/clinical"
):
    """
    运行单个临床域的评测

    Args:
        domain: 临床域 ID
        max_tasks: 评测的最大任务数
        max_rounds: 每个任务的最大轮数
        agent_model: 代理使用的模型
        user_model: 用户模拟器使用的模型
        output_dir: 输出目录
    """
    print(f"\n{'='*80}")
    print(f"开始评测: {CLINICAL_DOMAINS[domain]['name_cn']} ({domain})")
    print(f"{'='*80}\n")

    # 获取 API 密钥
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    # 加载任务
    task_loader = registry.get_tasks_loader(domain)
    all_tasks = task_loader()

    print(f"总任务数: {len(all_tasks)}")
    print(f"评测任务数: {max_tasks}")

    # 选择任务
    tasks = all_tasks[:max_tasks]

    # 创建输出目录
    output_path = Path(output_dir) / domain
    output_path.mkdir(parents=True, exist_ok=True)

    # 运行评测
    try:
        result = run_tasks(
            domain=domain,
            tasks=tasks,
            agent="llm_agent",
            user="user_simulator",
            llm_agent=agent_model,
            llm_user=user_model,
            llm_args_agent={"api_key": api_key},
            llm_args_user={"api_key": api_key},
            max_steps=max_rounds,
            num_trials=1,
            console_display=True,
        )

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = output_path / f"result_{timestamp}.json"

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 评测完成！结果已保存到: {result_file}")

        return result

    except Exception as e:
        print(f"\n[ERROR] 评测失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_all_domains(
    max_tasks_per_domain: int = 5,
    max_rounds: int = 3,
    agent_model: str = "gpt-4",
    user_model: str = "gpt-4"
):
    """运行所有临床域的评测"""
    print("\n" + "="*80)
    print("开始评测所有临床域")
    print("="*80 + "\n")

    results = {}

    for domain in CLINICAL_DOMAINS.keys():
        result = run_evaluation(
            domain=domain,
            max_tasks=max_tasks_per_domain,
            max_rounds=max_rounds,
            agent_model=agent_model,
            user_model=user_model
        )

        if result:
            results[domain] = result

    # 汇总结果
    print("\n" + "="*80)
    print("评测汇总")
    print("="*80 + "\n")

    print(f"已完成评测: {len(results)}/{len(CLINICAL_DOMAINS)} 个临床域")
    print()

    for domain, result in results.items():
        info = CLINICAL_DOMAINS[domain]
        print(f"  {info['name_cn']}: [OK] 完成")

    print()

    return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Tau2-Bench Clinical Domains Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有可用的临床域
  python run_clinical_benchmark.py --list

  # 运行单个临床域评测（测试 1 个任务）
  python run_clinical_benchmark.py --domain clinical_neurology --max-tasks 1

  # 运行所有临床域评测（每个域 5 个任务）
  python run_clinical_benchmark.py --all --max-tasks 5

  # 使用不同的模型
  python run_clinical_benchmark.py --domain clinical_cardiology --agent-model claude-3-opus-20240229

  # 完整评测（所有任务）
  python run_clinical_benchmark.py --all --max-tasks 1000
        """
    )

    parser.add_argument("--domain", type=str,
                       help="临床域 ID (例如: clinical_neurology)")
    parser.add_argument("--all", action="store_true",
                       help="运行所有临床域的评测")
    parser.add_argument("--list", action="store_true",
                       help="列出所有可用的临床域")
    parser.add_argument("--max-tasks", type=int, default=5,
                       help="每个域评测的最大任务数 (默认: 5)")
    parser.add_argument("--max-rounds", type=int, default=3,
                       help="每个任务的最大轮数 (默认: 3)")
    parser.add_argument("--agent-model", type=str, default="gpt-4",
                       help="代理使用的模型 (默认: gpt-4)")
    parser.add_argument("--user-model", type=str, default="gpt-4",
                       help="用户模拟器使用的模型 (默认: gpt-4)")
    parser.add_argument("--output-dir", type=str, default="outputs/clinical",
                       help="输出目录 (默认: outputs/clinical)")

    args = parser.parse_args()

    # 打印横幅
    print_banner()

    # 检查 API 密钥
    if not check_api_key():
        return 1

    # 列出域
    if args.list:
        list_domains()
        return 0

    # 运行评测
    if args.all:
        results = run_all_domains(
            max_tasks_per_domain=args.max_tasks,
            max_rounds=args.max_rounds,
            agent_model=args.agent_model,
            user_model=args.user_model
        )
    elif args.domain:
        if args.domain not in CLINICAL_DOMAINS:
            print(f"[ERROR] 错误: 未知的临床域 '{args.domain}'")
            print()
            print("可用的临床域:")
            for domain in CLINICAL_DOMAINS.keys():
                print(f"  - {domain}")
            return 1

        run_evaluation(
            domain=args.domain,
            max_tasks=args.max_tasks,
            max_rounds=args.max_rounds,
            agent_model=args.agent_model,
            user_model=args.user_model,
            output_dir=args.output_dir
        )
    else:
        parser.print_help()
        print()
        list_domains()

    return 0


if __name__ == "__main__":
    sys.exit(main())
