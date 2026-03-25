# Docker Desktop 安装指南 - Windows

## 📥 第1步：下载Docker Desktop

### 方法1：官网下载（推荐）

1. **访问官方网站**
   ```
   https://www.docker.com/products/docker-desktop/
   ```

2. **下载Windows版本**
   - 点击 "Download for Windows"
   - 文件名：`Docker Desktop Installer.exe`
   - 大小：约500MB

### 方法2：国内镜像（更快）

如果官网慢，使用国内镜像：
```
https://mirrors.aliyun.com/docker-toolbox/windows/docker-for-windows/
```

---

## 🛠️ 第2步：安装Docker Desktop

### 安装过程

1. **运行安装程序**
   - 双击下载的 `.exe` 文件
   - 可能弹出UAC提示，点击"是"

2. **配置选项**
   ✅ 勾选 "Use WSL 2 based engine"（推荐）
   ✅ 勾选 "Add shortcut to desktop"
   - 点击 "OK"

3. **等待安装**
   - 安装过程：2-5分钟
   - 会下载WSL2内核
   - 可能要求重启

### 重启计算机

安装完成后会提示重启：
```
✅ 点击 "Restart now"
```

---

## 🚀 第3步：启动和配置

### 首次启动

1. **启动Docker Desktop**
   - 双击桌面图标
   - 或从开始菜单启动

2. **接受服务协议**
   - 点击 "Accept"

3. **等待启动**
   - 系统托盘出现鲸鱼图标
   - 等待变为绿色（Running）

### 验证安装

打开 **PowerShell** 或 **Git Bash**：

```powershell
# 检查Docker版本
docker --version

# 应该看到：
# Docker version 24.0.7, build 12965
```

---

## ⚙️ 配置优化

### 推荐设置

#### 1. 资源设置

**Docker Desktop Dashboard → Settings → Resources**

```
内存: 4-8GB
CPU: 2-4核
磁盘: 50GB
```

#### 2. 文件共享

**Docker Desktop Dashboard → Settings → Resources → File Sharing**

```
✅ 勾选 C:\Users
✅ 勾选 你的项目目录
```

#### 3. 网络代理（如果需要）

**Settings → Resources → Proxies**

```
Web: http://proxy:port
HTTPS: http://proxy:port
```

---

## ✅ 验证安装成功

### 测试命令

在 **Git Bash** 或 **PowerShell** 中运行：

```bash
# 检查Docker
docker --version

# 检查Docker Compose
docker-compose version

# 测试运行Hello World
docker run hello-world
```

**成功输出**：
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

---

## 🐛 故障排除

### 问题1：Docker Desktop无法启动

**可能原因**：
- Hyper-V未启用
- WSL2未安装
- 虚拟化被禁用

**解决方案**：

#### 启用WSL2
```powershell
# PowerShell (管理员)
dism.exe /online /norestart
dism.exe /enable-feature:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /enable-feature:VirtualMachinePlatform /all /norestart
```

然后重启电脑。

#### 启用Hyper-V（如果WSL2失败）
```powershell
# 控制面板 → 程序 → 启用或关闭Windows功能
# 勾选：
✅ Hyper-V
✅ 虚拟机平台
```

### 问题2：构建失败

**可能原因**：
- 内存不足
- 网络问题
- 路径问题

**解决方案**：

```bash
# 清理Docker缓存
docker system prune -a

# 重启Docker Desktop
# 右键系统托盘图标 → Restart
```

### 问题3：权限错误

**可能原因**：
- 文件权限
- 防火墙/杀毒软件

**解决方案**：

```bash
# 使用Git Bash而不是CMD
# 或使用PowerShell（管理员）
```

### 问题4：下载慢

**解决方案**：使用国内镜像

```bash
# 配置国内镜像源
# 创建或编辑 %USERPROFILE%\.docker\daemon.json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
```

---

## 🎯 安装检查清单

完成以下检查：

- [ ] Docker Desktop已安装
- [ ] Docker Desktop已启动
- [ ] 系统托盘显示Docker图标（绿色）
- [ ] `docker --version` 返回版本号
- [ ] `docker run hello-world` 成功
- [ ] 项目目录已设置文件共享

全部打勾 = ✅ 安装成功！

---

## 🚀 安装完成后

### 测试你的环境

```bash
# 在项目目录运行
bash test_with_docker.sh
```

### 日常使用

```bash
# 推送前测试
bash test_with_docker.sh && git push
```

---

## 📞 需要帮助？

### 如果遇到问题

1. **查看Docker日志**
   - Docker Desktop → 菜单 → Diagnostics
   - 或查看 `~/Library/Containers/com.docker.docker/Data/log/host`

2. **重启Docker**
   ```bash
   # 右键系统托盘图标 → Restart
   ```

3. **完全重置**
   ```bash
   # 卸载Docker Desktop
   # 重新安装
   ```

---

## ✅ 准备好了吗？

**安装完成后告诉我**：
1. 安装是否成功？
2. `docker --version` 输出什么？
3. 运行 `bash test_with_docker.sh` 的结果如何？

我会根据你的反馈继续协助！
