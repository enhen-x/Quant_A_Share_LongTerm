# src/utils/calendar.py
"""交易日历工具"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Union

import pandas as pd


class TradingCalendar:
    """A股交易日历"""
    
    def __init__(self, trade_dates: Optional[List[str]] = None):
        """
        初始化交易日历
        
        Args:
            trade_dates: 交易日期列表 (格式: YYYYMMDD)
                        如为 None，将从数据文件加载
        """
        self._trade_dates = None
        
        if trade_dates is not None:
            self._trade_dates = pd.to_datetime(trade_dates, format='%Y%m%d')
            self._trade_dates = pd.DatetimeIndex(sorted(self._trade_dates))
    
    def load_from_file(self, path: str) -> 'TradingCalendar':
        """从文件加载交易日历"""
        df = pd.read_parquet(path)
        self._trade_dates = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        self._trade_dates = pd.DatetimeIndex(sorted(self._trade_dates))
        return self
    
    def is_trade_date(self, dt: Union[str, datetime, date]) -> bool:
        """判断是否为交易日"""
        if self._trade_dates is None:
            raise ValueError("交易日历未初始化")
        
        if isinstance(dt, str):
            dt = pd.to_datetime(dt)
        elif isinstance(dt, date) and not isinstance(dt, datetime):
            dt = pd.Timestamp(dt)
        
        return dt in self._trade_dates
    
    def get_trade_dates(
        self, 
        start_date: str, 
        end_date: str
    ) -> pd.DatetimeIndex:
        """
        获取日期范围内的交易日
        
        Args:
            start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
            end_date: 结束日期
            
        Returns:
            交易日 DatetimeIndex
        """
        if self._trade_dates is None:
            raise ValueError("交易日历未初始化")
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        mask = (self._trade_dates >= start) & (self._trade_dates <= end)
        return self._trade_dates[mask]
    
    def get_prev_trade_date(
        self, 
        dt: Union[str, datetime], 
        n: int = 1
    ) -> datetime:
        """
        获取前 n 个交易日
        
        Args:
            dt: 当前日期
            n: 向前推移的交易日数
            
        Returns:
            前 n 个交易日
        """
        if self._trade_dates is None:
            raise ValueError("交易日历未初始化")
        
        if isinstance(dt, str):
            dt = pd.to_datetime(dt)
        
        # 找到当前日期之前的交易日
        prev_dates = self._trade_dates[self._trade_dates < dt]
        
        if len(prev_dates) < n:
            raise ValueError(f"没有足够的历史交易日 (需要 {n} 天)")
        
        return prev_dates[-n]
    
    def get_next_trade_date(
        self, 
        dt: Union[str, datetime], 
        n: int = 1
    ) -> datetime:
        """
        获取后 n 个交易日
        
        Args:
            dt: 当前日期
            n: 向后推移的交易日数
            
        Returns:
            后 n 个交易日
        """
        if self._trade_dates is None:
            raise ValueError("交易日历未初始化")
        
        if isinstance(dt, str):
            dt = pd.to_datetime(dt)
        
        # 找到当前日期之后的交易日
        next_dates = self._trade_dates[self._trade_dates > dt]
        
        if len(next_dates) < n:
            raise ValueError(f"没有足够的未来交易日 (需要 {n} 天)")
        
        return next_dates[n - 1]
    
    def get_month_end_trade_dates(
        self, 
        start_date: str, 
        end_date: str
    ) -> pd.DatetimeIndex:
        """获取月末交易日"""
        trade_dates = self.get_trade_dates(start_date, end_date)
        df = pd.DataFrame({'date': trade_dates})
        df['month'] = df['date'].dt.to_period('M')
        month_ends = df.groupby('month')['date'].last()
        return pd.DatetimeIndex(month_ends.values)
    
    def get_quarter_end_trade_dates(
        self, 
        start_date: str, 
        end_date: str
    ) -> pd.DatetimeIndex:
        """获取季末交易日"""
        trade_dates = self.get_trade_dates(start_date, end_date)
        df = pd.DataFrame({'date': trade_dates})
        df['quarter'] = df['date'].dt.to_period('Q')
        quarter_ends = df.groupby('quarter')['date'].last()
        return pd.DatetimeIndex(quarter_ends.values)
