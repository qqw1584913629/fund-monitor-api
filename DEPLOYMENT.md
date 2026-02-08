# 🚀 云平台部署指南

本文档介绍如何将财经数据 API 服务部署到各大云平台。

## 📋 平台对比

| 平台 | 免费额度 | Python支持 | GitHub集成 | 推荐度 |
|-----|---------|-----------|------------|--------|
| **Hugging Face** | ✅ 永久免费 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Railway** | ❌ $5/月起 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Render** | ✅ 750小时/月 | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Fly.io** | ✅ 3个小应用 | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Cloudflare** | ❌ | ❌ | ✅ | ❌ 不支持Python |

---

## 🏆 方案 1: Hugging Face Spaces（最推荐，永久免费）

### 步骤：

1. **创建 Space**
   - 访问 https://huggingface.co/spaces
   - 点击 "Create new Space"
   - 填写信息：
     - SDK: **Docker**
     - Space name: `fund-monitor-api`
     - License: MIT
     - Visibility: Public（免费）

2. **上传代码**

   方式一：通过 Git 上传
   ```bash
   git clone https://huggingface.co/spaces/你的用户名/fund-monitor-api
   cd fund-monitor-api
   cp Dockerfile.hf Dockerfile
   cp -r ../api_service ../config.py ../fund_core.py ../requirements.txt .
   git add .
   git commit -m "Initial commit"
   git push
   ```

   方式二：通过 Web 界面上传文件
   - 将 `Dockerfile.hf` 重命名为 `Dockerfile`
   - 上传所有项目文件

3. **自动部署**
   - Hugging Face 会自动构建 Docker 镜像
   - 几分钟后，服务启动
   - 访问：`https://huggingface.co/spaces/你的用户名/fund-monitor-api`

### 注意事项：
- ⚠️ 首次构建需要 5-10 分钟
- ✅ 使用端口 7860（已配置在 Dockerfile 中）
- ✅ 完全免费，无限制

---

## 🚂 方案 2: Railway（最简单）

### 步骤：

1. **注册并连接 GitHub**
   - 访问 https://railway.app/
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 授权 Railway 访问你的 GitHub

2. **选择仓库**
   - 选择你的 `fund-monitor-api` 仓库
   - Railway 会自动检测 Python 项目

3. **配置部署**
   - Root Directory: `/`（根目录）
   - Build Command: 自动检测
   - Start Command: 自动检测

4. **添加环境变量（可选）**
   - Settings → Variables
   - 可以添加 `LOG_LEVEL=DEBUG` 等

5. **部署完成**
   - 点击 "Deploy"
   - 几分钟后获得域名：`https://你的应用.railway.app`

### 费用：
- 免费试用：$5 免费额度
- 之后：$5/月起

---

## 🎨 方案 3: Render（免费额度大）

### 步骤：

1. **注册并连接 GitHub**
   - 访问 https://render.com/
   - 点击 "New" → "Web Service"
   - 连接 GitHub 仓库

2. **配置表单**
   - Name: `fund-monitor-api`
   - Region: Singapore（离国内近）
   - Branch: `main`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api_service.main:app --host 0.0.0.0 --port $PORT`

3. **部署**
   - 点击 "Create Web Service"
   - 自动部署
   - 获得域名：`https://fund-monitor-api.onrender.com`

### 免费额度：
- ✅ 750 小时/月（足够一个月运行）
- ✅ 512MB RAM
- ✅ 自动休眠（无流量15分钟后）

---

## ✈️ 方案 4: Fly.io（全球部署）

### 步骤：

1. **安装 Fly CLI**
   ```bash
   # macOS/Linux
   curl -L https://fly.io/install.sh | sh

   # Windows
   pwsh -c "iwr https://fly.io/install.ps1 | iex"
   ```

2. **登录**
   ```bash
   flyctl auth login
   ```

3. **部署**
   ```bash
   cd fund-monitor-api
   flyctl launch
   # 按提示操作，选择地区等
   flyctl deploy
   ```

4. **访问**
   ```bash
   flyctl open
   ```

### 免费额度：
- ✅ 3 个小应用免费
- ✅ 160GB 出站流量/月
- ✅ 3GB 卷存储

---

## ❌ 为什么不用 Cloudflare？

**Cloudflare Workers 不支持 Python**，原因：

1. **运行时限制**
   - Cloudflare Workers 只支持 JavaScript/TypeScript/WASM
   - Python 需要转换为 WASM（Pyodide），性能差且限制多

2. **API 适配器**
   - 需要重写所有代码为 JavaScript
   - AKShare 等库无法使用

3. **更好的替代**
   - Hugging Face Spaces：免费、简单、Python 原生
   - Railway：自动从 GitHub 部署
   - Render：750小时免费

---

## 🔧 部署检查清单

部署前确认：

- [ ] `requirements.txt` 包含所有依赖
- [ ] `api_service/main.py` 入口正确
- [ ] 端口使用环境变量 `$PORT`（Render/Fly）
- [ ] 健康检查路径 `/health` 可访问
- [ ] 仓库包含 `.gitignore` 排除敏感文件

---

## 📊 性能优化建议

1. **缓存策略**
   ```python
   # 在 fund_core.py 中添加缓存
   from functools import lru_cache

   @lru_cache(maxsize=128)
   def get_gold_history_cached(days: int = 30):
       return get_gold_history(days)
   ```

2. **并发限制**
   ```python
   # config.py
   MAX_WORKERS = 3  # 云平台资源有限，降低并发
   ```

3. **超时设置**
   ```python
   # config.py
   REQUEST_TIMEOUT = 5  # 云平台网络可能较慢
   ```

---

## 🌏 选择建议

| 需求 | 推荐平台 |
|-----|---------|
| 完全免费，永久使用 | Hugging Face Spaces |
| 最简单，从 GitHub 一键部署 | Railway |
| 免费额度大，离国内近 | Render |
| 全球多节点部署 | Fly.io |

---

## 🎯 我的推荐

**个人项目/学习**：Hugging Face Spaces（免费+简单）

**生产环境**：Railway（稳定+快速）

**国内访问**：Render（新加坡节点）

---

部署有问题？检查：
1. Dockerfile 是否正确
2. requirements.txt 是否完整
3. 端口是否使用环境变量
4. 健康检查路径是否配置
