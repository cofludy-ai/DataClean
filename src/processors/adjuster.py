"""
复权处理模块
使用前复权价格，确保历史价格可比性
"""
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PriceAdjuster:
    """价格复权处理器"""

    def __init__(self, method: str = "qfq"):
        """
        初始化

        Args:
            method: 复权方法
                - "qfq": 前复权（推荐，历史价格按最新复权）
                - "hfq": 后复权
        """
        self.method = method
        logger.info(f"价格复权处理器初始化: {method}")

    def adjust(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        对数据进行复权处理

        Args:
            df: 原始数据 DataFrame

        Returns:
            复权后的 DataFrame
        """
        if df.empty:
            return df

        df = df.copy()

        # 检查是否需要复权
        if '复权类型' in df.columns:
            logger.info("数据已是复权数据，跳过复权处理")
            return df

        # 注意：AkShare 的 stock_zh_a_hist 已经支持 adjust="qfq"
        # 这里可以做额外的复权验证和处理

        # 验证价格合理性
        df = self._validate_prices(df)

        return df

    def _validate_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """验证价格合理性"""
        if df.empty:
            return df

        # 确保价格列存在
        price_cols = ['开盘', '收盘', '最高', '最低']
        if not all(col in df.columns for col in price_cols):
            logger.warning("缺少价格列，跳过价格验证")
            return df

        # 标记异常价格
        df['价格异常'] = False

        # 检查：最高价 >= 最低价
        mask = df['最高'] < df['最低']
        df.loc[mask, '价格异常'] = True
        if mask.any():
            logger.warning(f"发现 {mask.sum()} 条最高价 < 最低价的异常记录")

        # 检查：收盘价应该在最高价和最低价之间（或相等）
        mask = (df['收盘'] > df['最高']) | (df['收盘'] < df['最低'])
        df.loc[mask, '价格异常'] = True
        if mask.any():
            logger.warning(f"发现 {mask.sum()} 条收盘价超出高低价范围的异常记录")

        # 检查：价格是否为正数
        for col in price_cols:
            mask = df[col] <= 0
            df.loc[mask, '价格异常'] = True
            if mask.any():
                logger.warning(f"发现 {mask.sum()} 条 {col} <= 0 的异常记录")

        return df

    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算收益率"""
        if df.empty or '收盘' not in df.columns:
            return df

        df = df.copy()

        # 按日期排序
        df = df.sort_values('日期')

        # 日收益率
        df['日收益率'] = df['收盘'].pct_change()

        # 累计收益率
        df['累计收益率'] = (1 + df['日收益率']).cumprod() - 1

        return df
