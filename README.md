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

**返回示例：**
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-15",
      "close": 482.50,
      "open": 480.20,
      "high": 483.10,
      "low": 479.80
    }
  ],
  "count": 30
}
```

### 2. 个股新闻

```
GET /api/news/stock?symbol=600519&limit=10
```

**参数：**
- `symbol`: 股票/基金代码
- `limit`: 返回数量限制（默认 10 条）

### 3. 财经快讯

```
GET /api/news/financial?symbol=全部&limit=50
```

**参数：**
- `symbol`: 品种符号（可选：全部、重要、VIP、贵金属、铜、铝、铅、锌、镍、锡）
- `limit`: 返回数量限制（默认 50 条）

### 4. 央视新闻

```
GET /api/news/cctv?date=20240115
```

**参数：**
- `date`: 日期，格式：YYYYMMDD（可选，默认今天）

### 5. 财经头条

```
GET /api/news/headlines
```

### 6. FastBull 快讯

```
GET /api/news/fastbull?limit=20
```

**参数：**
- `limit`: 返回数量限制（默认 20 条）

## 📁 项目结构

```
fund-monitor-api/
├── api_service/
│   └── main.py          # FastAPI 服务入口
├── config.py            # 配置文件
├── fund_core.py         # 数据获取核心模块
├── requirements.txt     # Python 依赖
├── .gitignore           # Git 忽略文件
└── README.md            # 项目说明
```

## ⚙️ 配置

所有配置项都在 `config.py` 文件中：

```python
# 网络配置
REQUEST_TIMEOUT = 10      # 请求超时（秒）
MAX_WORKERS = 5           # 并发请求数

# 日志配置
LOG_LEVEL = 'INFO'        # 日志级别
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# 版本信息
VERSION = "1.0.0"
```

## 🛠️ 技术栈

- **Python 3.8+**
- **FastAPI** - 高性能 Web 框架
- **AKShare** - 金融数据接口
- **Pandas** - 数据处理
- **Requests** - HTTP 请求
- **BeautifulSoup4** - HTML 解析

## ⚠️ 注意事项

1. **数据来源限制**：部分数据源可能有访问频率限制，请合理使用
2. **时效性**：新闻数据可能存在延迟，具体延迟时间取决于数据源
3. **CCTV 新闻**：最早支持 2016-02-03 的数据
4. **FastBull**：需要安装 `beautifulsoup4` 才能使用

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
