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
        if 'adj_type' in df.columns:
            logger.info("数据已是复权数据，跳过复权处理")
            return df

        # 注意：东方财富 API 的 kline 接口已经支持 adjust="qfq"
        # 这里可以做额外的复权验证和处理

        # 验证价格合理性
        df = self._validate_prices(df)

        return df

    def _validate_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """验证价格合理性"""
        if df.empty:
            return df

        # 确保价格列存在
        price_cols = ['open', 'close', 'high', 'low']
        if not all(col in df.columns for col in price_cols):
            logger.warning("缺少价格列，跳过价格验证")
            return df

        # 标记异常价格
        df['price_abnormal'] = False

        # 检查：high >= low
        mask = df['high'] < df['low']
        df.loc[mask, 'price_abnormal'] = True
        if mask.any():
            logger.warning(f"发现 {mask.sum()} 条 high < low 的异常记录")

        # 检查：close 应该在 high 和 low 之间（或相等）
        mask = (df['close'] > df['high']) | (df['close'] < df['low'])
        df.loc[mask, 'price_abnormal'] = True
        if mask.any():
            logger.warning(f"发现 {mask.sum()} 条 close 超出 high-low 范围的异常记录")

        # 检查：价格是否为正数
        for col in price_cols:
            mask = df[col] <= 0
            df.loc[mask, 'price_abnormal'] = True
            if mask.any():
                logger.warning(f"发现 {mask.sum()} 条 {col} <= 0 的异常记录")

        return df

    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算收益率"""
        if df.empty or 'close' not in df.columns:
            return df

        df = df.copy()

        # 按日期排序
        df = df.sort_values('date')

        # 日收益率
        df['daily_return'] = df['close'].pct_change()

        # 累计收益率
        df['cumulative_return'] = (1 + df['daily_return']).cumprod() - 1

        return df
