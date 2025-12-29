# src/factors/momentum.py
"""动量因子计算"""

from typing import List, Optional
import pandas as pd
import numpy as np


class MomentumFactors:
    """动量因子计算器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.windows = self.config.get('windows', [21, 63, 126, 252])
    
    def calc_return(
        self, 
        close: pd.Series,
        window: int
    ) -> pd.Series:
        """
        计算 N 日收益率
        
        Args:
            close: 收盘价序列
            window: 计算窗口 (交易日)
            
        Returns:
            收益率序列 (百分比)
        """
        return close.pct_change(window) * 100
    
    def calc_momentum_score(
        self, 
        close: pd.Series,
        windows: List[int] = None
    ) -> pd.Series:
        """
        计算综合动量得分
        
        综合多个周期的收益率
        """
        if windows is None:
            windows = self.windows
        
        scores = []
        for w in windows:
            ret = self.calc_return(close, w)
            # 排名转换为 0-1
            rank = ret.rank(pct=True)
            scores.append(rank)
        
        # 简单平均
        return pd.concat(scores, axis=1).mean(axis=1)
    
    def calc_relative_strength(
        self, 
        stock_close: pd.Series,
        benchmark_close: pd.Series,
        window: int = 252
    ) -> pd.Series:
        """
        计算相对强度
        
        RS = (股票收益 - 基准收益) / 基准收益
        """
        stock_ret = stock_close.pct_change(window)
        bench_ret = benchmark_close.pct_change(window)
        
        rs = (stock_ret - bench_ret) / bench_ret.abs().clip(lower=0.01)
        return rs
    
    def calc_alpha(
        self, 
        stock_returns: pd.Series,
        market_returns: pd.Series,
        risk_free_rate: float = 0.03,
        window: int = 252
    ) -> pd.Series:
        """
        计算历史 Alpha
        
        使用简单的 CAPM 模型
        """
        # 超额收益
        excess_stock = stock_returns - risk_free_rate / 252
        excess_market = market_returns - risk_free_rate / 252
        
        def rolling_alpha(idx):
            if idx < window:
                return np.nan
            
            y = excess_stock.iloc[idx-window:idx]
            x = excess_market.iloc[idx-window:idx]
            
            # 简单线性回归
            if len(x) < window // 2:
                return np.nan
            
            cov = np.cov(x, y)[0, 1]
            var = np.var(x)
            if var == 0:
                return np.nan
            
            beta = cov / var
            alpha = y.mean() - beta * x.mean()
            return alpha * 252  # 年化
        
        alphas = [rolling_alpha(i) for i in range(len(stock_returns))]
        return pd.Series(alphas, index=stock_returns.index)
    
    def calc_all(
        self, 
        df: pd.DataFrame,
        close_col: str = 'close'
    ) -> pd.DataFrame:
        """计算所有动量因子"""
        result = pd.DataFrame(index=df.index)
        
        if close_col not in df.columns:
            return result
        
        close = df[close_col]
        
        for w in self.windows:
            months = w // 21  # 转换为月数
            col_name = f'factor_ret_{months}m'
            result[col_name] = self.calc_return(close, w)
        
        result['factor_momentum_score'] = self.calc_momentum_score(close)
        
        return result
