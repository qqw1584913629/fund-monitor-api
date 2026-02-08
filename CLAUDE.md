# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基金实时估值监控工具 v2.1.0 - 用于追踪中国公募基金的实时估值、持仓盈亏、数据可视化分析，支持微信预警推送。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 Streamlit Web 界面
streamlit run fund_streamlit.py

# 运行命令行监控工具
python fund_realtime_valuation.py
```

## 架构说明

### 数据获取策略（按优先级）

1. **天天基金估值接口** - 直接调用 `fundgz.1234567.com.cn` 获取盘中实时估值（最快最准，并发请求）
2. **商品期货基金估算** - 根据对应期货品种（沪金/沪银）实时涨跌幅估算净值
3. **历史净值兜底** - 通过 akshare 的 `fund_open_fund_info_em` 获取最新净值

### 项目结构

```
Project_A/
├── config.py                 # 配置中心（API、超时、缓存、推送等）
├── fund_core.py              # 核心模块（数据获取、持仓、预警、推送）
├── fund_streamlit.py         # Streamlit Web 界面（9个标签页）
├── fund_realtime_valuation.py # 命令行监控工具
├── fund_portfolio_v2.json    # 持仓数据（份额+成本价模型）
├── fund_history.json         # 历史记录（每日快照+交易记录）
├── .env                      # 本地配置（含推送Token，不上传）
├── .env.example              # 配置示例（上传到GitHub）
├── requirements.txt          # Python 依赖
├── Dockerfile                # Docker 镜像配置
├── docker-compose.yml        # Docker Compose 配置
└── .streamlit/               # Streamlit 主题配置
```

### 核心模块 (fund_core.py)

| 函数/类 | 用途 |
|--------|------|
| `get_fund_data(codes)` | 获取基金数据（多数据源降级策略） |
| `get_single_fund_valuation(code)` | 获取单只基金实时估值 |
| `get_commodity_fund_valuation(code, nav)` | 商品期货基金估值计算 |
| `validate_fund_code(code)` | 验证基金代码格式（6位数字） |
| `search_fund(keyword)` | 搜索基金 |
| `get_fund_ranking(type, sort_by)` | 获取基金排行榜 |
| `get_market_indices()` | 获取大盘指数 |
| `get_precious_metals()` | 获取贵金属/原油行情 |
| `send_wechat_push(title, content)` | 发送微信推送 |
| `send_alert_push(alerts)` | 发送预警推送 |
| `PortfolioManager` | 持仓管理器 |
| `AlertManager` | 预警管理器 |

## 功能模块

### Web界面标签页（9个）

1. **📊 实时监控** - 实时估值、今日盈亏、持仓盈亏、涨跌柱状图
2. **📈 大盘指数** - 上证、深证、创业板等主要指数实时行情
3. **🥇 贵金属/原油** - 沪金、沪银、原油期货实时行情及历史走势
4. **📅 收益日历** - 日历形式展示每日盈亏，月度统计
5. **➕ 添加持仓** - 支持份额/成本价 或 金额/收益率两种方式
6. **🔍 基金搜索** - 按名称或代码搜索基金
7. **🏆 基金排行** - 各类型基金收益排行榜
8. **📈 数据分析** - 持仓饼图、收益率柱状图、分类分析
9. **📜 历史记录** - 每日收益走势、交易记录

### 微信推送功能

使用 PushPlus 进行微信推送（在 `.env` 文件中配置）：

| 方式 | 免费额度 | 实名要求 | 获取地址 |
|-----|---------|---------|---------|
| PushPlus | 200条/天 | 需要 | https://www.pushplus.plus/ |

**配置步骤：**

```bash
# 1. 复制示例配置
cp .env.example .env

# 2. 编辑 .env 文件，填入你的 Token
PUSHPLUS_TOKEN=你的Token
```

**推送场景：**

- 预警触发时自动推送（涨跌幅超过阈值）
- 支持测试推送（侧边栏设置页面）
- 同一基金5分钟内不重复推送（防刷屏）

### 核心类使用示例

```python
from fund_core import PortfolioManager, AlertManager, get_fund_data, validate_fund_code, send_wechat_push

