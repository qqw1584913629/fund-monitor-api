# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

财经数据 API 服务 v1.0.0 - 提供黄金历史价格、基金实时排行、多种新闻资讯数据接口的 RESTful API 服务。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 API 服务（方式1：uvicorn）
python -m uvicorn api_service.main:app --host 0.0.0.0 --port 5000

# 启动 API 服务（方式2：直接运行）
python -m api_service.main

# 访问 API 文档
# http://localhost:5000/docs (Swagger UI)
# http://localhost:5000/redoc (ReDoc)

# 健康检查
curl http://localhost:5000/health
```

## 架构说明

### 分层架构

```
客户端层（浏览器/C#/移动端）
    ↓ HTTP/JSON
API 服务层 (FastAPI)
    ↓ 函数调用
核心数据层 (fund_core.py)
    ↓ HTTP/API 调用
数据源层 (AKShare/东方财富/财新网/央视网/FastBull)
```

### 项目结构

```
fund-monitor-api/
├── api_service/
│   └── main.py                # FastAPI 服务入口（8个 RESTful 端点）
├── fund_core.py               # 核心数据模块（7个数据获取函数）
├── config.py                  # 配置中心（网络、日志、版本）
├── requirements.txt           # Python 依赖（9个核心包）
├── Dockerfile                 # Hugging Face Spaces 部署配置
├── render.yaml                # Render 平台部署配置
├── railway.json               # Railway 平台部署配置
├── fly.toml                   # Fly.io 平台部署配置
├── README.md                  # 项目主文档
├── DEPLOYMENT.md              # 部署指南
└── .gitignore                 # Git 忽略规则
```

## 核心 API 端点

| 端点路径 | HTTP 方法 | 功能 | 参数 |
|---------|----------|------|------|
| `/` | GET | 服务状态及端点列表 | 无 |
| `/health` | GET | 健康检查 | 无 |
| `/api/gold/history` | GET | 黄金历史价格 | days (默认30, 最大720) |
| `/api/fund/ranking` | GET | 基金涨幅排行 | limit (默认100, 最大500) |
| `/api/news/stock` | GET | 个股/基金新闻 | symbol, limit (默认10) |
| `/api/news/financial` | GET | 期货/商品快讯 | symbol (默认"全部"), limit (默认50) |
| `/api/news/headlines` | GET | 财新头条 | 无 |
| `/api/news/fastbull` | GET | FastBull快讯 | limit (默认20) |
| `/api/news/cctv` | GET | 央视新闻联播 | date (YYYYMMDD格式, 可选) |

## 核心模块 (fund_core.py)

### 数据获取函数

| 函数 | 数据源 | 功能 | 返回类型 |
|------|--------|------|----------|
| `get_gold_history(days)` | AKShare (上海黄金交易所) | 获取 Au99.99 历史价格 | DataFrame |
| `get_fund_daily_ranking(limit)` | AKShare (东方财富) | 获取基金当日涨跌幅排行 | DataFrame |
| `get_stock_news(codes, limit)` | 东方财富 | 个股/基金相关新闻 | DataFrame |
| `get_financial_news(symbol, limit)` | 上海有色网 | 期货/商品新闻快讯 | DataFrame |
| `get_cctv_news(date)` | 央视网 | 新闻联播文字稿 | DataFrame |
| `get_financial_headlines()` | 财新网 | 财经头条新闻 | DataFrame |
| `get_fastbull_news(limit)` | FastBull | 7x24小时财经快讯 | DataFrame |

### API 服务层 (api_service/main.py)

**数据模型：**
```python
class GoldPrice(BaseModel):
    date: str
    close: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None

class FundRanking(BaseModel):
    code: str
    name: str
    net_value: Optional[float] = None
    accumulated_net_value: Optional[float] = None
    daily_growth_rate: Optional[float] = None
    date: Optional[str] = None
```

**统一响应格式：**
```python
{
    "success": True/False,
    "data": [...],           # 或 "news": [...]
    "count": 10,
    "message": "错误信息"     # 可选
}
```

## 功能模块

### 1. 黄金历史价格 API

**端点：** `GET /api/gold/history?days=30`

**数据源：** 上海黄金交易所 Au99.99

**返回字段：**
- `date`: 日期
- `close`: 收盘价
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `volume`: 成交量

**使用示例：**
```bash
curl http://localhost:5000/api/gold/history?days=30
```

### 2. 基金涨幅排行 API ⭐ 新增

**端点：** `GET /api/fund/ranking?limit=100`

**数据源：** 东方财富 - 场外基金实时估值

**返回字段：**
- `code`: 基金代码
- `name`: 基金名称
- `net_value`: 单位净值
- `accumulated_net_value`: 累计净值
- `daily_growth_rate`: 日增长率(%)
- `date`: 净值日期

**使用示例：**
```bash
# 获取涨幅前10名的基金
curl http://localhost:5000/api/fund/ranking?limit=10
```

### 3. 个股/基金新闻 API

**端点：** `GET /api/news/stock?symbol=600519&limit=10`

**数据源：** 东方财富

**使用场景：** 查询特定股票或基金的相关新闻

### 4. 财经快讯 API

**端点：** `GET /api/news/financial?symbol=贵金属&limit=50`

**数据源：** 上海有色网

**可选品种：** 全部, 重要, VIP, 贵金属, 铜, 铝, 铅, 锌, 镍, 锡

### 5. 财新头条 API

**端点：** `GET /api/news/headlines`

**数据源：** 财新网

**内容：** 财经头条新闻列表

### 6. FastBull 快讯 API

**端点：** `GET /api/news/fastbull?limit=20`

**数据源：** FastBull (网页爬取)

**内容：** 7x24小时实时财经快讯

### 7. 央视新闻联播 API

**端点：** `GET /api/news/cctv?date=20260209`

**数据源：** 央视网

**内容：** 新闻联播文字稿（最早支持 20160203）

## 配置说明

### config.py 配置项

```python
# 版本信息
VERSION = "1.0.0"

