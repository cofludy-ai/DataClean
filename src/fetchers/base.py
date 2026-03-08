"""
数据获取器基类
定义数据获取接口，所有数据源需继承此类
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import pandas as pd


class BaseFetcher(ABC):
    """数据获取器抽象基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
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
        pass

    @abstractmethod
    def fetch_adj_factor(self, stock_code: str) -> pd.DataFrame:
        """
        获取复权因子

        Args:
            stock_code: 股票代码

        Returns:
            DataFrame with columns: 股票代码, 日期, 复权因子
        """
        pass

    @abstractmethod
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        pass
