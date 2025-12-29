# src/data_source/base.py
"""数据源抽象基类"""

from abc import ABC, abstractmethod
from typing import Optional, List

import pandas as pd


class DataSourceBase(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        pass
    
    @abstractmethod
    def get_daily(
        self, 
        ts_code: str, 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """获取日线行情"""
        pass
    
    @abstractmethod
    def get_daily_basic(self, trade_date: str) -> pd.DataFrame:
        """获取每日指标 (PE/PB/市值等)"""
        pass
    
    @abstractmethod
    def get_adj_factor(self, ts_code: str) -> pd.DataFrame:
        """获取复权因子"""
        pass
    
    @abstractmethod
    def get_income(
        self, 
        ts_code: str, 
        period: Optional[str] = None
    ) -> pd.DataFrame:
        """获取利润表"""
        pass
    
    @abstractmethod
    def get_balancesheet(
        self, 
        ts_code: str, 
        period: Optional[str] = None
    ) -> pd.DataFrame:
        """获取资产负债表"""
        pass
    
    @abstractmethod
    def get_cashflow(
        self, 
        ts_code: str, 
        period: Optional[str] = None
    ) -> pd.DataFrame:
        """获取现金流量表"""
        pass
    
    @abstractmethod
    def get_fina_indicator(self, ts_code: str) -> pd.DataFrame:
        """获取财务指标"""
        pass
