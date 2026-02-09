"""
财经数据 API 服务
包含黄金历史和新闻资讯接口
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import asyncio
import threading
import requests
import logging

# 添加父目录到路径，这样能导入 fund_core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fund_core import (
    get_gold_history,
    get_stock_news,
    get_financial_news,
    get_cctv_news,
    get_financial_headlines,
    get_fastbull_news,
    get_fund_daily_ranking
)
import pandas as pd
import numpy as np
from config import VERSION

# 配置日志
logger = logging.getLogger(__name__)

app = FastAPI(
    title="财经数据 API 服务",
    description="提供黄金历史价格和多种新闻资讯数据接口",
    version=VERSION
)

# 允许跨域（让C#/浏览器都能调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 保活机制 ==========
# 你的 Render 服务 URL（部署后修改为你的实际 URL）
KEEP_ALIVE_URL = "https://fund-monitor-api.onrender.com"
KEEP_ALIVE_INTERVAL = 300  # 5分钟（300秒）


def self_ping_worker():
    """
    后台线程：定时请求自己的 /ping 端点，防止 Render 空闲关机
    每 5 分钟自动 ping 一次
    """
    logger.info(f"🔄 保活线程已启动，每 {KEEP_ALIVE_INTERVAL} 秒 ping 一次")

    while True:
        try:
            threading.Event().wait(KEEP_ALIVE_INTERVAL)
            response = requests.get(f"{KEEP_ALIVE_URL}/ping", timeout=10)
            logger.info(f"[保活] Ping 状态: {response.status_code}")
        except Exception as e:
            logger.warning(f"[保活] Ping 失败: {e}")


@app.on_event("startup")
async def startup_event():
    """应用启动时触发"""
    # 启动后台保活线程
    keep_alive_thread = threading.Thread(target=self_ping_worker, daemon=True)
    keep_alive_thread.start()
    logger.info(f"✅ 保活机制已启用，每 {KEEP_ALIVE_INTERVAL} 秒 ping {KEEP_ALIVE_URL}/ping")


# ========== 数据模型 ==========
class GoldPrice(BaseModel):
    """黄金价格数据模型"""
    date: str                     # 日期
    close: Optional[float] = None  # 收盘价
    open: Optional[float] = None   # 开盘价
    high: Optional[float] = None   # 最高价
    low: Optional[float] = None    # 最低价
    volume: Optional[int] = None   # 成交量


class FundRanking(BaseModel):
    """基金排行数据模型"""
    code: str                              # 基金代码
    name: str                              # 基金名称
    net_value: Optional[float] = None      # 单位净值
    accumulated_net_value: Optional[float] = None  # 累计净值
    daily_growth_rate: Optional[float] = None      # 日增长率(%)


# ========== 接口 ==========
@app.get("/")
async def root():
    """根路径 - 服务状态"""
    return {
        "service": "Project A 数据服务",
        "version": "0.2.0",
        "status": "running",
        "endpoints": {
            "国内黄金历史": "/api/gold/history?days=30",
            "基金涨跌幅排行": "/api/fund/ranking?limit=100",
            "个股新闻": "/api/news/stock?symbol=600519",
            "财经快讯": "/api/news/financial",
            "财新头条": "/api/news/headlines",
            "FastBull快讯": "/api/news/fastbull",
            "央视新闻": "/api/news/cctv",
            "健康检查": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "fund-monitor-api"}


@app.get("/ping")
async def ping():
    """
    保活端点 - 用于外部服务定时 ping 防止 Render 空闲关机

    使用方法：
    - 设置 UptimeRobot 或 cron-job.org 定时访问此端点
    - 建议间隔：5-10 分钟
    - 示例：https://你的服务名.onrender.com/ping
    """
    return {
        "status": "ok",
        "message": "pong",
        "timestamp": pd.Timestamp.now().isoformat()
    }


@app.get("/api/gold/history")
async def get_gold_history_endpoint(days: int = 30):
    """
    获取黄金历史价格

    参数:
        days: 获取天数 (默认30天，最大720天)

    返回:
        {
            "success": true,
            "data": [...],
            "count": 30
        }
    """
    try:
        # 限制最大天数
        days = min(days, 720)

        # 调用 fund_core 中的函数
        df = get_gold_history(days)

        if df.empty:
            return {
                "success": False,
                "message": "暂无数据",
                "data": [],
                "count": 0
            }

        # 转换DataFrame为JSON
        data_list = []
        for _, row in df.iterrows():
            item = {
                "date": str(row.get('date', '')),
                "close": float(row.get('close', 0)) if 'close' in row and pd.notna(row.get('close')) else None,
                "open": float(row.get('open', 0)) if 'open' in row and pd.notna(row.get('open')) else None,
                "high": float(row.get('high', 0)) if 'high' in row and pd.notna(row.get('high')) else None,
                "low": float(row.get('low', 0)) if 'low' in row and pd.notna(row.get('low')) else None,
                "volume": int(row.get('volume', 0)) if 'volume' in row and pd.notna(row.get('volume')) else None
            }
            data_list.append(item)

        return {
            "success": True,
            "data": data_list,
            "count": len(data_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


# ========== 基金数据接口 ==========
@app.get("/api/fund/ranking")
async def get_fund_ranking_endpoint(limit: int = 100, symbol: str = "全部"):
    """
    获取所有基金当日涨跌幅排行

    参数:
        limit: 返回数量限制（默认100只基金，最大500）
        symbol: 基金类型（默认"全部"）
                可选: "股票型", "混合型", "债券型", "指数型", "QDII", "FOF"

    返回:
        {
            "success": true,
            "data": [...],
            "count": 100
        }

    数据说明:
        - code: 基金代码
        - name: 基金名称
        - net_value: 单位净值
        - accumulated_net_value: 累计净值
        - daily_growth_rate: 日增长率(%)

    性能说明:
        - 全部基金: ~4秒
        - 股票型: ~1.5秒
        - 混合型/债券型: 更快
    """
    try:
        # 限制最大返回数量
        limit = min(limit, 500)

        # 调用 fund_core 中的函数
        df = get_fund_daily_ranking(limit=limit, symbol=symbol)

        if df.empty:
            return {
                "success": False,
                "message": "暂无数据",
                "data": [],
                "count": 0
            }

        # 转换DataFrame为JSON
        data_list = []
        for _, row in df.iterrows():
            item = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    item[col] = None
                elif isinstance(val, (pd.Timestamp, np.datetime64)):
                    item[col] = str(val)
                elif isinstance(val, (np.integer, np.floating)):
                    item[col] = float(val)
                else:
                    item[col] = val
            data_list.append(item)

        return {
            "success": True,
            "data": data_list,
            "count": len(data_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取基金排行失败: {str(e)}")


# ========== 新闻资讯接口 ==========
@app.get("/api/news/stock")
async def get_stock_news_endpoint(symbol: str, limit: int = 10):
    """
    获取个股/基金相关新闻

    参数:
        symbol: 股票/基金代码（如：600519）
        limit: 返回数量限制（默认10条）

    返回:
        {
            "success": true,
            "news": [...],
            "count": 10
        }
    """
    try:
        df = get_stock_news(stock_codes=[symbol], limit=limit)

        if df.empty:
            return {
                "success": False,
                "message": f"未找到 {symbol} 的新闻",
                "news": [],
                "count": 0
            }

        # 安全转换JSON
        news_list = []
        for _, row in df.iterrows():
            item = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    item[col] = None
                elif isinstance(val, (pd.Timestamp, np.datetime64)):
                    item[col] = str(val)
                else:
                    item[col] = val
            news_list.append(item)

        return {
            "success": True,
            "news": news_list,
            "count": len(news_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")


@app.get("/api/news/financial")
async def get_financial_news_endpoint(symbol: str = "全部", limit: int = 50):
    """
    获取期货/商品新闻快讯（上海有色网）

    参数:
        symbol: 品种符号（默认"全部"）
                可选: 重要, VIP, 贵金属, 铜, 铝, 铅, 锌, 镍, 锡
        limit: 返回数量限制（默认50条）

    返回:
        {
            "success": true,
            "news": [...],
            "count": 50
        }
    """
    try:
        df = get_financial_news(symbol=symbol, limit=limit)

        if df.empty:
            return {
                "success": False,
                "message": "暂无新闻",
                "news": [],
                "count": 0
            }

        # 安全转换JSON
        news_list = []
        for _, row in df.iterrows():
            item = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    item[col] = None
                elif isinstance(val, (pd.Timestamp, np.datetime64)):
                    item[col] = str(val)
                else:
                    item[col] = val
            news_list.append(item)

        return {
            "success": True,
            "news": news_list,
            "count": len(news_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")


@app.get("/api/news/headlines")
async def get_financial_headlines_endpoint():
    """
    获取财新网主要财经头条

    返回:
        {
            "success": true,
            "news": [...],
            "count": 100
        }
    """
    try:
        df = get_financial_headlines()

        if df.empty:
            return {
                "success": False,
                "message": "暂无头条",
                "news": [],
                "count": 0
            }

        # 安全转换JSON
        news_list = []
        for _, row in df.iterrows():
            item = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    item[col] = None
                elif isinstance(val, (pd.Timestamp, np.datetime64)):
                    item[col] = str(val)
                else:
                    item[col] = val
            news_list.append(item)

        return {
            "success": True,
            "news": news_list,
            "count": len(news_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取头条失败: {str(e)}")


@app.get("/api/news/fastbull")
async def get_fastbull_news_endpoint(limit: int = 20):
    """
    获取 FastBull 实时财经快讯

    参数:
        limit: 返回数量限制（默认20条）

    返回:
        {
            "success": true,
            "news": [...],
            "count": 20
        }
    """
    try:
        df = get_fastbull_news(limit=limit)

        if df.empty:
            return {
                "success": False,
                "message": "暂无快讯",
                "news": [],
                "count": 0
            }

        # 安全转换JSON
        news_list = []
        for _, row in df.iterrows():
            item = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    item[col] = None
                elif isinstance(val, (pd.Timestamp, np.datetime64)):
                    item[col] = str(val)
                else:
                    item[col] = val
            news_list.append(item)

        return {
            "success": True,
            "news": news_list,
            "count": len(news_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取快讯失败: {str(e)}")


@app.get("/api/news/cctv")
async def get_cctv_news_endpoint(date: Optional[str] = None):
    """
    获取央视新闻联播文字稿

    参数:
        date: 日期，格式: YYYYMMDD（可选，默认今天）

    返回:
        {
            "success": true,
            "news": [...],
            "count": 10,
            "date": "20260208"
        }
    """
    try:
        df = get_cctv_news(date=date)

        if df.empty:
            return {
                "success": False,
                "message": "暂无新闻",
                "news": [],
                "count": 0,
                "date": date or ""
            }

        # 安全转换JSON
        news_list = []
        for _, row in df.iterrows():
            item = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    item[col] = None
                elif isinstance(val, (pd.Timestamp, np.datetime64)):
                    item[col] = str(val)
                else:
                    item[col] = val
            news_list.append(item)

        return {
            "success": True,
            "news": news_list,
            "count": len(news_list),
            "date": date or ""
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import sys
    import io

    # 设置标准输出编码为 UTF-8
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    print("=" * 60)
    print("API 服务启动中...")
    print(f"API地址: http://localhost:5000")
    print(f"文档地址: http://localhost:5000/docs")
    print(f"基金排行接口: http://localhost:5000/api/fund/ranking")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=5000)
