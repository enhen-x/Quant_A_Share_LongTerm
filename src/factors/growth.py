# src/factors/growth.py
"""成长因子计算"""

from typing import Optional
import pandas as pd
import numpy as np


class GrowthFactors:
    """成长因子计算器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.eps_years = self.config.get('eps_growth_years', 3)
    
    def calc_revenue_yoy(self, df: pd.DataFrame) -> pd.Series:
        """计算营收同比增速"""
        if 'revenue' not in df.columns:
            raise ValueError("需要 revenue 列")
        
        # 假设数据按季度排列
        return df['revenue'].pct_change(4) * 100  # 同比
    
    def calc_profit_yoy(self, df: pd.DataFrame) -> pd.Series:
        """计算净利润同比增速"""
        if 'net_profit' not in df.columns:
            raise ValueError("需要 net_profit 列")
        
        return df['net_profit'].pct_change(4) * 100
    
    def calc_eps_cagr(
        self, 
        eps_history: pd.Series,
        years: int = None
    ) -> float:
        """
        计算 EPS 复合年化增长率
        
        CAGR = (End/Start)^(1/n) - 1
        """
        if years is None:
            years = self.eps_years
        
        # 取 years 年前的值和当前值
        periods = years * 4  # 季度
        if len(eps_history) < periods:
            return np.nan
        
        start = eps_history.iloc[-periods]
        end = eps_history.iloc[-1]
        
        if start <= 0 or end <= 0:
            return np.nan
        
        cagr = (end / start) ** (1 / years) - 1
        return cagr * 100  # 百分比
    
    def calc_sustainable_growth_rate(
        self, 
        roe: pd.Series,
        payout_ratio: pd.Series
    ) -> pd.Series:
        """
        计算可持续增长率
        
        SGR = ROE × (1 - 分红比例)
        """
        retention_ratio = 1 - payout_ratio.clip(lower=0, upper=1)
        sgr = roe * retention_ratio
        return sgr
    
    def calc_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有成长因子"""
        result = pd.DataFrame(index=df.index)
        
        if 'q_sales_yoy' in df.columns:
            result['factor_revenue_yoy'] = df['q_sales_yoy']
        
        if 'q_profit_yoy' in df.columns:
            result['factor_profit_yoy'] = df['q_profit_yoy']
        
        if 'basic_eps_yoy' in df.columns:
            result['factor_eps_yoy'] = df['basic_eps_yoy']
        
        return result
