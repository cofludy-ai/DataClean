#!/usr/bin/env python3
"""
全量A股数据下载脚本
支持增量下载，检测已有数据后只下载新增部分
"""
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from fetchers.eastmoney import EastMoneyFetcher
from processors import BasicCleaner, PriceAdjuster
from storage import DataStorage
from query import DataQuery
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# A股全量股票代码池
def generate_stock_codes():
    """生成A股可能的股票代码"""
    codes = []
    
    # 上海主板 (600000-603999)
    for i in range(600000, 604000):
        codes.append(str(i))
    
    # 深圳主板 (000001-002999)
    for i in range(1, 3000):
        codes.append(str(i).zfill(6))
    
    # 创业板 (300000-303000)
    for i in range(300000, 303001):
        codes.append(str(i))
    
    # 科创板 (688000-688999)
    for i in range(688000, 689000):
        codes.append(str(i))
    
    return codes


def get_existing_dates(storage, stock_code):
    """获取某股票已有的日期范围"""
    clean_file = storage.clean_dir / f"{stock_code}_clean.csv"
    if clean_file.exists():
        df = pd.read_csv(clean_file)
        if not df.empty and 'date' in df.columns:
            return set(df['date'].tolist())
    return set()


def process_stock(stock_code, start_date, end_date, fetcher, storage, save_format='csv'):
    """处理单只股票"""
    # 检查已有数据
    existing_dates = get_existing_dates(storage, stock_code)
    
    # 获取数据
    try:
        df_raw = fetcher.fetch_daily(stock_code, start_date, end_date)
        
        if df_raw.empty:
            return stock_code, False, "无数据"
        
        # 检查是否需要下载（是否有新数据）
        if existing_dates:
            new_dates = set(df_raw['date'].tolist()) - existing_dates
            if not new_dates:
                return stock_code, True, "已有最新数据"
            # 只保留新数据
            df_raw = df_raw[df_raw['date'].isin(new_dates)]
            logger.info(f"{stock_code}: 新增 {len(df_raw)} 条数据")
        
        # 清洗
        adjuster = PriceAdjuster()
        cleaner = BasicCleaner()
        
        df_clean = cleaner.clean(adjuster.adjust(df_raw))
        
        # 保存
        storage.save_raw(df_raw, stock_code, save_format)
        storage.save_clean(df_clean, stock_code, save_format)
        
        return stock_code, True, f"获取 {len(df_clean)} 条"
        
    except Exception as e:
        return stock_code, False, str(e)


def download_all_stocks(
    start_date='2020-01-01',
    end_date=None,
    batch_size=50,
    max_workers=5,
    request_interval=0.3,
    data_dir='data'
):
    """
    全量下载A股数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期（默认今天）
        batch_size: 每批处理的股票数
        max_workers: 并行线程数
        request_interval: 请求间隔（秒）
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"开始下载A股数据: {start_date} ~ {end_date}")
    
    # 初始化
    fetcher = EastMoneyFetcher(request_interval=request_interval)
    storage = DataStorage(data_dir)
    
    # 生成股票代码
    all_stocks = generate_stock_codes()
    logger.info(f"待处理股票数量: {len(all_stocks)}")
    
    # 统计
    success = 0
    fail = 0
    skip = 0
    
    # 分批处理
    for batch_start in range(0, len(all_stocks), batch_size):
        batch = all_stocks[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(all_stocks) + batch_size - 1) // batch_size
        
        logger.info(f"处理批次 {batch_num}/{total_batches}: {len(batch)} 只股票")
        
        # 并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    process_stock, 
                    code, start_date, end_date, 
                    fetcher, storage
                ): code 
                for code in batch
            }
            
            for future in as_completed(futures):
                code = futures[future]
                try:
                    stock_code, ok, msg = future.result()
                    if ok:
                        if "已有最新" in msg:
                            skip += 1
                        else:
                            success += 1
                            logger.info(f"✓ {stock_code}: {msg}")
                    else:
                        fail += 1
                        logger.warning(f"✗ {stock_code}: {msg}")
                except Exception as e:
                    fail += 1
                    logger.error(f"✗ {code}: {e}")
        
        logger.info(f"批次完成: 成功 {success}, 跳过 {skip}, 失败 {fail}")
        
        # 短暂休息
        time.sleep(1)
    
    logger.info("="*50)
    logger.info(f"全量下载完成!")
    logger.info(f"成功: {success}, 跳过: {skip}, 失败: {fail}")
    logger.info("="*50)
    
    return success, skip, fail


def merge_to_master():
    """合并所有数据到主文件"""
    storage = DataStorage('data')
    clean_files = list(storage.clean_dir.glob("*_clean.csv"))
    
    logger.info(f"发现 {len(clean_files)} 个清洗后的数据文件")
    
    all_data = []
    for f in clean_files:
        df = pd.read_csv(f)
        all_data.append(df)
    
    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)
        df_all = df_all.drop_duplicates(subset=['stock_code', 'date'], keep='last')
        df_all = df_all.sort_values(['stock_code', 'date']).reset_index(drop=True)
        
        storage.save_master(df_all, 'all_stocks.csv')
        logger.info(f"主数据文件已保存: {len(df_all)} 条记录")
        return df_all
    
    return pd.DataFrame()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='全量A股数据下载')
    parser.add_argument('--start-date', default='2020-01-01', help='开始日期')
    parser.add_argument('--end-date', default=None, help='结束日期')
    parser.add_argument('--batch-size', type=int, default=50, help='每批数量')
    parser.add_argument('--workers', type=int, default=5, help='并行线程数')
    parser.add_argument('--merge', action='store_true', help='完成后合并到主文件')
    
    args = parser.parse_args()
    
    download_all_stocks(
        start_date=args.start_date,
        end_date=args.end_date,
        batch_size=args.batch_size,
        max_workers=args.workers
    )
    
    if args.merge:
        merge_to_master()
