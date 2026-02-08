# 财经数据 API 服务

一个简洁的财经数据 API 服务，提供黄金历史价格和多种新闻资讯数据接口。

## ✨ 功能特性

| 功能 | 描述 | 数据源 |
|-----|------|--------|
| **🥇 黄金历史** | 获取上海黄金交易所 Au99.99 历史价格 | AKShare |
| **📌 个股新闻** | 获取股票/基金相关新闻 | 东方财富 |
| **⚡ 财经快讯** | 获取期货/商品新闻快讯 | 上海有色网 |
| **📺 央视新闻** | 获取新闻联播文字稿 | 央视网 |
| **🏆 财经头条** | 获取财新网主要新闻 | 财新网 |
| **🚀 FastBull快讯** | 获取 7x24 小时财经快讯 | FastBull |

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行服务

```bash
python api_service/main.py
```

服务将在 `http://localhost:5000` 启动。

### 查看文档

访问 `http://localhost:5000/docs` 查看 Swagger API 文档。

## 📖 API 接口

### 1. 黄金历史价格

```
GET /api/gold/history?days=30
```

**参数：**
- `days`: 获取天数（默认 30 天，最大 720 天）

### 2. 个股新闻

```
GET /api/news/stock?symbol=600519&limit=10
```

### 3. 财经快讯

```
GET /api/news/financial?symbol=全部&limit=50
```

### 4. 央视新闻

```
GET /api/news/cctv?date=20240115
```

### 5. 财经头条

```
GET /api/news/headlines
```

### 6. FastBull 快讯

```
GET /api/news/fastbull?limit=20
```

## ☁️ 云平台部署

> 📘 **详细部署指南**: 查看 [DEPLOYMENT.md](DEPLOYMENT.md) 获取完整部署说明

### Hugging Face Spaces（推荐，永久免费）

1. 访问 https://huggingface.co/spaces
2. 点击 "Create new Space" → 选择 **Docker** SDK
3. 将 `Dockerfile.hf` 重命名为 `Dockerfile`
4. 上传代码，自动部署

### Railway（推荐，最简单）

1. 访问 https://railway.app/
2. "New Project" → "Deploy from GitHub repo"
3. 选择你的仓库，自动部署

### Render（免费）

1. 访问 https://render.com/
2. "New" → "Web Service" → 连接 GitHub
3. Start Command: `uvicorn api_service.main:app --host 0.0.0.0 --port $PORT`

---

> ⚠️ **Cloudflare 不支持 Python**，请使用上述平台替代。详见 [DEPLOYMENT.md](DEPLOYMENT.md)

## 📁 项目结构

```
fund-monitor-api/
├── api_service/
│   └── main.py          # FastAPI 服务入口
├── config.py            # 配置文件
├── fund_core.py         # 数据获取核心模块
├── requirements.txt     # Python 依赖
└── README.md            # 项目说明
```

## 📄 License

MIT License
