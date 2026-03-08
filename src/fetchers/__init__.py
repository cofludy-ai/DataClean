"""
数据获取器模块
"""
from .base import BaseFetcher
from .eastmoney import EastMoneyFetcher

__all__ = ['BaseFetcher', 'EastMoneyFetcher']
