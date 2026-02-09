"""
数据获取核心模块
提供统一的数据获取接口，支持黄金历史和新闻资讯
"""
import requests
import logging
import akshare as ak
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List, Any

# 导入配置
from config import (
    REQUEST_TIMEOUT,
    MAX_WORKERS,
    LOG_LEVEL,
    LOG_FORMAT,
)

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


# ==================== 黄金历史数据 ====================

def get_gold_history(days: int = 30) -> pd.DataFrame:
    """
    获取黄金历史价格

    参数:
        days: int, 获取天数

    返回:
        DataFrame
    """
    try:
        df = ak.spot_hist_sge(symbol='Au99.99')
        if df is not None and not df.empty:
            df = df.tail(days).copy()
            df['date'] = pd.to_datetime(df['date'])
            return df
    except Exception as e:
        logger.warning(f"获取黄金历史价格失败: {e}")

    return pd.DataFrame()


# ==================== 基金数据 ====================

def get_fund_daily_ranking(limit: int = 100) -> pd.DataFrame:
    """
    获取所有基金当日涨跌幅排行

    参数:
        limit: 返回数量限制（默认100只基金）

    返回:
        DataFrame: 基金实时数据，包含字段:
        - code: 基金代码
        - name: 基金名称
        - net_value: 最新净值
        - accumulated_net_value: 累计净值
        - daily_growth_rate: 日增长率(%)
        - date: 净值日期
    """
    try:
        logger.info(f"正在获取基金实时排行数据")

        # 使用 akshare 获取场外基金实时估值
        df = ak.fund_open_fund_daily_em()

        if df is not None and not df.empty:
            # 重命名列，统一命名规范
            column_mapping = {
                '基金代码': 'code',
                '基金简称': 'name',
                '单位净值': 'net_value',
                '累计净值': 'accumulated_net_value',
                '日增长率': 'daily_growth_rate',
                '净值日期': 'date'
            }

            # 只保留需要的列
            existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df[list(existing_columns.keys())].rename(columns=existing_columns)

            # 按日增长率排序（涨的在前）
            df = df.sort_values('daily_growth_rate', ascending=False)

            # 限制返回数量
            df = df.head(limit)

            # 清洗数据：去除百分号，转换为数值
            if 'daily_growth_rate' in df.columns:
                df['daily_growth_rate'] = df['daily_growth_rate'].replace('%', '', regex=True)
                df['daily_growth_rate'] = pd.to_numeric(df['daily_growth_rate'], errors='coerce')

            logger.info(f"成功获取 {len(df)} 只基金数据")
            return df

    except Exception as e:
        logger.warning(f"获取基金排行失败: {e}")

    return pd.DataFrame()


# ==================== 新闻资讯 ====================

def get_stock_news(stock_codes: List[str], limit: int = 100) -> pd.DataFrame:
    """
    获取个股/基金相关新闻（东方财富）

    参数:
        stock_codes: 股票/基金代码列表
        limit: 每个代码获取的新闻数量限制

    返回:
        DataFrame: 新闻数据
    """
    all_news = []

    def fetch_single_news(code: str) -> Optional[List[Dict[str, Any]]]:
        """获取单个代码的新闻"""
        try:
            df = ak.stock_news_em(symbol=code)
            if df is not None and not df.empty:
                # 重命名列
                df = df.rename(columns={
                    '关键词': 'code',
                    '新闻标题': 'title',
                    '新闻内容': 'content',
                    '发布时间': 'publish_time',
                    '文章来源': 'source',
                    '新闻链接': 'url'
                })
                return df.head(limit).to_dict('records')
        except Exception as e:
            logger.debug(f"获取 {code} 新闻失败: {e}")
        return []

    # 并发获取
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_single_news, code): code for code in stock_codes}
        for future in as_completed(futures):
            news_list = future.result()
            if news_list:
                all_news.extend(news_list)

    if all_news:
        df = pd.DataFrame(all_news)
        # 解析时间并排序
        df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce')
        df = df.sort_values('publish_time', ascending=False)
        logger.info(f"获取 {len(df)} 条新闻")
        return df

    return pd.DataFrame()


