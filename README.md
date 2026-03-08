# A股市场日级数据清洗工具

A股市场日级数据的获取、清洗、校验和查询工具。

## 功能特性

- **多数据源支持**：通过插件式架构支持多种数据源（当前实现东方财富 API）
- **复权处理**：支持前复权（qfq）和后复权（hfq）价格
- **数据清洗**：自动检测和处理异常数据
- **数据校验**：全面的数据质量检查
- **数据查询**：灵活的切片查询接口
- **增量更新**：支持增量合并，减少重复工作
- **本地存储**：支持 CSV、Parquet、JSON 多种格式

## 项目结构

```
stock-data-cleaner/
├── data/                 # 数据目录
│   ├── raw/             # 原始数据
│   ├── clean/           # 清洗后数据
│   └── master/          # 合并后的主数据
├── src/                 # 源代码
│   ├── fetchers/        # 数据获取器
│   │   ├── base.py      # 基类
│   │   └── eastmoney.py # 东方财富实现
│   ├── processors/      # 数据处理
│   │   ├── adjuster.py  # 复权处理
│   │   └── cleaner.py   # 基础清洗
│   ├── query.py         # 数据查询
│   ├── validator.py     # 数据校验
│   ├── storage.py       # 存储模块
│   ├── columns.py       # 列名映射
│   └── main.py          # 主入口
├── tests/               # 测试
├── requirements.txt     # 依赖
└── README.md
```

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 命令行运行

```bash
cd src

# 获取单只股票数据
python3 main.py --stocks 600519 --start-date 2021-01-01 --end-date 2026-03-08

# 获取多只股票数据
python3 main.py --stocks 600519 600036 000001 --start-date 2021-01-01 --end-date 2026-03-08

# 增量合并到主数据文件
python3 main.py --stocks 600519 --start-date 2021-01-01 --end-date 2026-03-08 --merge
```

### 2. 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--stocks` | 股票代码列表 | 10只测试股票 |
| `--start-date` | 开始日期 (YYYY-MM-DD) | 2021-01-01 |
| `--end-date` | 结束日期 (YYYY-MM-DD) | 当前日期 |
| `--data-dir` | 数据目录 | data |
| `--adjust` | 复权类型 (qfq/hfq/no) | qfq |
| `--save-format` | 保存格式 (csv/parquet/json) | csv |
| `--merge` | 增量合并到主数据文件 | False |
| `--master-file` | 主数据文件名 | all_stocks.csv |

### 3. Python API

```python
import sys
sys.path.insert(0, 'src')

# ============ 数据获取 ============
from fetchers.eastmoney import EastMoneyFetcher

fetcher = EastMoneyFetcher()
df = fetcher.fetch_daily('600519', '20210101', '20260308')
print(f"获取到 {len(df)} 条数据")

# ============ 数据清洗 ============
from processors import BasicCleaner, PriceAdjuster

cleaner = BasicCleaner()
adjuster = PriceAdjuster(method='qfq')

df_clean = cleaner.clean(adjuster.adjust(df))
print(f"清洗后 {len(df_clean)} 条数据")

# ============ 数据存储 ============
from storage import DataStorage

storage = DataStorage('data')
storage.save_clean(df_clean, '600519')
storage.merge_incremental(df_clean, 'all_stocks.csv')

# ============ 数据查询 ============
from query import DataQuery

query = DataQuery('data/master/all_stocks.csv')

# 查询单只股票
df = query.query(stock_codes=['600519'])

# 查询日期范围
df = query.query(start_date='2024-01-01', end_date='2024-12-31')

# 查询多只股票
df = query.query(stock_codes=['600519', '600036'], start_date='2024-01-01')

# 获取最近 N 天数据
df = query.get_latest('600519', n=10)

# 获取股票列表
stocks = query.get_stock_list()

# 获取统计信息
stats = query.get_statistics()

# ============ 数据校验 ============
from validator import DataValidator

validator = DataValidator()

# 校验 DataFrame
result = validator.validate(df)
print(f"校验结果: {result['valid']}")
print(f"问题数量: {result['issue_count']}")
for issue in result['issues']:
    print(f"  - {issue['type']}: {issue['message']}")

# 校验文件
result = validator.validate_file('data/clean/600519_clean.csv')
```

## 数据格式

### 列名说明（英文）

| 字段 | 类型 | 说明 |
|------|------|------|
| date | string | 交易日期 (YYYY-MM-DD) |
| stock_code | string | 股票代码 |
| open | float | 开盘价（前复权） |
| close | float | 收盘价（前复权） |
| high | float | 最高价（前复权） |
| low | float | 最低价（前复权） |
| volume | int | 成交量（手） |
| amount | float | 成交额（元） |
| amplitude | float | 振幅（%） |
| change_pct | float | 涨跌幅（%） |
| change | float | 涨跌额（元） |
| turnover | float | 换手率（%） |

### 示例数据

```
date,stock_code,open,close,high,low,volume,amount,amplitude,change_pct,change,turnover
2021-01-04,600519,1785.77,1782.79,1790.78,1768.25,29248,6090260480.0,1.26,-0.06,-1.00,0.35
2021-01-05,600519,1775.79,1845.24,1845.24,1775.00,32928,7282306560.0,3.94,3.50,62.45,0.41
```

## 测试股票

默认包含10只A股：
- 000001 平安银行
- 000002 万科A
- 600000 浦发银行
- 600036 招商银行
- 600519 贵州茅台
- 601318 中国平安
- 601398 工商银行
- 601857 中国石油
- 000858 五粮液
- 600276 恒瑞医药

## 数据校验规则

### 错误 (Error)
- 缺少必填字段
- 日期格式错误
- 最高价 < 最低价
- 价格 <= 0
- 成交量为负数
- 关键字段缺失

### 警告 (Warning)
- 存在重复记录
- 收盘价超出高低价范围
- 单日涨跌幅超过20%
- 成交量异常大（超过平均10倍）
- 涨跌幅超过10%（复权后）

### 信息 (Info)
- 成交量为0（可能是停牌）
- 数据存在较大时间跨度

## License

MIT
