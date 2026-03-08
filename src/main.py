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

from fetchers.akshare import AkshareFetcher
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
    '000002',  # 万 科Ａ
    '600000',  # 浦发银行
    '600036',  # 招商银行
    '600519',  # 贵州茅台
    '601318',  # 中国平安
    '601398',  # 工商银行
    '601857',  # 中国石油
    '000858',  # 五粮液
    '600276',  # 恒瑞医药
]


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
    fetcher: AkshareFetcher,
    cleaner: BasicCleaner,
    adjuster: PriceAdjuster,
    storage: DataStorage,
    save_format: str
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

    Returns:
        是否成功
    """
    logger.info(f"=" * 50)
    logger.info(f"处理股票: {stock_code}")

    try:
        # 1. 获取数据
        logger.info(f"获取数据: {start_date} - {end_date}")
        df_raw = fetcher.fetch_daily(stock_code, start_date, end_date)

        if df_raw.empty:
            logger.warning(f"未获取到 {stock_code} 的数据")
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
    fetcher = AkshareFetcher(request_interval=1.0)
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
