"""
数据查询模块
提供数据切片和查询接口
"""
import pandas as pd
import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DataQuery:
    """数据查询接口"""

    def __init__(self, master_file: str = "data/master/all_stocks.csv"):
        """
        初始化
        
        Args:
            master_file: 主数据文件路径
        """
        self.master_file = master_file
        self._df = None
        logger.info(f"数据查询初始化: {master_file}")

    def load(self) -> pd.DataFrame:
        """加载主数据文件"""
        if self._df is None:
            try:
                self._df = pd.read_csv(self.master_file)
                logger.info(f"加载数据: {len(self._df)} 条记录")
            except FileNotFoundError:
                logger.warning(f"文件不存在: {self.master_file}")
                self._df = pd.DataFrame()
        return self._df

    def reload(self):
        """重新加载数据"""
        self._df = None
        return self.load()

    def query(
        self,
        stock_codes: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        查询数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 返回数量限制
            columns: 返回的列名
            
        Returns:
            查询结果 DataFrame
        """
        df = self.load()
        
        if df.empty:
            return df

        # 转换 stock_code 为字符串类型（兼容存储时为 int 的情况）
        df['stock_code'] = df['stock_code'].astype(str)
        
        # 按股票代码筛选
        if stock_codes:
            stock_codes = [str(code) for code in stock_codes]
            df = df[df['stock_code'].isin(stock_codes)]
            logger.info(f"按股票代码筛选: {len(df)} 条")

        # 按开始日期筛选
        if start_date:
            df = df[df['date'] >= start_date]
            logger.info(f"按开始日期筛选: {len(df)} 条")

        # 按结束日期筛选
        if end_date:
            df = df[df['date'] <= end_date]
            logger.info(f"按结束日期筛选: {len(df)} 条")

        # 排序
        df = df.sort_values(['stock_code', 'date'])

        # 数量限制
        if limit:
            df = df.head(limit)
            logger.info(f"限制数量: {len(df)} 条")

        # 列选择
        if columns:
            available_cols = [c for c in columns if c in df.columns]
            df = df[available_cols]

        return df

    def get_latest(self, stock_code: str, n: int = 1) -> pd.DataFrame:
        """
        获取某股票最近 N 天数据
        
        Args:
            stock_code: 股票代码
            n: 天数
            
        Returns:
            DataFrame
        """
        df = self.load()
        if df.empty:
            return df
        
        # 转换 stock_code 为字符串
        df['stock_code'] = df['stock_code'].astype(str)
        stock_code = str(stock_code)
        
        df = df[df['stock_code'] == stock_code]
        df = df.sort_values('date', ascending=False)
        return df.head(n)

    def get_stock_list(self) -> List[str]:
        """获取所有股票代码列表"""
        df = self.load()
        if df.empty:
            return []
        df['stock_code'] = df['stock_code'].astype(str)
        return df['stock_code'].unique().tolist()

    def get_date_range(self) -> tuple:
        """获取数据日期范围"""
        df = self.load()
        if df.empty:
            return None, None
        return df['date'].min(), df['date'].max()

    def get_statistics(self) -> dict:
        """获取数据统计信息"""
        df = self.load()
        if df.empty:
            return {}
        
        return {
            'total_records': len(df),
            'stock_count': df['stock_code'].nunique(),
            'date_range': f"{df['date'].min()} ~ {df['date'].max()}",
            'columns': df.columns.tolist()
        }