# 验证基金代码
if validate_fund_code("161226"):
    print("有效的基金代码")

# 持仓管理器
pm = PortfolioManager()
pm.add_fund(code, name, shares, cost_price, category)
pm.calculate_profit(code, current_nav)
pm.record_daily_snapshot(df)
pm.export_to_excel(filepath, df)

# 预警管理器（自动推送）
alert_mgr = AlertManager()
alert_mgr.set_thresholds(up=3.0, down=-3.0)
alerts = alert_mgr.check_alerts(df, auto_push=True)  # 自动推送

# 手动推送
send_wechat_push("标题", "<h3>内容</h3>")

# 获取基金数据
df = get_fund_data(["161226", "017641"])
```

### 数据流

```
用户持仓 (fund_portfolio_v2.json)
    ↓
get_fund_data() - 并发获取 + 多数据源降级
    ↓
    ├── 天天基金估值（普通基金）
    ├── 期货价格估算（商品期货基金）
    └── 历史净值（兜底）
    ↓
PortfolioManager.calculate_profit() - 计算收益
    ↓
AlertManager.check_alerts() - 检查预警 → 自动推送微信
    ↓
展示结果 + 图表可视化 (Plotly)
    ↓
record_daily_snapshot() - 记录历史
```

## 配置说明

### 环境变量配置 (.env)

```bash
# PushPlus 配置（需实名）
PUSHPLUS_TOKEN=你的Token
```

### config.py 配置项

```python
# 版本信息
VERSION = "2.1.0"

# 网络配置
REQUEST_TIMEOUT = 3       # 请求超时（秒）
MAX_WORKERS = 5           # 并发请求数
CACHE_TTL = 55            # 缓存有效期（秒）

# 历史记录配置
MAX_TRANSACTION_RECORDS = 500   # 交易记录最大保留条数
MAX_DAILY_HISTORY_DAYS = 365    # 每日快照最大保留天数

# 预警默认配置
DEFAULT_ALERT_UP = 3.0    # 默认涨幅预警阈值
DEFAULT_ALERT_DOWN = -3.0 # 默认跌幅预警阈值

# 推送配置
PUSH_ENABLED = True       # 推送总开关
PUSH_ON_ALERT = True      # 预警时推送
PUSH_INTERVAL = 300       # 推送间隔（秒），防止刷屏

# 商品期货基金映射（用于实时估值计算）
COMMODITY_FUND_MAP = {
    '161226': {'name': '国投瑞银白银期货(LOF)A', 'commodity': 'AG0', 'commodity_name': '沪银'},
    '518880': {'name': '华安黄金ETF', 'commodity': 'AU0', 'commodity_name': '沪金'},
    # ...
}
```

## 技术特性

- **类型提示** - 核心函数使用 Python typing 模块
- **线程安全** - 缓存和推送记录使用 `threading.Lock` 保护
- **输入验证** - `validate_fund_code()` 验证基金代码格式
- **多数据源降级** - 自动切换数据源，保证数据可用性
- **内存缓存** - 55秒 TTL 缓存，减少重复请求
- **并发请求** - ThreadPoolExecutor 并发获取数据
- **环境变量** - 敏感信息通过 `.env` 文件管理，不上传到 GitHub

## 注意事项

- 涨跌幅颜色遵循 A 股习惯：**红色上涨，绿色下跌**
- 天天基金接口需要设置正确的 `Referer` 和 `User-Agent` 头
- 商品期货基金（如白银LOF）无法获取盘中估值，使用期货价格估算
- 非交易时间部分数据可能无法获取，会自动降级到历史净值
- 交易记录和每日快照会自动清理，防止文件无限增长
- 导出 Excel 需要安装 `openpyxl`
- 日志级别可通过 `config.py` 的 `LOG_LEVEL` 调整
- `.env` 文件包含敏感信息，已在 `.gitignore` 中，不会上传到 GitHub
