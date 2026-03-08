"""
AkShare 数据获取器
实现基于 AkShare 库的数据获取
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import time
import logging

from .base import BaseFetcher

logger = logging.getLogger(__name__)


class AkshareFetcher(BaseFetcher):
    """AkShare 数据获取器"""

    def __init__(self, request_interval: float = 1.0):
        """
        初始化

        Args:
            request_interval: 请求间隔（秒），防止被限流
        """
        super().__init__("AkShare")
        self.request_interval = request_interval

    def _convert_date(self, date_str: str) -> str:
        """转换日期格式为 YYYYMMDD"""
        if "-" in date_str:
            return date_str.replace("-", "")
        return date_str

    def _safe_request(self, func, *args, **kwargs):
        """带重试的安全请求"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(self.request_interval)  # 请求间隔
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))  # 递增等待
                else:
                    raise

    def fetch_daily(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            stock_code: 股票代码 (e.g., '000001', '600000')
            start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
            end_date: 结束日期 (YYYYMMDD 或 YYYY-MM-DD)

        Returns:
            DataFrame with columns: 股票代码, 日期, 开盘, 收盘, 最高, 最低, 成交额, 成交量
        """
        # 转换日期格式
        start = self._convert_date(start_date)
        end = self._convert_date(end_date)

        # 判断市场
        if stock_code.startswith("6"):
            symbol = f"sh{stock_code}"
        else:
            symbol = f"sz{stock_code}"

        logger.info(f"获取 {stock_code} 日线数据: {start} - {end}")

        try:
            df = self._safe_request(
                ak.stock_zh_a_hist,
                symbol=symbol,
                start_date=start,
                end_date=end,
                adjust="qfq"  # 前复权
            )

            if df is None or df.empty:
                logger.warning(f"未获取到 {stock_code} 的数据")
                return pd.DataFrame()

            # 统一列名
            df = df.rename(columns={
                '日期': '日期',
                '股票代码': '股票代码',
                '开盘': '开盘',
                '收盘': '收盘',
                '最高': '最高',
                '最低': '最低',
                '成交量': '成交量',
                '成交额': '成交额',
                '振幅': '振幅',
                '涨跌幅': '涨跌幅',
                '涨跌额': '涨跌额',
                '换手率': '换手率'
            })

            # 确保股票代码列
            df['股票代码'] = stock_code

            return df

        except Exception as e:
            logger.error(f"获取 {stock_code} 数据失败: {e}")
            return pd.DataFrame()

    def fetch_adj_factor(self, stock_code: str) -> pd.DataFrame:
        """
        获取复权因子

        Args:
            stock_code: 股票代码

        Returns:
            DataFrame with columns: 股票代码, 日期, 复权因子
        """
        logger.info(f"获取 {stock_code} 复权因子")

        try:
            if stock_code.startswith("6"):
                symbol = f"sh{stock_code}"
            else:
                symbol = f"sz{stock_code}"

            df = self._safe_request(
                ak.stock_zh_a_hist,
                symbol=symbol,
                adjust="qfq"
            )

            if df is None or df.empty:
                return pd.DataFrame()

            # 提取日期和复权因子
            result = pd.DataFrame({
                '股票代码': stock_code,
                '日期': df['日期'],
                '复权因子': df.get('收盘', 1.0)  # 如果有复权因子列则使用
            })

            return result

        except Exception as e:
            logger.error(f"获取 {stock_code} 复权因子失败: {e}")
            return pd.DataFrame()

    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        logger.info("获取A股股票列表")

        try:
            df = self._safe_request(ak.stock_info_a_code_name)
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
