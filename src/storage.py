"""
本地数据存储模块
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

        # 创建目录
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.clean_dir.mkdir(parents=True, exist_ok=True)

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
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
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
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        elif format == "parquet":
            df.to_parquet(filepath, index=False)
        elif format == "json":
            df.to_json(filepath, orient='records', force_ascii=False, indent=2)

        logger.info(f"清洗数据已保存: {filepath}")
        return str(filepath)

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
