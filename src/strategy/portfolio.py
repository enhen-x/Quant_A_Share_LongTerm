# src/strategy/portfolio.py
"""组合构建"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from ..utils.config import load_config
from ..utils.logger import get_logger


class PortfolioBuilder:
    """投资组合构建器"""
    
    def __init__(self, config: dict = None):
        self.logger = get_logger('portfolio')
        
        if config is None:
            full_config = load_config()
            config = full_config.get('strategy', {})
        
        self.config = config
        self.max_industry_weight = config.get('max_industry_weight', 0.20)
    
    def build_equal_weight(
        self, 
        stocks: List[str]
    ) -> Dict[str, float]:
        """
        等权重组合
        
        Args:
            stocks: 股票代码列表
            
        Returns:
            股票权重字典
        """
        n = len(stocks)
        weight = 1.0 / n if n > 0 else 0
        return {stock: weight for stock in stocks}
    
    def build_score_weight(
        self, 
        scores: pd.Series,
        power: float = 1.0
    ) -> Dict[str, float]:
        """
        得分加权组合
        
        Args:
            scores: 股票得分 (ts_code -> score)
            power: 幂次，power > 1 则高分股权重更大
            
        Returns:
            股票权重字典
        """
        # 归一化得分
        scores_normalized = (scores - scores.min()) / (scores.max() - scores.min())
        scores_powered = scores_normalized ** power
        
        # 归一化为权重
        weights = scores_powered / scores_powered.sum()
        return weights.to_dict()
    
    def apply_industry_constraint(
        self, 
        weights: Dict[str, float],
        industry_map: Dict[str, str],
        max_weight: float = None
    ) -> Dict[str, float]:
        """
        应用行业约束
        
        Args:
            weights: 原始权重
            industry_map: 股票 -> 行业映射
            max_weight: 单行业最大权重
            
        Returns:
            调整后的权重
        """
        if max_weight is None:
            max_weight = self.max_industry_weight
        
        # 计算各行业当前权重
        industry_weights = {}
        for stock, weight in weights.items():
            industry = industry_map.get(stock, 'Unknown')
            if industry not in industry_weights:
                industry_weights[industry] = 0
            industry_weights[industry] += weight
        
        # 检查是否超限
        adjusted = weights.copy()
        for industry, ind_weight in industry_weights.items():
            if ind_weight > max_weight:
                # 等比例缩减
                scale = max_weight / ind_weight
                for stock, weight in adjusted.items():
                    if industry_map.get(stock) == industry:
                        adjusted[stock] = weight * scale
        
        # 重新归一化
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted
    
    def calculate_target_shares(
        self, 
        weights: Dict[str, float],
        prices: Dict[str, float],
        total_capital: float,
        lot_size: int = 100
    ) -> Dict[str, int]:
        """
        计算目标持仓股数
        
        Args:
            weights: 权重字典
            prices: 当前价格字典
            total_capital: 总资金
            lot_size: 最小交易单位 (手)
            
        Returns:
            目标股数字典
        """
        target_shares = {}
        
        for stock, weight in weights.items():
            if stock not in prices or prices[stock] <= 0:
                continue
            
            amount = total_capital * weight
            shares = int(amount / prices[stock] / lot_size) * lot_size
            target_shares[stock] = shares
        
        return target_shares
