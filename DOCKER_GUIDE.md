# 使用Docker模拟GitHub Actions环境的完整指南

## 🐳 为什么选择Docker？

### 优势
- ✅ **环境100%一致**：与GitHub Actions完全相同
- ✅ **快速反馈**：本地测试，秒级结果
- ✅ **完全隔离**：不影响你的Windows环境
- ✅ **可重现**：团队其他成员结果完全相同
- ✅ **易于调试**：可以进入容器交互

## 📋 安装步骤

### 步骤1：安装Docker Desktop

#### 下载地址
```
https://www.docker.com/products/docker-desktop/
```

#### 安装过程
1. 下载 `Docker Desktop for Windows`
2. 双击安装程序
3. 重启计算机（如果需要）
4. 启动Docker Desktop
5. 等待Docker引擎启动（状态栏出现鲸鱼图标）

#### 验证安装
```powershell
# 在PowerShell中运行
docker --version
docker compose version
```

应该看到版本号。

---

## 🚀 使用指南

### 快速测试（一键运行）

```bash
# 方式1：使用脚本
bash test_with_docker.sh

# 方式2：手动命令
docker build -f Dockerfile.test -t tau2-test .
docker run --rm tau2-test
```

### 详细测试（包含所有功能）

```bash
# 1. 构建镜像
docker build -f Dockerfile.test -t tau2-test .

# 2. 运行基本测试
docker run --rm tau2-test

# 3. 进入容器交互
docker run --rm -it tau2-test bash

# 在容器内
python
>> from DataQualityFiltering.core import LLMEvaluator
>> # 测试你的代码
```

---

## 🔧 高级用法

### 测试特定模块

```bash
# 测试模块2：无幻觉诊断
docker run --rm tau2-test python -c "
import sys
sys.path.insert(0, '.')
from evaluator_no_hallucination import NoHallucinationDiagnosisEvaluator
evaluator = NoHallucinationDiagnosisEvaluator()
result = evaluator.evaluate(
    patient_input='医生，我不舒服。',
    agent_response='您能详细说说哪里不舒服吗？',
    available_info={'symptoms': ['不舒服']}
)
print(f'Score: {result[\"overall_score\"]}')
"
```

### 持续化测试

```bash
# 后台运行测试
docker run -d --name test-runner tau2-test tail -f /dev/null

# 查看结果
docker logs test-runner

# 清理
docker stop test-runner
docker rm test-runner
```

---

## 🛠️ 开发工作流

### 方案A：每次提交前测试

```bash
# 1. 本地开发
# ... 编写代码 ...

# 2. 提交前测试
bash test_with_docker.sh

# 3. 如果测试通过，提交
git add .
git commit -m "feat: new feature"
git push
```

### 方案B：集成到Git Hook（自动测试）

创建 `.git/hooks/pre-commit`：

```bash
#!/bin/bash
echo "🐳 Running Docker tests before commit..."
bash test_with_docker.sh
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Tests failed! Commit aborted."
    echo "Please fix the issues and try again."
    exit 1
fi

echo "✅ Tests passed! Proceeding with commit..."
exit 0
```

启用hook：
```bash
chmod +x .git/hooks/pre-commit
```

### 方案C：Python脚本自动测试

创建 `test_and_push.sh`：

```bash
#!/bin/bash
echo "🐧 Step 1: Running Docker tests..."
bash test_with_docker.sh
if [ $? -ne 0 ]; then
    echo "❌ Tests failed!"
    exit 1
fi

echo "✅ Tests passed!"
echo ""
echo "📤 Step 2: Pushing to GitHub..."
git push

echo "🎉 Done!"
```

---

## 📊 故障排除

### 问题1：docker command not found

**原因**：Docker未安装或未启动

**解决**：
```powershell
# 检查Docker Desktop是否运行
# 查看系统托盘是否有Docker图标

# 如果没有图标
Start -> Docker Desktop
```

### 问题2：Build failed

**原因**：网络问题或依赖安装失败

**解决**：
```bash
# 使用国内镜像源
docker build -f Dockerfile.test -t tau2-test \
  --build-arg MIRROR=https://mirrors.tuna.tsinghua.edu.cn/pypi/simple/
```

### 问题3：Permission denied

**原因**：文件权限问题

**解决**：
```bash
# 在WSL中运行
wsl bash test_with_docker.sh
```

### 问题4：端口冲突

**原因**：不太可能，我们不暴露端口

**解决**：不需要暴露端口

---

## 🎓 最佳实践

### 1. 镜像管理

```bash
# 查看镜像
docker images

# 删除旧镜像
docker rmi tau2-test

# 清理系统
docker system prune
```

### 2. 日志查看

```bash
# 查看构建日志
docker build -f Dockerfile.test -t tau2-test 2>&1 | tee build.log

# 查看运行日志
docker run --rm tau2-test 2>&1 | tee run.log
```

### 3. 性能优化

```bash
# 第一次构建较慢（5-10分钟）
# 后续构建很快（<1分钟）

# 如果想更快，使用缓存
docker build -f Dockerfile.test -t tau2-test --cache-from=tau2-test
```

---

## 🎉 成功标志

### Docker测试通过的输出

```
✅ All basic tests passed!
[SUCCESS] Repository is healthy
```

### 推送到GitHub后的结果

```
GitHub Actions:
✅ Basic Health Check - PASSED
✅ Test 1 - Import Check - PASSED
✅ Test 2 - Tau2 Evaluators - PASSED
✅ Test 3 - Data Quality - PASSED
✅ Success - PASSED
```

---

## 📚 进阶使用

### 创建多阶段测试

创建 `Dockerfile.multi`：

```dockerfile
# 构建阶段
FROM ubuntu:22.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python3.10 pip
WORKDIR /workspace
COPY . .
RUN pip install -e .

# 测试阶段
FROM ubuntu:22.04
COPY --from=builder /workspace /workspace
ENV PYTHONPATH=/workspace
CMD ["python", "-c", "import sys; sys.path.insert(0, '.'); from tau2.evaluator import ClinicalEvaluator; print('[OK] All tests passed!')"]
```

### 集成到CI/CD

```yaml
# .github/workflows/test.yml
jobs:
  docker-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and test with Docker
        run: |
          docker build -f Dockerfile.test -t tau2-test .
          docker run --rm tau2-test
```

---

## 💡 小贴士

### 1. Docker Desktop配置

```yaml
Settings -> Resources:
  Memory: 4GB (建议)
  CPUs: 2 (建议)
  Disk: 50GB (建议)
```

### 2. 文件共享

Docker Desktop会自动共享：
- ✅ C:\Users
- ✅ 当前目录

### 3. 网络代理

如果需要代理：

```yaml
# Docker Desktop Settings -> Resources -> Proxies
Web: http://your-proxy:port
```

---

## 🚀 现在开始！

### 第一次使用（5分钟设置）

```bash
# 1. 安装Docker Desktop（下载并安装）
# 2. 启动Docker Desktop
# 3. 运行测试
bash test_with_docker.sh
```

### 日常使用（10秒验证）

```bash
# 每次推送前运行
bash test_with_docker.sh && git push
```

---

## 📞 需要帮助？

如果遇到问题：
1. 检查Docker Desktop是否运行
2. 查看Docker Desktop日志
3. 检查防火墙/杀毒软件
4. 尝试 `docker system prune -a` 清理

---

**开始使用吧！** 🎉

需要我帮你：
1. 配置Docker Desktop？
2. 测试Docker安装？
3. 解决Docker问题？
