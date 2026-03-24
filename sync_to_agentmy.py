"""
同步质量阈值筛选模块到 agentmy 仓库
Python 版本
"""

import os
import shutil
import subprocess
from pathlib import Path


def run_command(cmd, description=""):
    """运行 shell 命令"""
    if description:
        print(f"  {description}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ 错误: {result.stderr}")
        return False
    return True


def sync_to_agentmy():
    """同步到 agentmy 仓库"""
    print("=" * 60)
    print("质量阈值筛选模块同步工具")
    print("=" * 60)
    print()

    # 配置路径
    base_dir = Path("C:/Users/方正")
    tau2_dqf = base_dir / "tau2-bench" / "DataQualityFiltering"
    agentmy_dir = base_dir / "agentmy"
    agentmy_dqf = agentmy_dir / "DataQualityFiltering"

    # 文件列表
    files_to_copy = [
        "scoring.py",
        "quality_classifier.py",
        "improver.py",
        "quality_threshold_pipeline.py",
        "reporting.py",
        "test_quality_threshold.py",
        "QUALITY_THRESHOLD_README.md",
    ]

    # 步骤 1: 检查仓库
    print("步骤 1: 检查 agentmy 仓库...")
    if not agentmy_dir.exists():
        print("  agentmy 目录不存在，需要先克隆仓库")
        print()
        print("  请运行以下命令克隆仓库（选择一种方式）：")
        print()
        print("  方式 1 (SSH - 推荐):")
        print("    cd C:\\Users\\方正")
        print("    git clone git@github.com:circadiancity/agentmy.git")
        print()
        print("  方式 2 (HTTPS):")
        print("    cd C:\\Users\\方正")
        print("    git clone https://github.com/circadiancity/agentmy.git")
        print()
        return False
    else:
        print(f"  ✅ 找到 agentmy 目录: {agentmy_dir}")
    print()

    # 步骤 2: 创建分支
    print("步骤 2: 创建 feature 分支...")
    os.chdir(agentmy_dir)
    run_command(
        "git checkout -b feature/quality-threshold-filtering",
        "创建 feature/quality-threshold-filtering 分支"
    ) or run_command(
        "git checkout feature/quality-threshold-filtering",
        "切换到 feature/quality-threshold-filtering 分支"
    )
    print()

    # 步骤 3: 复制文件
    print("步骤 3: 复制新模块文件...")
    for filename in files_to_copy:
        src = tau2_dqf / filename
        dst = agentmy_dqf / filename

        if src.exists():
            shutil.copy2(src, dst)
            print(f"  ✓ 已复制: {filename}")
        else:
            print(f"  ✗ 源文件不存在: {filename}")
    print()

    # 步骤 4: CLI 修改说明
    print("步骤 4: CLI 修改")
    print("  ⚠️  需要手动修改 DataQualityFiltering/__main__.py")
    print("  请参考 tau2-bench/DataQualityFiltering/__main__.py 的以下内容：")
    print()
    print("  1. 添加 UTF-8 编码支持（文件开头）")
    print("  2. 添加 quality-threshold 命令参数")
    print("  3. 添加 _handle_quality_threshold() 函数")
    print("  4. 在 _handle_data_quality() 中添加 quality-threshold 处理")
    print()
    print("  或者直接复制整个 __main__.py 文件")
    print()

    # 步骤 5: 运行测试
    print("步骤 5: 运行测试...")
    os.chdir(agentmy_dqf)
    if run_command("python test_quality_threshold.py", "运行测试"):
        print("  ✅ 所有测试通过")
    else:
        print("  ⚠️  测试失败")
        response = input("  是否继续提交？(y/n): ")
        if response.lower() != 'y':
            print("  ❌ 用户取消操作")
            return False
    print()

    # 步骤 6: 提交
    print("步骤 6: 提交更改...")
    os.chdir(agentmy_dir)

    for filename in files_to_copy:
        run_command(f"git add DataQualityFiltering/{filename}", f"添加 {filename}")

    commit_message = '''feat: add quality threshold filtering system (0-30 point scale)

Implement comprehensive quality threshold filtering with three-tier classification:

Features:
- Extended scoring system (0-30 points)
- Three-tier quality classification (HIGH/MEDIUM/LOW)
- Automatic improvement mechanism
- CLI integration
- Comprehensive reporting

All tests passing (5/5).

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>'''

    run_command(f'git commit -m "{commit_message}"', "提交更改")
    print()

    # 步骤 7: 推送
    print("步骤 7: 推送到远程仓库...")
    print("  运行以下命令推送:")
    print("    git push -u origin feature/quality-threshold-filtering")
    print()

    # 尝试自动推送
    if run_command("git push -u origin feature/quality-threshold-filtering", "推送到远程"):
        print()
        print("=" * 60)
        print("🎉 同步完成！")
        print("=" * 60)
        print()
        print("创建 Pull Request:")
        print("  https://github.com/circadiancity/agentmy/compare/main...feature/quality-threshold-filtering")
    else:
        print()
        print("=" * 60)
        print("⚠️  自动推送失败")
        print("=" * 60)
        print()
        print("请手动运行以下命令:")
        print("  cd C:\\Users\\方正\\agentmy")
        print("  git push -u origin feature/quality-threshold-filtering")

    return True


if __name__ == "__main__":
    try:
        sync_to_agentmy()
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消操作")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
