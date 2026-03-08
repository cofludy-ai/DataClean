"""
东方财富直接 API 数据获取器
直接调用东方财富 API，避免第三方库网络问题
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)


class EastMoneyFetcher:
    """东方财富数据获取器"""

    def __init__(self, request_interval: float = 0.5):
        self.request_interval = request_interval
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        })

    def _safe_request(self, url: str, params: dict = None, max_retries: int = 3):
        """安全请求"""
        for attempt in range(max_retries):
            try:
                time.sleep(self.request_interval)
                resp = self.session.get(url, params=params, timeout=15)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise

    def fetch_kline(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            stock_code: 股票代码 (如 '600519')
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            
        Returns:
            DataFrame
        """
        # 转换日期格式
        start = self._convert_date(start_date)
        end = self._convert_date(end_date)
        
        return self._fetch_kline_impl(stock_code, start, end)
    
    def fetch_daily(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取日线数据（fetch_kline 的别名）
        
        Args:
            stock_code: 股票代码 (如 '600519')
            start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
            end_date: 结束日期 (YYYYMMDD 或 YYYY-MM-DD)
            
        Returns:
            DataFrame
        """
        # 转换日期格式
        start = self._convert_date(start_date)
        end = self._convert_date(end_date)
        
        return self._fetch_kline_impl(stock_code, start, end)
    
    def _convert_date(self, date_str: str) -> str:
        """转换日期格式为 YYYYMMDD"""
        if "-" in date_str:
            return date_str.replace("-", "")
        return date_str
    
    def _fetch_kline_impl(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        # 判断市场代码
        if stock_code.startswith('6'):
            secid = f"1.{stock_code}"  # 上海
        elif stock_code.startswith(('0', '3')):
            secid = f"0.{stock_code}"  # 深圳
        elif stock_code.startswith('8') or stock_code.startswith('4'):
            secid = f"0.{stock_code}"  # 北京
        else:
            secid = f"1.{stock_code}"
        
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        
        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",  # 日K
            "fqt": "1",    # 前复权
            "beg": start_date,
            "end": end_date,
            "lmt": "1000000"
        }
        
        logger.info(f"获取 {stock_code} K线数据: {start_date} - {end_date}")
        
        try:
            data = self._safe_request(url, params)
            
            if data.get('data') is None:
                logger.warning(f"未获取到 {stock_code} 的数据")
                return pd.DataFrame()
            
            klines = data['data']['klines']
            
            if not klines:
                logger.warning(f"获取到空数据: {stock_code}")
                return pd.DataFrame()
            
            # 解析数据
            records = []
            for kline in klines:
                parts = kline.split(',')
                records.append({
                    'date': parts[0],
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'volume': int(parts[5]),
                    'amount': float(parts[6]) if parts[6] else 0,
                    'amplitude': float(parts[7]) if parts[7] else 0,
                    'change_pct': float(parts[8]) if parts[8] else 0,
                    'change': float(parts[9]) if parts[9] else 0,
                    'turnover': float(parts[10]) if parts[10] else 0,
                    'stock_code': stock_code
                })
            
            df = pd.DataFrame(records)
            
            logger.info(f"成功获取 {stock_code}: {len(df)} 条数据")
            return df
            
        except Exception as e:
            logger.error(f"获取 {stock_code} 失败: {e}")
            return pd.DataFrame()

    def get_realtime_quote(self, stock_code: str) -> dict:
        """获取实时行情"""
        if stock_code.startswith('6'):
            secid = f"1.{stock_code}"
        else:
            secid = f"0.{stock_code}"
        
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": secid,
            "fields": "f57,f58,f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f59,f60,f116,f117,f162,f167,f168,f169,f170,f171,f173,f177"
        }
        
        try:
            data = self._safe_request(url, params)
            if data.get('data'):
                return data['data']
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
        return {}

    def get_stock_list(self) -> list:
        """获取A股股票列表"""
        import pandas as pd
        
        # 方法1: 使用 AkShare
        try:
            import akshare as ak
            df = ak.stock_info_a_code_name()
            return df['code'].tolist() if 'code' in df.columns else []
        except Exception as e:
            logger.warning(f"AkShare获取失败: {e}")
        
        # 方法2: 直接从东方财富获取
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "fltt": "2",
                "fields": "f12,f13,f14",
                "secids": "1.000001,0.399001"
            }
            # 这个接口只能获取少量测试数据
            
            # 使用另一个接口获取全部股票
            url2 = "https://61.129.115.115/api/ul/qt/clist/get"
            params2 = {
                "pn": 1,
                "pz": 5000,
                "po": 1,
                "np": 1,
                "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": 2,
                "invt": 2,
                "fid": "f3",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            }
            
            data = self._safe_request(url2, params2)
            if data and data.get('data'):
                stocks = data['data']['diff']
                return [str(s['f12']) for s in stocks]
        except Exception as e:
            logger.error(f"东方财富API获取失败: {e}")
        
        return []
