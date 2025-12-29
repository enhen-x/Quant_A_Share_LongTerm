# src/factors/quality.py
"""质量因子计算"""

from typing import Optional
import pandas as pd
import numpy as np


class QualityFactors:
    """质量因子计算器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.roe_years = self.config.get('roe_stability_years', 5)
    
    def calc_roe_stability(
        self, 
        roe_history: pd.DataFrame,
        years: int = None
    ) -> pd.Series:
        """
        计算 ROE 稳定性
        
        过去 N 年 ROE 的标准差，越低越稳定
        
        Args:
            roe_history: 历史 ROE 数据 (行=时间, 列=股票)
            years: 计算年数
            
        Returns:
            ROE 标准差 (越低越好)
        """
        if years is None:
            years = self.roe_years
        
        # 取最近 N 年数据
        recent = roe_history.tail(years * 4)  # 季报
        return recent.std()
    
    def calc_roe_mean(
        self, 
        roe_history: pd.DataFrame,
        years: int = None
    ) -> pd.Series:
        """计算平均 ROE"""
        if years is None:
            years = self.roe_years
        
        recent = roe_history.tail(years * 4)
        return recent.mean()
    
    def calc_gross_margin_trend(
        self, 
        gross_margin_history: pd.DataFrame,
        periods: int = 8
    ) -> pd.Series:
        """
        计算毛利率变化趋势
        
        使用线性回归斜率
        """
        recent = gross_margin_history.tail(periods)
        
        def trend_slope(series):
            if series.isna().sum() > len(series) / 2:
                return np.nan
            x = np.arange(len(series))
            y = series.values
            mask = ~np.isnan(y)
            if mask.sum() < 3:
                return np.nan
            slope = np.polyfit(x[mask], y[mask], 1)[0]
            return slope
        
        return recent.apply(trend_slope)
    
    def calc_debt_ratio_score(
        self, 
        debt_ratio: pd.Series
    ) -> pd.Series:
        """
        负债率评分
        
        负债率越低评分越高 (0-100)
        """
        # 负债率通常 0-100%
        # 转换为得分：100 - debt_ratio
        score = 100 - debt_ratio.clip(lower=0, upper=100)
        return score
    
    def calc_current_ratio_score(
        self, 
        current_ratio: pd.Series
    ) -> pd.Series:
        """
        流动比率评分
        
        流动比率越高越好 (但过高可能表示资金利用效率低)
        最优区间: 1.5 - 3.0
        """
        def score_func(x):
            if pd.isna(x):
                return np.nan
            if x < 1.0:
                return max(0, x * 50)  # 0-50
            elif x <= 2.0:
                return 50 + (x - 1.0) * 50  # 50-100
            elif x <= 3.0:
                return 100  # 最优
            else:
                return max(50, 100 - (x - 3.0) * 10)  # 逐渐降低
        
        return current_ratio.apply(score_func)
    
    def calc_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有质量因子"""
        result = pd.DataFrame(index=df.index)
        
        if 'roe' in df.columns:
            result['factor_roe'] = df['roe']
        
        if 'roa' in df.columns:
            result['factor_roa'] = df['roa']
        
        if 'grossprofit_margin' in df.columns:
            result['factor_gross_margin'] = df['grossprofit_margin']
        
        if 'debt_to_assets' in df.columns:
            result['factor_debt_ratio'] = df['debt_to_assets']
            result['factor_debt_score'] = self.calc_debt_ratio_score(
                df['debt_to_assets']
            )
        
        return result
