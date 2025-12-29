# src/position/fixed_position.py
"""固定仓位策略"""

from typing import Dict, List
import pandas as pd

from .base import PositionSizerBase


class FixedPositionSizer(PositionSizerBase):
    """固定仓位分配器"""
    
    def calculate_weights(
        self, 
        stocks: List[str], 
        **kwargs
    ) -> Dict[str, float]:
        """等权分配"""
        return self.equal_weight(stocks)
    
    def equal_weight(self, stocks: List[str]) -> Dict[str, float]:
        """
        等权分配: 每只股票 1/N
        """
        n = len(stocks)
        if n == 0:
            return {}
        weight = 1.0 / n
        return {stock: weight for stock in stocks}
    
    def market_cap_weight(
        self, 
        stocks: List[str], 
        market_caps: pd.Series
    ) -> Dict[str, float]:
        """
        市值加权
        
        Args:
            stocks: 股票列表
            market_caps: 市值数据 (index = ts_code)
        """
        caps = market_caps.loc[stocks]
        total = caps.sum()
        if total == 0:
            return self.equal_weight(stocks)
        
        weights = caps / total
        return weights.to_dict()
    
    def score_weight(
        self, 
        scores: pd.Series, 
        power: float = 1.0
    ) -> Dict[str, float]:
        """
        得分加权: 得分越高权重越大
        
        Args:
            scores: 得分 (index = ts_code)
            power: 幂次，>1 则更集中于高分股
        """
        # 归一化到 0-1
        normalized = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
        weighted = (normalized ** power)
        weights = weighted / weighted.sum()
        return weights.to_dict()
