# src/position/position_manager.py
"""综合仓位管理器"""

from typing import Dict, List, Optional
import pandas as pd

from ..utils.config import load_config
from ..utils.logger import get_logger
from .fixed_position import FixedPositionSizer
from .risk_parity import RiskParitySizer
from .volatility_target import VolatilityTargetSizer
from .drawdown_control import DrawdownController


class PositionManager:
    """综合仓位管理器: 组合多种仓位策略"""
    
    def __init__(self, config: dict = None):
        """
        Args:
            config: 仓位管理配置
                {
                    "base_sizer": "risk_parity",
                    "vol_target": 0.15,
                    "max_single_weight": 0.10,
                    "max_industry_weight": 0.25,
                    "max_drawdown": 0.15,
                }
        """
        self.logger = get_logger('position_manager')
        
        if config is None:
            full_config = load_config()
            config = full_config.get('position', {})
        
        self.config = config
        
        # 基础仓位分配器
        base_method = config.get('base_sizer', 'equal_weight')
        if base_method == 'risk_parity':
            self.base_sizer = RiskParitySizer()
        else:
            self.base_sizer = FixedPositionSizer()
        
        # 波动率目标
        vol_target = config.get('vol_target', 0.15)
        self.vol_sizer = VolatilityTargetSizer(target_vol=vol_target)
        
        # 回撤控制
        max_dd = config.get('max_drawdown', 0.15)
        self.dd_controller = DrawdownController(
            max_portfolio_dd=max_dd
        )
        
        # 约束参数
        self.max_single_weight = config.get('max_single_weight', 0.10)
        self.max_industry_weight = config.get('max_industry_weight', 0.25)
        
        self.logger.info(f"仓位管理器初始化完成，基础方法: {base_method}")
    
    def calculate_target_weights(
        self,
        stocks: List[str],
        scores: pd.Series = None,
        returns: pd.DataFrame = None,
        industry_map: Dict[str, str] = None
    ) -> Dict[str, float]:
        """
        计算目标权重
        
        Args:
            stocks: 选中的股票列表
            scores: 股票得分 (可选)
            returns: 历史收益率 (可选)
            industry_map: 股票行业映射 (可选)
            
        Returns:
            目标权重字典
        """
        # 1. 基础分配
        if returns is not None:
            weights = self.base_sizer.calculate_weights(stocks, returns=returns)
        else:
            weights = self.base_sizer.calculate_weights(stocks)
        
        # 2. 应用单只股票上限
        weights = self._apply_single_cap(weights)
        
        # 3. 应用行业上限
        if industry_map:
            weights = self._apply_industry_cap(weights, industry_map)
        
        # 4. 波动率调整 (如果有收益率数据)
        if returns is not None and not returns.empty:
            realized_vol = self.vol_sizer.calculate_realized_volatility(
                returns.mean(axis=1)  # 组合平均收益
            )
            weights = self.vol_sizer.adjust_weights(weights, realized_vol)
        
        return weights
    
    def _apply_single_cap(
        self, 
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """应用单只股票上限"""
        capped = {}
        total_excess = 0
        n_below_cap = 0
        
        for stock, w in weights.items():
            if w > self.max_single_weight:
                capped[stock] = self.max_single_weight
                total_excess += w - self.max_single_weight
            else:
                capped[stock] = w
                n_below_cap += 1
        
        # 将超额部分分配给未达上限的股票
        if n_below_cap > 0 and total_excess > 0:
            extra_per_stock = total_excess / n_below_cap
            for stock in capped:
                if weights[stock] < self.max_single_weight:
                    capped[stock] += extra_per_stock
        
        return capped
    
    def _apply_industry_cap(
        self, 
        weights: Dict[str, float],
        industry_map: Dict[str, str]
    ) -> Dict[str, float]:
        """应用行业上限"""
        # 计算各行业权重
        industry_weights = {}
        for stock, w in weights.items():
            ind = industry_map.get(stock, 'Unknown')
            industry_weights[ind] = industry_weights.get(ind, 0) + w
        
        # 检查并调整超限行业
        adjusted = weights.copy()
        for ind, ind_w in industry_weights.items():
            if ind_w > self.max_industry_weight:
                scale = self.max_industry_weight / ind_w
                for stock, w in adjusted.items():
                    if industry_map.get(stock) == ind:
                        adjusted[stock] = w * scale
        
        # 归一化
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
        计算目标股数
        
        Args:
            weights: 权重字典
            prices: 当前价格
            total_capital: 总资金
            lot_size: 最小交易单位
            
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
