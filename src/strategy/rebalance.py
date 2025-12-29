# src/strategy/rebalance.py
"""调仓逻辑"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd

from ..utils.logger import get_logger


@dataclass
class Order:
    """交易订单"""
    ts_code: str
    direction: str  # 'BUY' or 'SELL'
    shares: int
    price: float = None
    reason: str = ""


class Rebalancer:
    """调仓管理器"""
    
    def __init__(self):
        self.logger = get_logger('rebalancer')
    
    def generate_rebalance_orders(
        self,
        current_positions: Dict[str, int],
        target_positions: Dict[str, int],
        prices: Dict[str, float]
    ) -> List[Order]:
        """
        生成调仓订单
        
        Args:
            current_positions: 当前持仓 {ts_code: shares}
            target_positions: 目标持仓 {ts_code: shares}
            prices: 当前价格
            
        Returns:
            订单列表
        """
        orders = []
        
        # 所有涉及的股票
        all_stocks = set(current_positions.keys()) | set(target_positions.keys())
        
        for stock in all_stocks:
            current = current_positions.get(stock, 0)
            target = target_positions.get(stock, 0)
            diff = target - current
            price = prices.get(stock, 0)
            
            if diff > 0:
                orders.append(Order(
                    ts_code=stock,
                    direction='BUY',
                    shares=diff,
                    price=price,
                    reason='调仓买入'
                ))
            elif diff < 0:
                orders.append(Order(
                    ts_code=stock,
                    direction='SELL',
                    shares=abs(diff),
                    price=price,
                    reason='调仓卖出'
                ))
        
        # 先卖后买排序
        sell_orders = [o for o in orders if o.direction == 'SELL']
        buy_orders = [o for o in orders if o.direction == 'BUY']
        
        return sell_orders + buy_orders
    
    def calculate_turnover(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> float:
        """
        计算换手率
        
        换手率 = sum(|target_weight - current_weight|) / 2
        """
        all_stocks = set(current_weights.keys()) | set(target_weights.keys())
        
        total_change = 0
        for stock in all_stocks:
            current = current_weights.get(stock, 0)
            target = target_weights.get(stock, 0)
            total_change += abs(target - current)
        
        return total_change / 2
    
    def estimate_transaction_cost(
        self,
        orders: List[Order],
        commission_rate: float = 0.001,
        stamp_tax_rate: float = 0.001
    ) -> float:
        """
        估算交易成本
        
        Args:
            orders: 订单列表
            commission_rate: 佣金率
            stamp_tax_rate: 印花税率 (仅卖出)
            
        Returns:
            总交易成本
        """
        total_cost = 0
        
        for order in orders:
            amount = order.shares * order.price
            
            # 佣金 (双向)
            commission = amount * commission_rate
            
            # 印花税 (仅卖出)
            stamp_tax = amount * stamp_tax_rate if order.direction == 'SELL' else 0
            
            total_cost += commission + stamp_tax
        
        return total_cost
    
    def apply_rebalance_threshold(
        self,
        orders: List[Order],
        threshold_pct: float = 0.02,
        total_portfolio_value: float = None
    ) -> List[Order]:
        """
        应用调仓阈值，过滤小额交易
        
        Args:
            orders: 原始订单
            threshold_pct: 阈值百分比 (相对于组合总值)
            total_portfolio_value: 组合总值
            
        Returns:
            过滤后的订单
        """
        if total_portfolio_value is None or total_portfolio_value <= 0:
            return orders
        
        threshold_amount = total_portfolio_value * threshold_pct
        
        filtered = []
        for order in orders:
            amount = order.shares * order.price
            if amount >= threshold_amount:
                filtered.append(order)
            else:
                self.logger.debug(
                    f"过滤小额订单: {order.ts_code} {order.direction} "
                    f"{order.shares} 股 (金额 {amount:.0f})"
                )
        
        return filtered
