# src/strategy/screener.py
"""股票筛选器"""

from typing import Dict, List, Optional
import pandas as pd

from ..utils.config import load_config
from ..utils.logger import get_logger


class StockScreener:
    """股票筛选器: 过滤不符合条件的股票"""
    
    def __init__(self, config: dict = None):
        self.logger = get_logger('screener')
        
        if config is None:
            full_config = load_config()
            config = full_config.get('data', {}).get('stock_pool', {})
        
        self.config = config
        
        self.exclude_st = config.get('exclude_st', True)
        self.exclude_kcb = config.get('exclude_kcb', True)
        self.exclude_bj = config.get('exclude_bj', True)
        self.min_market_cap = config.get('min_market_cap', 3e9)
        self.min_list_days = config.get('min_list_days', 365)
    
    def filter_st(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤 ST 股票"""
        if 'name' not in df.columns:
            return df
        mask = ~df['name'].str.contains('ST|退', na=False)
        filtered = len(df) - mask.sum()
        self.logger.info(f"过滤 ST 股票: {filtered} 只")
        return df[mask]
    
    def filter_kcb(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤科创板 (688 开头)"""
        if 'ts_code' not in df.columns:
            return df
        mask = ~df['ts_code'].str.startswith('688')
        filtered = len(df) - mask.sum()
        self.logger.info(f"过滤科创板: {filtered} 只")
        return df[mask]
    
    def filter_bj(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤北交所 (以 .BJ 结尾或 8 开头)"""
        if 'ts_code' not in df.columns:
            return df
        mask = ~(df['ts_code'].str.contains('.BJ') | 
                 df['ts_code'].str.startswith('8'))
        filtered = len(df) - mask.sum()
        self.logger.info(f"过滤北交所: {filtered} 只")
        return df[mask]
    
    def filter_market_cap(
        self, 
        df: pd.DataFrame, 
        min_cap: float = None
    ) -> pd.DataFrame:
        """过滤市值过小的股票"""
        if min_cap is None:
            min_cap = self.min_market_cap
        
        if 'total_mv' not in df.columns:
            return df
        
        # total_mv 单位是万元，转换为元
        mask = df['total_mv'] * 10000 >= min_cap
        filtered = len(df) - mask.sum()
        self.logger.info(f"过滤市值 < {min_cap/1e8:.1f} 亿: {filtered} 只")
        return df[mask]
    
    def filter_list_days(
        self, 
        df: pd.DataFrame, 
        min_days: int = None
    ) -> pd.DataFrame:
        """过滤上市时间过短的股票"""
        if min_days is None:
            min_days = self.min_list_days
        
        if 'list_date' not in df.columns:
            return df
        
        from datetime import datetime
        today = pd.Timestamp(datetime.now())
        df['list_date_dt'] = pd.to_datetime(df['list_date'], format='%Y%m%d')
        df['list_days'] = (today - df['list_date_dt']).dt.days
        
        mask = df['list_days'] >= min_days
        filtered = len(df) - mask.sum()
        self.logger.info(f"过滤上市不足 {min_days} 天: {filtered} 只")
        
        result = df[mask].drop(columns=['list_date_dt', 'list_days'])
        return result
    
    def apply_all_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """应用所有过滤条件"""
        self.logger.info(f"开始筛选，原始股票数: {len(df)}")
        
        result = df.copy()
        
        if self.exclude_st:
            result = self.filter_st(result)
        
        if self.exclude_kcb:
            result = self.filter_kcb(result)
        
        if self.exclude_bj:
            result = self.filter_bj(result)
        
        result = self.filter_market_cap(result)
        result = self.filter_list_days(result)
        
        self.logger.info(f"筛选完成，剩余股票数: {len(result)}")
        return result
