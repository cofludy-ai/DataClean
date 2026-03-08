"""
本地数据存储模块
支持增量合并和主数据文件管理
"""
import os
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DataStorage:
    """本地数据存储"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化

        Args:
            data_dir: 数据目录根路径
        """
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.clean_dir = self.data_dir / "clean"
        self.master_dir = self.data_dir / "master"

        # 创建目录
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.clean_dir.mkdir(parents=True, exist_ok=True)
        self.master_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"数据存储初始化: {self.data_dir}")

    def save_raw(self, df: pd.DataFrame, stock_code: str, format: str = "csv") -> str:
        """
        保存原始数据

        Args:
            df: 数据
            stock_code: 股票代码
            format: 保存格式 (csv, parquet, json)

        Returns:
            保存的文件路径
        """
        filename = f"{stock_code}_raw.{format}"
        filepath = self.raw_dir / filename

        if format == "csv":
            df.to_csv(filepath, index=False, encoding='utf-8')
        elif format == "parquet":
            df.to_parquet(filepath, index=False)
        elif format == "json":
            df.to_json(filepath, orient='records', force_ascii=False, indent=2)

        logger.info(f"原始数据已保存: {filepath}")
        return str(filepath)

    def save_clean(self, df: pd.DataFrame, stock_code: str, format: str = "csv") -> str:
        """
        保存清洗后数据

        Args:
            df: 数据
            stock_code: 股票代码
            format: 保存格式 (csv, parquet, json)

        Returns:
            保存的文件路径
        """
        filename = f"{stock_code}_clean.{format}"
        filepath = self.clean_dir / filename

        if format == "csv":
            df.to_csv(filepath, index=False, encoding='utf-8')
        elif format == "parquet":
            df.to_parquet(filepath, index=False)
        elif format == "json":
            df.to_json(filepath, orient='records', force_ascii=False, indent=2)

        logger.info(f"清洗数据已保存: {filepath}")
        return str(filepath)

    def save_master(self, df: pd.DataFrame, filename: str = "all_stocks.csv", format: str = "csv") -> str:
        """
        保存主数据文件（合并所有股票）

        Args:
            df: 数据
            filename: 文件名
            format: 保存格式

        Returns:
            保存的文件路径
        """
        filepath = self.master_dir / filename

        if format == "csv":
            df.to_csv(filepath, index=False, encoding='utf-8')
        elif format == "parquet":
            df.to_parquet(filepath, index=False)
        elif format == "json":
            df.to_json(filepath, orient='records', force_ascii=False, indent=2)

        logger.info(f"主数据文件已保存: {filepath}")
        return str(filepath)

    def load_master(self, filename: str = "all_stocks.csv", format: str = "csv") -> pd.DataFrame:
        """
        加载主数据文件

        Args:
            filename: 文件名
            format: 文件格式

        Returns:
            DataFrame
        """
        filepath = self.master_dir / filename

        if not filepath.exists():
            logger.info(f"主数据文件不存在: {filepath}")
            return pd.DataFrame()

        if format == "csv":
            return pd.read_csv(filepath)
        elif format == "parquet":
            return pd.read_parquet(filepath)
        elif format == "json":
            return pd.read_json(filepath)

    def merge_incremental(self, df_new: pd.DataFrame, filename: str = "all_stocks.csv", 
                          format: str = "csv") -> pd.DataFrame:
        """
        增量合并数据

        Args:
            df_new: 新增数据
            filename: 主数据文件名
            format: 文件格式

        Returns:
            合并后的 DataFrame
        """
        if df_new.empty:
            logger.warning("新增数据为空")
            return df_new

        # 加载历史数据
        df_history = self.load_master(filename, format)

        if df_history.empty:
            logger.info("无历史数据，直接保存新增数据")
            df_merged = df_new.copy()
        else:
            logger.info(f"合并数据: 历史 {len(df_history)} 条 + 新增 {len(df_new)} 条")
            
            # 合并数据
            df_merged = pd.concat([df_history, df_new], ignore_index=True)
            
            # 去重（按 stock_code 和 date）
            df_merged = df_merged.drop_duplicates(subset=['stock_code', 'date'], keep='last')
            
            # 排序
            df_merged = df_merged.sort_values(['stock_code', 'date']).reset_index(drop=True)
            
            logger.info(f"合并后: {len(df_merged)} 条")

        # 保存
        self.save_master(df_merged, filename, format)

        return df_merged

    def load_raw(self, stock_code: str, format: str = "csv") -> pd.DataFrame:
        """加载原始数据"""
        filename = f"{stock_code}_raw.{format}"
        filepath = self.raw_dir / filename

        if not filepath.exists():
            logger.warning(f"文件不存在: {filepath}")
            return pd.DataFrame()

        if format == "csv":
            return pd.read_csv(filepath)
        elif format == "parquet":
            return pd.read_parquet(filepath)
        elif format == "json":
            return pd.read_json(filepath)

    def load_clean(self, stock_code: str, format: str = "csv") -> pd.DataFrame:
        """加载清洗后数据"""
        filename = f"{stock_code}_clean.{format}"
        filepath = self.clean_dir / filename

        if not filepath.exists():
            logger.warning(f"文件不存在: {filepath}")
            return pd.DataFrame()

        if format == "csv":
            return pd.read_csv(filepath)
        elif format == "parquet":
            return pd.read_parquet(filepath)
        elif format == "json":
            return pd.read_json(filepath)

    def list_raw_files(self) -> list:
        """列出原始数据文件"""
        return [f.name for f in self.raw_dir.iterdir() if f.is_file()]

    def list_clean_files(self) -> list:
        """列出清洗后数据文件"""
        return [f.name for f in self.clean_dir.iterdir() if f.is_file()]
