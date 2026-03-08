"""
数据校验模块
检测清洗后的数据是否合理
"""
import pandas as pd
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class DataValidator:
    """数据校验器"""

    def __init__(self):
        logger.info("数据校验器初始化")

    def validate(self, df: pd.DataFrame) -> Dict:
        """
        全面校验数据
        
        Args:
            df: 待校验的数据
            
        Returns:
            校验结果字典
        """
        if df.empty:
            return {
                'valid': False,
                'error': '数据为空',
                'issues': []
            }

        issues = []
        
        # 1. 必填字段检查
        issues.extend(self._check_required_columns(df))
        
        # 2. 日期格式检查
        issues.extend(self._check_date_format(df))
        
        # 3. 重复数据检查
        issues.extend(self._check_duplicates(df))
        
        # 4. 价格合理性检查
        issues.extend(self._check_price(df))
        
        # 5. 成交量检查
        issues.extend(self._check_volume(df))
        
        # 6. 涨跌停检查
        issues.extend(self._check_limit(df))
        
        # 7. 缺失值检查
        issues.extend(self._check_missing(df))
        
        # 8. 连续性检查
        issues.extend(self._check_continuity(df))

        result = {
            'valid': len(issues) == 0,
            'total_records': len(df),
            'issue_count': len(issues),
            'issues': issues
        }
        
        if issues:
            logger.warning(f"发现 {len(issues)} 个问题")
        else:
            logger.info("数据校验通过")
        
        return result

    def _check_required_columns(self, df: pd.DataFrame) -> List[Dict]:
        """检查必填字段"""
        required = ['date', 'stock_code', 'open', 'close', 'high', 'low', 'volume']
        issues = []
        
        missing = [c for c in required if c not in df.columns]
        if missing:
            issues.append({
                'type': 'missing_column',
                'severity': 'error',
                'message': f"缺少必填字段: {missing}"
            })
        
        return issues

    def _check_date_format(self, df: pd.DataFrame) -> List[Dict]:
        """检查日期格式"""
        issues = []
        
        if 'date' not in df.columns:
            return issues
        
        try:
            pd.to_datetime(df['date'])
        except Exception as e:
            issues.append({
                'type': 'invalid_date_format',
                'severity': 'error',
                'message': f"日期格式错误: {e}"
            })
        
        return issues

    def _check_duplicates(self, df: pd.DataFrame) -> List[Dict]:
        """检查重复数据"""
        issues = []
        
        if 'stock_code' in df.columns and 'date' in df.columns:
            duplicates = df[df.duplicated(subset=['stock_code', 'date'], keep=False)]
            if not duplicates.empty:
                issues.append({
                    'type': 'duplicate_records',
                    'severity': 'warning',
                    'message': f"发现 {len(duplicates)} 条重复记录",
                    'count': len(duplicates)
                })
        
        return issues

    def _check_price(self, df: pd.DataFrame) -> List[Dict]:
        """检查价格合理性"""
        issues = []
        
        price_cols = ['open', 'close', 'high', 'low']
        if not all(c in df.columns for c in price_cols):
            return issues
        
        # 检查：最高价 >= 最低价
        invalid = df[df['high'] < df['low']]
        if not invalid.empty:
            issues.append({
                'type': 'high_low_inconsistent',
                'severity': 'error',
                'message': f"最高价 < 最低价: {len(invalid)} 条",
                'count': len(invalid)
            })
        
        # 检查：收盘价应在高低价范围内
        invalid = df[(df['close'] > df['high']) | (df['close'] < df['low'])]
        if not invalid.empty:
            issues.append({
                'type': 'close_out_of_range',
                'severity': 'warning',
                'message': f"收盘价超出高低价范围: {len(invalid)} 条",
                'count': len(invalid)
            })
        
        # 检查：价格应为正数
        for col in price_cols:
            invalid = df[df[col] <= 0]
            if not invalid.empty:
                issues.append({
                    'type': 'invalid_price',
                    'severity': 'error',
                    'message': f"{col} <= 0: {len(invalid)} 条",
                    'count': len(invalid)
                })
        
        # 检查：开盘价与收盘价差异过大（超过20%）
        invalid = df[abs(df['close'] - df['open']) / df['open'] > 0.2]
        if not invalid.empty:
            issues.append({
                'type': 'extreme_price_change',
                'severity': 'warning',
                'message': f"单日涨跌幅超过20%: {len(invalid)} 条",
                'count': len(invalid)
            })
        
        return issues

    def _check_volume(self, df: pd.DataFrame) -> List[Dict]:
        """检查成交量"""
        issues = []
        
        if 'volume' not in df.columns:
            return issues
        
        # 检查：成交量为负数
        invalid = df[df['volume'] < 0]
        if not invalid.empty:
            issues.append({
                'type': 'invalid_volume',
                'severity': 'error',
                'message': f"成交量为负数: {len(invalid)} 条",
                'count': len(invalid)
            })
        
        # 检查：成交量为0（停牌日除外）
        zero_volume = df[df['volume'] == 0]
        if not zero_volume.empty:
            # 排除涨跌停的情况（开盘=收盘，且成交量为0可能是惜售）
            issues.append({
                'type': 'zero_volume',
                'severity': 'info',
                'message': f"成交量为0: {len(zero_volume)} 条（可能是停牌）",
                'count': len(zero_volume)
            })
        
        # 检查：成交量异常大（超过平均10倍）
        avg_volume = df['volume'].mean()
        abnormal = df[df['volume'] > avg_volume * 10]
        if not abnormal.empty:
            issues.append({
                'type': 'abnormal_volume',
                'severity': 'warning',
                'message': f"成交量异常大: {len(abnormal)} 条",
                'count': len(abnormal)
            })
        
        return issues

    def _check_limit(self, df: pd.DataFrame) -> List[Dict]:
        """检查涨跌停"""
        issues = []
        
        if 'change_pct' not in df.columns:
            return issues
        
        # 理论上A股涨跌停是10%（ST是5%），但复权后可能略有差异
        # 检查超过涨跌停限制
        limit_10 = df[df['change_pct'].abs() > 10.5]
        limit_5 = df[(df['change_pct'].abs() > 5.5) & (df['change_pct'].abs() <= 10.5)]
        
        if not limit_10.empty:
            issues.append({
                'type': 'exceed_limit_10',
                'severity': 'warning',
                'message': f"涨跌幅超过10%: {len(limit_10)} 条",
                'count': len(limit_10)
            })
        
        return issues

    def _check_missing(self, df: pd.DataFrame) -> List[Dict]:
        """检查缺失值"""
        issues = []
        
        required = ['date', 'stock_code', 'close']
        for col in required:
            if col in df.columns:
                missing = df[df[col].isna()]
                if not missing.empty:
                    issues.append({
                        'type': 'missing_value',
                        'severity': 'error',
                        'message': f"{col} 缺失: {len(missing)} 条",
                        'count': len(missing)
                    })
        
        return issues

    def _check_continuity(self, df: pd.DataFrame) -> List[Dict]:
        """检查数据连续性"""
        issues = []
        
        if 'date' not in df.columns or 'stock_code' not in df.columns:
            return issues
        
        # 检查每只股票
        for stock_code in df['stock_code'].unique():
            stock_df = df[df['stock_code'] == stock_code].sort_values('date')
            dates = pd.to_datetime(stock_df['date'])
            
            # 检查是否有跳跃（超过10天没有数据）
            date_diff = dates.diff()
            
            # 处理 Timedelta 类型
            try:
                diff_days = date_diff.dt.days
            except AttributeError:
                # 如果是 int 直接使用
                diff_days = date_diff
            
            large_gaps = diff_days[diff_days > 10]
            
            if not large_gaps.empty:
                issues.append({
                    'type': 'data_gap',
                    'severity': 'info',
                    'message': f"{stock_code}: 发现 {len(large_gaps)} 个大时间跨度（>10天无数据）",
                    'count': len(large_gaps)
                })
        
        return issues

    def validate_file(self, file_path: str) -> Dict:
        """
        校验文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            校验结果
        """
        try:
            df = pd.read_csv(file_path)
            logger.info(f"加载文件: {file_path}, {len(df)} 条")
            return self.validate(df)
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'issues': []
            }
