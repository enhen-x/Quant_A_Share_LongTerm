# src/position/risk_parity.py
"""风险平价策略"""

from typing import Dict, List
import pandas as pd
import numpy as np

from .base import PositionSizerBase


class RiskParitySizer(PositionSizerBase):
    """风险平价仓位管理器: 使各标的对组合风险的贡献相等"""
    
    def __init__(self, lookback: int = 60):
        """
        Args:
            lookback: 波动率计算回溯期 (交易日)
        """
        self.lookback = lookback
    
    def calculate_weights(
        self, 
        stocks: List[str], 
        returns: pd.DataFrame = None,
        **kwargs
    ) -> Dict[str, float]:
        """
        计算风险平价权重
        
        Args:
            stocks: 股票列表
            returns: 收益率数据 (列 = 股票)
        """
        if returns is None or returns.empty:
            # 无数据时回退到等权
            n = len(stocks)
            return {s: 1.0/n for s in stocks}
        
        return self.calculate_by_volatility(returns[stocks])
    
    def calculate_by_volatility(
        self, 
        returns: pd.DataFrame
    ) -> Dict[str, float]:
        """
        基于历史波动率计算风险平价权重
        
        权重 ∝ 1 / σ_i (波动率的倒数)
        """
        # 计算年化波动率
        vol = returns.tail(self.lookback).std() * np.sqrt(252)
        
        # 避免除以 0
        vol = vol.clip(lower=0.01)
        
        # 波动率倒数
        inv_vol = 1.0 / vol
        
        # 归一化为权重
        weights = inv_vol / inv_vol.sum()
        
        return weights.to_dict()
    
    def calculate_risk_contribution(
        self, 
        weights: Dict[str, float],
        cov_matrix: pd.DataFrame
    ) -> pd.Series:
        """
        计算各资产的风险贡献
        
        用于验证风险平价是否达成
        """
        w = pd.Series(weights)
        stocks = list(weights.keys())
        cov = cov_matrix.loc[stocks, stocks]
        
        portfolio_vol = np.sqrt(w @ cov @ w)
        
        # 边际风险贡献
        marginal = cov @ w
        
        # 风险贡献 = w_i * 边际风险贡献_i
        risk_contrib = w * marginal / portfolio_vol
        
        return risk_contrib
