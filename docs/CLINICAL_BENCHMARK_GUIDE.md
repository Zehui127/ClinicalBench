# Tau2-Bench 临床域评测指南

## 📋 概述

本指南帮助你运行 tau2-bench 医疗临床域的评测。项目包含 5 个临床科室，共 2,450 个任务。

### 临床域列表

| 临床域 | 名称 | 任务数 | 描述 |
|--------|------|--------|------|
| `clinical_cardiology` | 心脏科 | 758 | 心血管疾病、心电图、血压、胸痛 |
| `clinical_endocrinology` | 内分泌科 | 176 | 糖尿病、甲状腺、激素代谢 |
| `clinical_gastroenterology` | 胃肠科 | 475 | 消化系统、肝脏、内镜检查 |
| `clinical_nephrology` | 肾病科 | 300 | 肾脏疾病、CKD 分期、透析 |
| `clinical_neurology` | 神经科 | 741 | 脑血管、癫痫、头痛、认知障碍 |

## 🚀 快速开始

### 步骤 1: 配置 API 密钥

编辑 `.env` 文件，填入你的 API 密钥：

```bash
# 编辑 .env 文件
OPENAI_API_KEY=sk-your-openai-api-key-here
# 或
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
```

### 步骤 2: 激活虚拟环境

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 步骤 3: 运行评测

```bash
# 列出所有可用的临床域
python run_clinical_benchmark.py --list

# 运行单个临床域评测（测试 1 个任务）
python run_clinical_benchmark.py --domain clinical_neurology --max-tasks 1

# 运行所有临床域评测（每个域 5 个任务）
python run_clinical_benchmark.py --all --max-tasks 5

# 使用不同的模型
python run_clinical_benchmark.py --domain clinical_cardiology --agent-model claude-3-opus-20240229
```

## 📊 评测结果

结果保存在 `outputs/clinical/<domain>/` 目录下：

```
outputs/
└── clinical/
    ├── clinical_neurology/
    │   └── result_20260311_234412.json
    ├── clinical_cardiology/
    │   └── result_20260311_234500.json
    └── ...
```

## 🎯 常用命令

### 测试运行（快速验证）

```bash
# 测试单个任务
python run_clinical_benchmark.py --domain clinical_neurology --max-tasks 1 --max-rounds 1
```

### 小规模评测

```bash
# 每个域评测 5 个任务
python run_clinical_benchmark.py --all --max-tasks 5
```

### 完整评测（所有任务）

```bash
# 评测所有任务（需要较长时间和 API 配额）
python run_clinical_benchmark.py --all --max-tasks 1000
```

### 使用特定模型

```bash
# 使用 GPT-4
python run_clinical_benchmark.py --domain clinical_cardiology --agent-model gpt-4 --user-model gpt-4

# 使用 Claude 3 Opus
python run_clinical_benchmark.py --domain clinical_cardiology --agent-model claude-3-opus-20240229

# 使用 GPT-3.5（更便宜）
python run_clinical_benchmark.py --domain clinical_cardiology --agent-model gpt-3.5-turbo
```

## 🔧 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--domain` | 临床域 ID | - |
| `--all` | 运行所有临床域 | False |
| `--list` | 列出所有可用的临床域 | False |
| `--max-tasks` | 每个域评测的最大任务数 | 5 |
| `--max-rounds` | 每个任务的最大轮数 | 3 |
| `--agent-model` | 代理使用的模型 | gpt-4 |
| `--user-model` | 用户模拟器使用的模型 | gpt-4 |
| `--output-dir` | 输出目录 | outputs/clinical |

## 📝 示例输出

```
================================================================================
                    TAU2-BENCH CLINICAL EVALUATION
================================================================================

[OK] API 密钥已配置

================================================================================
开始评测: 神经科 (clinical_neurology)
================================================================================

总任务数: 741
评测任务数: 1

Starting evaluation...
Task: clinical_neurology_001
...

[OK] 评测完成！结果已保存到: outputs/clinical/clinical_neurology/result_20260311_234412.json
```

## 💡 提示

1. **成本控制**: 建议先用 `--max-tasks 1` 测试，确认无误后再运行完整评测
2. **模型选择**: GPT-3.5-turbo 更便宜，适合快速测试；GPT-4 或 Claude 3 Opus 性能更好
3. **并行运行**: 可以同时运行多个临床域的评测以提高效率
4. **结果分析**: 结果文件包含详细的交互记录和评分

## 🐛 故障排除

### 问题: API 密钥未找到

```
[ERROR] 错误: 未找到有效的 API 密钥
```

**解决方案**:
1. 检查 `.env` 文件是否存在
2. 确认 API 密钥格式正确
3. 或设置环境变量: `export OPENAI_API_KEY=your_key`

### 问题: 模块导入错误

```
ModuleNotFoundError: No module named 'tau2'
```

**解决方案**:
```bash
# 确保在项目根目录
cd tau2-bench

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -e .
```

### 问题: 编码错误

**解决方案**: 确保终端使用 UTF-8 编码（Windows PowerShell 默认支持）

## 📚 相关资源

- **项目仓库**: https://github.com/circadiancity/agentmy
- **Tau2-Bench 文档**: https://github.com/osokininds/tau2-bench
- **项目 README**: README.md
- **临床域总结**: CLINICAL_DOMAINS_SUMMARY.md

## 🤝 贡献

如有问题或建议，请提交 Issue 或 Pull Request 到 GitHub 仓库。
