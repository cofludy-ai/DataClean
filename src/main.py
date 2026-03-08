#!/usr/bin/env python3
"""
A股市场日级数据清洗工具
主入口文件
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Optional

# 添加 src 目录到路径
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fetchers.eastmoney import EastMoneyFetcher
from processors import BasicCleaner, PriceAdjuster
from storage import DataStorage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试股票列表（10只）
DEFAULT_TEST_STOCKS = [
    '000001',  # 平安银行
    '000002',  # 万科A
    '600000',  # 浦发银行
    '600036',  # 招商银行
    '600519',  # 贵州茅台
    '601318',  # 中国平安
    '601398',  # 工商银行
    '601857',  # 中国石油
    '000858',  # 五粮液
    '600276',  # 恒瑞医药
]


def generate_sample_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    生成模拟数据用于测试（当API不可用时）
    """
    import pandas as pd
    from datetime import datetime, timedelta
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 生成交易日（跳过周末）
    dates = []
    current = start
    while current <= end:
        if current.weekday() < 5:  # 周一到周五
            dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # 生成模拟数据
    import random
    random.seed(int(stock_code) if stock_code.isdigit() else 12345)
    
    base_price = random.uniform(10, 200)
    data = []
    for date in dates:
        open_p = base_price * random.uniform(0.98, 1.02)
        close_p = base_price * random.uniform(0.97, 1.03)
        high_p = max(open_p, close_p) * random.uniform(1.00, 1.05)
        low_p = min(open_p, close_p) * random.uniform(0.95, 1.00)
        volume = random.randint(1000000, 50000000)
        amount = volume * random.uniform(10, 100)
        
        data.append({
            '日期': date,
            '股票代码': stock_code,
            '开盘': round(open_p, 2),
            '收盘': round(close_p, 2),
            '最高': round(high_p, 2),
            '最低': round(low_p, 2),
            '成交量': volume,
            '成交额': round(amount, 2),
            '振幅': round(random.uniform(0, 5), 2),
            '涨跌幅': round(random.uniform(-5, 5), 2),
            '涨跌额': round(random.uniform(-10, 10), 2),
            '换手率': round(random.uniform(0, 5), 2)
        })
        base_price = close_p
    
    return pd.DataFrame(data)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='A股市场日级数据清洗工具'
    )

    parser.add_argument(
        '--stocks',
        nargs='+',
        default=DEFAULT_TEST_STOCKS,
        help='股票代码列表'
    )

    parser.add_argument(
        '--start-date',
        default='2021-01-01',
        help='开始日期 (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        default=datetime.now().strftime('%Y-%m-%d'),
        help='结束日期 (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--data-dir',
        default='data',
        help='数据存储目录'
    )

    parser.add_argument(
        '--adjust',
        choices=['qfq', 'hfq', 'no'],
        default='qfq',
        help='复权类型: qfq(前复权), hfq(后复权), no(不复权)'
    )

    parser.add_argument(
        '--skip-fetch',
        action='store_true',
        help='跳过数据获取，仅执行清洗'
    )

    parser.add_argument(
        '--save-format',
        choices=['csv', 'parquet', 'json'],
        default='csv',
        help='保存格式'
    )

    return parser.parse_args()


def fetch_and_clean(
    stock_code: str,
    start_date: str,
    end_date: str,
    fetcher: EastMoneyFetcher,
    cleaner: BasicCleaner,
    adjuster: PriceAdjuster,
    storage: DataStorage,
    save_format: str,
    use_mock: bool = False
) -> bool:
    """
    获取并清洗单只股票数据

    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        fetcher: 数据获取器
        cleaner: 清洗器
        adjuster: 复权处理器
        storage: 存储
        save_format: 保存格式
        use_mock: 是否使用模拟数据（当API不可用时）

    Returns:
        是否成功
    """
    logger.info(f"=" * 50)
    logger.info(f"处理股票: {stock_code}")

    try:
        # 1. 获取数据
        logger.info(f"获取数据: {start_date} - {end_date}")
        
        try:
            df_raw = fetcher.fetch_daily(stock_code, start_date, end_date)
        except Exception as e:
            logger.warning(f"API获取失败: {e}")
            if use_mock:
                logger.info("使用模拟数据...")
                df_raw = generate_sample_data(stock_code, start_date, end_date)
            else:
                df_raw = pd.DataFrame()

        if df_raw.empty:
            logger.warning(f"未获取到 {stock_code} 的数据")
            if use_mock:
                df_raw = generate_sample_data(stock_code, start_date, end_date)
                logger.info(f"生成了模拟数据: {len(df_raw)} 条")
            else:
                return False

        logger.info(f"原始数据: {len(df_raw)} 条")

        # 保存原始数据
        storage.save_raw(df_raw, stock_code, save_format)

        # 2. 复权处理
        logger.info("执行复权处理")
        df_adj = adjuster.adjust(df_raw)

        # 3. 数据清洗
        logger.info("执行数据清洗")
        df_clean = cleaner.clean(df_adj)

        # 4. 保存清洗后数据
        storage.save_clean(df_clean, stock_code, save_format)

        # 5. 输出统计
        stats = cleaner.get_statistics(df_clean)
        logger.info(f"统计信息: {stats}")

        logger.info(f"完成: {stock_code}")
        return True

    except Exception as e:
        logger.error(f"处理失败: {e}")
        return False


def main():
    """主函数"""
    args = parse_args()

    logger.info("=" * 50)
    logger.info("A股数据清洗工具启动")
    logger.info(f"股票数量: {len(args.stocks)}")
    logger.info(f"日期范围: {args.start_date} - {args.end_date}")
    logger.info(f"复权类型: {args.adjust}")
    logger.info("=" * 50)

    # 初始化组件
    fetcher = EastMoneyFetcher(request_interval=0.5)
    cleaner = BasicCleaner()
    adjuster = PriceAdjuster(method=args.adjust)
    storage = DataStorage(args.data_dir)

    # 统计
    success_count = 0
    fail_count = 0

    # 处理每只股票
    for i, stock_code in enumerate(args.stocks, 1):
        logger.info(f"\n[{i}/{len(args.stocks)}] 正在处理...")

        success = fetch_and_clean(
            stock_code,
            args.start_date,
            args.end_date,
            fetcher,
            cleaner,
            adjuster,
            storage,
            args.save_format
        )

        if success:
            success_count += 1
        else:
            fail_count += 1

    # 总结
    logger.info("=" * 50)
    logger.info("处理完成!")
    logger.info(f"成功: {success_count}/{len(args.stocks)}")
    logger.info(f"失败: {fail_count}/{len(args.stocks)}")
    logger.info("=" * 50)

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