# 网络配置
REQUEST_TIMEOUT = 10      # HTTP 请求超时（秒）
MAX_WORKERS = 5           # 并发线程数

# 日志配置
LOG_LEVEL = "INFO"        # 日志级别：DEBUG/INFO/WARNING/ERROR
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
```

### 环境变量

当前项目**无需环境变量**，所有配置集中在 `config.py`。

## 技术特性

### 核心特性

- **类型提示** - 全面使用 Python typing 模块
- **并发请求** - ThreadPoolExecutor 并发获取数据
- **错误恢复** - 所有函数返回空 DataFrame 而非抛出异常
- **数据标准化** - 统一返回 pandas DataFrame
- **CORS 支持** - 允许跨域请求，支持浏览器/C#/移动端调用
- **自动 API 文档** - FastAPI 自动生成 Swagger UI 和 ReDoc

### 安全特性

- **输入验证** - 使用 Pydantic 进行数据验证
- **参数限制** - days 最大720天，limit 最大500条
- **安全序列化** - 正确处理 pandas 特殊类型（Timestamp, datetime64）
- **异常处理** - 统一错误处理，返回标准 HTTP 状态码

### 部署特性

- **多平台支持** - 提供部署配置：Hugging Face, Render, Railway, Fly.io
- **健康检查** - `/health` 端点用于服务监控
- **环境变量端口** - 支持 `$PORT` 环境变量（云平台标准）
- **Docker 支持** - 标准化容器部署

## 数据流

```
客户端请求
    ↓
API 层验证参数
    ↓
调用核心函数
    ↓
数据获取
    ├── AKShare API（黄金、基金）
    ├── 网页爬取（FastBull）
    └── 第三方 API（东方财富、央视、财新）
    ↓
数据转换
    ├── DataFrame → JSON
    ├── 时间格式化
    └── NaN → null
    ↓
响应返回
```

## 依赖关系

```
fastapi>=0.100.0          # Web 框架
├── uvicorn>=0.23.0       # ASGI 服务器
└── pydantic               # 数据验证

pandas>=2.0.0             # 数据处理
numpy>=1.24.0             # 数值计算

akshare>=1.10.0           # 财经数据源
requests>=2.28.0          # HTTP 客户端
beautifulsoup4>=4.12.0    # HTML 解析
```

## 注意事项

- **无状态设计** - 无需数据库，所有数据实时从外部数据源获取
- **无缓存机制** - 当前版本无缓存，频繁请求可能被限流（可优化）
- **数据源稳定性** - 2个数据源依赖网页爬取，脆弱性较高（FastBull、财新）
- **非交易时间** - 部分数据在非交易时间可能无法获取
- **编码问题** - Windows 控制台已配置 UTF-8 编码支持
- **日志级别** - 可通过 `config.py` 的 `LOG_LEVEL` 调整
- **端口冲突** - 默认端口 5000，如冲突可修改启动命令

## 部署平台

### 快速部署

**Hugging Face Spaces：**
```bash
# 推送代码到 GitHub 仓库
# 在 Hugging Face 创建新 Space，选择 Docker
# 关联 GitHub 仓库，自动部署
```

**Render：**
```bash
# 关联 GitHub 仓库
# render.yaml 会自动配置构建和启动命令
```

**Railway：**
```bash
# 安装 Railway CLI
railway login
railway init
railway up
```

**Fly.io：**
```bash
# 安装 Fly CLI
fly launch
fly deploy
```

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn api_service.main:app --reload --host 0.0.0.0 --port 5000

# 访问文档
open http://localhost:5000/docs
```

## 常见问题

**Q: 为什么某些接口返回空数据？**
A: 可能是数据源暂时不可用，或非交易时间数据未更新。检查 `/health` 端点确认服务状态。

**Q: 如何添加新的数据源？**
A: 在 `fund_core.py` 添加新函数，然后在 `api_service/main.py` 添加对应端点。

**Q: 如何修改端口？**
A: 修改启动命令中的 `--port` 参数，如 `--port 8080`。

**Q: 中文显示乱码怎么办？**
A: 确保终端使用 UTF-8 编码，Windows 已在代码中处理。

**Q: 如何限制 API 访问？**
A: 当前版本无认证，如需添加可使用 FastAPI 的 `OAuth2PasswordBearer` 或 API Key 中间件。
