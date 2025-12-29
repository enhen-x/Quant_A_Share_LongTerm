# src/position/volatility_target.py
"""目标波动率策略"""

from typing import Dict
import pandas as pd
import numpy as np

from ..utils.logger import get_logger


class VolatilityTargetSizer:
    """目标波动率: 根据市场波动动态调整整体仓位"""
    
    def __init__(self, target_vol: float = 0.15, max_leverage: float = 1.5):
        """
        Args:
            target_vol: 目标年化波动率 (如 15%)
            max_leverage: 最大杠杆倍数
        """
        self.target_vol = target_vol
        self.max_leverage = max_leverage
        self.logger = get_logger('vol_target')
    
    def calculate_position_ratio(
        self, 
        realized_vol: float
    ) -> float:
        """
        计算仓位比例
        
        position_ratio = target_vol / realized_vol
        
        - 市场波动高 → 降低仓位
        - 市场波动低 → 可以加仓
        
        Args:
            realized_vol: 实现波动率 (年化)
            
        Returns:
            仓位比例 (0-max_leverage)
        """
        if realized_vol <= 0:
            return 1.0
        
        ratio = self.target_vol / realized_vol
        
        # 限制在合理范围
        ratio = min(ratio, self.max_leverage)
        ratio = max(ratio, 0.2)  # 最低 20% 仓位
        
        self.logger.debug(
            f"实现波动率: {realized_vol:.2%}, "
            f"目标: {self.target_vol:.2%}, "
            f"仓位比例: {ratio:.2f}"
        )
        
        return ratio
    
    def calculate_realized_volatility(
        self, 
        returns: pd.Series,
        window: int = 20
    ) -> float:
        """
        计算实现波动率
        
        Args:
            returns: 收益率序列
            window: 计算窗口 (交易日)
            
        Returns:
            年化波动率
        """
        recent_returns = returns.tail(window)
        daily_vol = recent_returns.std()
        annual_vol = daily_vol * np.sqrt(252)
        return annual_vol
    
    def adjust_weights(
        self, 
        weights: Dict[str, float],
        realized_vol: float
    ) -> Dict[str, float]:
        """
        根据波动率调整权重
        
        Args:
            weights: 原始权重
            realized_vol: 实现波动率
            
        Returns:
            调整后的权重
        """
        ratio = self.calculate_position_ratio(realized_vol)
        
        # 调整所有权重
        adjusted = {k: v * ratio for k, v in weights.items()}
        
        return adjusted
