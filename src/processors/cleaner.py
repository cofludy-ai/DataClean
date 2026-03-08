"""
基础数据清洗模块
"""
import pandas as pd
import logging
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BasicCleaner:
    """基础数据清洗器"""

    def __init__(self):
        logger.info("基础数据清洗器初始化")

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        执行完整清洗流程

        Args:
            df: 原始数据 DataFrame

        Returns:
            清洗后的 DataFrame
        """
        if df.empty:
            logger.warning("输入数据为空")
            return df

        original_count = len(df)
        df = df.copy()

        # 1. 标准化列名（兼容中文）
        df = self._normalize_columns(df)

        # 2. 标准化日期格式
        df = self._normalize_date(df)

        # 3. 去除重复数据
        df = self._remove_duplicates(df)

        # 4. 数据类型转换
        df = self._convert_types(df)

        # 5. 排序
        df = df.sort_values(['stock_code', 'date']).reset_index(drop=True)

        cleaned_count = len(df)
        logger.info(f"清洗完成: {original_count} -> {cleaned_count} 条记录")

        return df

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        # 兼容中文列名
        chinese_mapping = {
            '日期': 'date',
            '股票代码': 'stock_code',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change',
            '换手率': 'turnover'
        }

        for cn, en in chinese_mapping.items():
            if cn in df.columns:
                df = df.rename(columns={cn: en})

        return df

    def _normalize_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化日期格式"""
        if 'date' not in df.columns:
            return df

        try:
            df['date'] = pd.to_datetime(df['date'])
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"日期格式转换失败: {e}")

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除重复数据"""
        if 'stock_code' in df.columns and 'date' in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=['stock_code', 'date'], keep='last')
            after = len(df)
            if before > after:
                logger.info(f"去除重复数据: {before} -> {after} 条")

        return df

    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据类型转换"""
        numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount',
                       'amplitude', 'change_pct', 'change', 'turnover']

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def get_statistics(self, df: pd.DataFrame) -> dict:
        """获取数据统计信息"""
        if df.empty:
            return {}

        stats = {
            'total_records': len(df),
            'stock_count': df['stock_code'].nunique() if 'stock_code' in df.columns else 0,
            'date_range': f"{df['date'].min()} ~ {df['date'].max()}" if 'date' in df.columns else 'N/A',
        }

        return stats