def get_financial_news(symbol: str = "全部", limit: int = 50) -> pd.DataFrame:
    """
    获取期货/商品新闻快讯（上海有色网）

    参数:
        symbol: 品种符号，可选: 全部, 重要, VIP, 贵金属, 铜, 铝, 铅, 锌, 镍, 锡
        limit: 返回数量限制

    返回:
        DataFrame: 新闻快讯
    """
    try:
        df = ak.futures_news_shmet(symbol=symbol)
        if df is not None and not df.empty:
            df = df.head(limit)
            logger.info(f"获取 {len(df)} 条财经快讯")
            return df
    except Exception as e:
        logger.warning(f"获取财经快讯失败: {e}")

    return pd.DataFrame()


def get_cctv_news(date: Optional[str] = None) -> pd.DataFrame:
    """
    获取央视新闻联播文字稿

    参数:
        date: 日期，格式: YYYYMMDD，目前最早支持 20160203

    返回:
        DataFrame: 新闻联播内容
    """
    if date is None:
        date = datetime.now().strftime('%Y%m%d')

    try:
        df = ak.news_cctv(date=date)
        if df is not None and not df.empty:
            logger.info(f"获取 {date} 央视新闻 {len(df)} 条")
            return df
    except Exception as e:
        logger.warning(f"获取央视新闻失败: {e}")

    return pd.DataFrame()


def get_financial_headlines() -> pd.DataFrame:
    """
    获取财新网主要新闻

    返回:
        DataFrame: 财经头条
    """
    try:
        df = ak.stock_news_main_cx()
        if df is not None and not df.empty:
            logger.info(f"获取财新头条 {len(df)} 条")
            return df
    except Exception as e:
        logger.warning(f"获取财新头条失败: {e}")

    return pd.DataFrame()


def get_fastbull_news(limit: int = 100) -> pd.DataFrame:
    """
    获取 FastBull 实时财经快讯

    数据源: https://www.fastbull.com/cn/express-news
    参考实现: RSSHub (https://github.com/DIYgod/RSSHub)

    参数:
        limit: 返回数量限制

    返回:
        DataFrame: 快讯数据，包含字段:
        - title: 标题
        - link: 链接
        - pub_date: 发布时间
        - publish_time: 格式化时间
        - source: 来源
    """
    root_url = 'https://www.fastbull.com'
    current_url = f'{root_url}/express-news'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.fastbull.com/',
    }

    try:
        logger.info(f"正在获取 FastBull 快讯")

        response = requests.get(current_url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        response.encoding = 'utf-8'

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.select('.news-list')

        logger.info(f"找到 {len(news_items)} 条快讯")

        news_list = []
        for item in news_items[:limit]:
            try:
                # 提取标题
                title_elem = item.select_one('.title_name')
                title = title_elem.text.strip() if title_elem else '无标题'

                # 提取链接
                link_elem = item.select_one('.title_name')
                link = link_elem.get('href', '') if link_elem else ''
                if link and not link.startswith('http'):
                    link = f'{root_url}{link}'

                # 提取时间戳（毫秒）
                data_date = item.get('data-date', '')
                if data_date:
                    try:
                        timestamp = int(data_date) / 1000
                        pub_date = pd.to_datetime(timestamp, unit='s')
                    except:
                        pub_date = pd.Timestamp.now()
                else:
                    pub_date = pd.Timestamp.now()

                news_list.append({
                    'title': title,
                    'link': link,
                    'pub_date': pub_date,
                    'publish_time': pub_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'FastBull'
                })

            except Exception as e:
                logger.debug(f"解析单条快讯失败: {e}")
                continue

        if news_list:
            df = pd.DataFrame(news_list)
            df = df.sort_values('pub_date', ascending=False)
            logger.info(f"成功获取 {len(df)} 条 FastBull 快讯")
            return df

        return pd.DataFrame()

    except requests.RequestException as e:
        logger.warning(f"FastBull 请求失败: {e}")
        return pd.DataFrame()
    except ImportError:
        logger.warning("beautifulsoup4 未安装，使用 pip install beautifulsoup4")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"FastBull 解析失败: {e}")
        return pd.DataFrame()
