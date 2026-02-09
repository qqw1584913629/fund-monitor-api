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
    date: Optional[str] = None             # 净值日期


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
    return {"status": "healthy"}


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
async def get_fund_ranking_endpoint(limit: int = 100):
    """
    获取所有基金当日涨跌幅排行

    参数:
        limit: 返回数量限制（默认100只基金）

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
        - date: 净值日期
    """
    try:
        # 限制最大返回数量
        limit = min(limit, 500)

        # 调用 fund_core 中的函数
        df = get_fund_daily_ranking(limit=limit)

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
