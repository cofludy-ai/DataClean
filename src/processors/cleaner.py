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

        # 1. 标准化列名
        df = self._normalize_columns(df)

        # 2. 标准化日期格式
        df = self._normalize_date(df)

        # 3. 去除重复数据
        df = self._remove_duplicates(df)

        # 4. 去除缺失值
        df = self._handle_missing_values(df)

        # 5. 数据类型转换
        df = self._convert_types(df)

        # 6. 数据校验
        df = self._validate_data(df)

        # 7. 排序
        df = df.sort_values(['股票代码', '日期']).reset_index(drop=True)

        cleaned_count = len(df)
        logger.info(f"清洗完成: {original_count} -> {cleaned_count} 条记录")

        return df

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        # 列名映射
        column_mapping = {
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
        }

        # 重命名存在的列
        for old, new in column_mapping.items():
            if old in df.columns and old != new:
                df = df.rename(columns={old: new})

        return df

    def _normalize_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化日期格式"""
        if '日期' not in df.columns:
            return df

        try:
            # 尝试解析日期
            df['日期'] = pd.to_datetime(df['日期'])
            # 统一格式为 YYYY-MM-DD
            df['日期'] = df['日期'].dt.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"日期格式转换失败: {e}")

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除重复数据"""
        if '股票代码' in df.columns and '日期' in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=['股票代码', '日期'], keep='last')
            after = len(df)
            if before > after:
                logger.info(f"去除重复数据: {before} -> {after} 条")

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        # 检查关键字段
        required_cols = ['日期', '股票代码', '开盘', '收盘', '最高', '最低']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            logger.warning(f"缺少关键列: {missing_cols}")
            return df

        # 标记缺失值
        for col in ['开盘', '收盘', '最高', '最低', '成交量', '成交额']:
            if col in df.columns:
                df[f'{col}_缺失'] = df[col].isna()

        # 删除关键字段缺失的行
        before = len(df)
        df = df.dropna(subset=['日期', '股票代码', '收盘'])
        after = len(df)

        if before > after:
            logger.info(f"删除缺失值: {before} -> {after} 条")

        return df

    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据类型转换"""
        # 数值列
        numeric_cols = ['开盘', '收盘', '最高', '最低', '成交量', '成交额',
                       '振幅', '涨跌幅', '涨跌额', '换手率']

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据校验"""
        if df.empty:
            return df

        df = df.copy()
        df['校验状态'] = '正常'

        # 1. 价格校验：最高 >= 最低
        mask = df['最高'] < df['最低']
        df.loc[mask, '校验状态'] = '异常'
        if mask.any():
            logger.warning(f"发现 {mask.sum()} 条最高价 < 最低价的异常记录")

        # 2. 价格校验：收盘价在高低价范围内
        mask = (df['收盘'] > df['最高']) | (df['收盘'] < df['最低'])
        df.loc[mask, '校验状态'] = '异常'
        if mask.any():
            logger.warning(f"发现 {mask.sum()} 条收盘价超出高低价范围的异常记录")

        # 3. 价格校验：价格应为正数
        for col in ['开盘', '收盘', '最高', '最低']:
            mask = df[col] <= 0
            df.loc[mask, '校验状态'] = '异常'
            if mask.any():
                logger.warning(f"发现 {mask.sum()} 条 {col} <= 0 的异常记录")

        # 4. 成交量校验：应为非负数
        if '成交量' in df.columns:
            mask = df['成交量'] < 0
            df.loc[mask, '校验状态'] = '异常'

        return df

    def get_statistics(self, df: pd.DataFrame) -> dict:
        """获取数据统计信息"""
        if df.empty:
            return {}

        stats = {
            '总记录数': len(df),
            '股票数量': df['股票代码'].nunique() if '股票代码' in df.columns else 0,
            '日期范围': f"{df['日期'].min()} ~ {df['日期'].max()}" if '日期' in df.columns else 'N/A',
            '异常记录数': len(df[df['校验状态'] == '异常']) if '校验状态' in df.columns else 0,
        }

        # 数值列统计
        numeric_cols = ['开盘', '收盘', '最高', '最低', '成交量', '成交额']
        for col in numeric_cols:
            if col in df.columns:
                stats[f'{col}_均值'] = df[col].mean()
                stats[f'{col}_最小值'] = df[col].min()
                stats[f'{col}_最大值'] = df[col].max()

        return stats
