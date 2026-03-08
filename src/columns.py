"""
数据列名映射
中文列名 -> 英文列名
"""
COLUMN_MAPPING = {
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
    '换手率': 'turnover',
}

# 反向映射
REVERSE_MAPPING = {v: k for k, v in COLUMN_MAPPING.items()}

# 英文列名列表
COLUMNS = [
    'date',
    'stock_code',
    'open',
    'close',
    'high',
    'low',
    'volume',
    'amount',
    'amplitude',
    'change_pct',
    'change',
    'turnover',
]
