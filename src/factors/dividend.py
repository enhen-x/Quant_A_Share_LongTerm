# src/factors/dividend.py
"""股息因子计算"""

from typing import Optional
import pandas as pd
import numpy as np


class DividendFactors:
    """股息因子计算器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
    
    def calc_dividend_yield(
        self, 
        dps: pd.Series,
        price: pd.Series
    ) -> pd.Series:
        """
        计算股息率
        
        股息率 = 每股股息 / 股价
        """
        return (dps / price.clip(lower=0.01)) * 100
    
    def calc_dividend_yield_ttm(
        self, 
        df: pd.DataFrame
    ) -> pd.Series:
        """从 daily_basic 数据获取 TTM 股息率"""
        if 'dv_ttm' in df.columns:
            return df['dv_ttm']
        return pd.Series(index=df.index)
    
    def calc_dividend_growth(
        self, 
        dps_history: pd.Series,
        years: int = 3
    ) -> float:
        """
        计算股息增长率
        
        CAGR of DPS over N years
        """
        if len(dps_history) < years:
            return np.nan
        
        start = dps_history.iloc[-years]
        end = dps_history.iloc[-1]
        
        if start <= 0 or end <= 0:
            return np.nan
        
        return ((end / start) ** (1 / years) - 1) * 100
    
    def calc_payout_ratio(
        self, 
        dps: pd.Series,
        eps: pd.Series
    ) -> pd.Series:
        """
        计算分红比例
        
        Payout Ratio = DPS / EPS
        """
        return (dps / eps.clip(lower=0.01)) * 100
    
    def calc_dividend_consistency(
        self, 
        dividend_history: pd.DataFrame,
        years: int = 5
    ) -> pd.Series:
        """
        计算分红一致性
        
        过去 N 年中有多少年分红
        """
        recent = dividend_history.tail(years)
        has_dividend = (recent > 0).sum()
        return has_dividend / years * 100
    
    def calc_dividend_yield_3y_avg(
        self, 
        dy_history: pd.DataFrame
    ) -> pd.Series:
        """计算 3 年平均股息率"""
        return dy_history.tail(3 * 252).mean()
    
    def calc_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有股息因子"""
        result = pd.DataFrame(index=df.index)
        
        if 'dv_ttm' in df.columns:
            result['factor_dv_ttm'] = df['dv_ttm']
        
        if 'dv_ratio' in df.columns:
            result['factor_dv_ratio'] = df['dv_ratio']
        
        return result
