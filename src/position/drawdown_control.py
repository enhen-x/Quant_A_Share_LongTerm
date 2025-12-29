# src/position/drawdown_control.py
"""回撤控制策略"""

from typing import Dict
from ..utils.logger import get_logger


class DrawdownController:
    """最大回撤控制: 触及止损线时减仓/清仓"""
    
    def __init__(
        self, 
        max_stock_dd: float = 0.10,
        max_portfolio_dd: float = 0.15
    ):
        """
        Args:
            max_stock_dd: 单只股票最大回撤 (10%)
            max_portfolio_dd: 组合最大回撤 (15%)
        """
        self.max_stock_dd = max_stock_dd
        self.max_portfolio_dd = max_portfolio_dd
        self.logger = get_logger('drawdown_ctrl')
        
        # 记录最高点
        self.stock_peaks: Dict[str, float] = {}
        self.portfolio_peak: float = 0
    
    def update_peaks(
        self, 
        stock_values: Dict[str, float],
        portfolio_value: float
    ):
        """更新各标的和组合的最高点"""
        for stock, value in stock_values.items():
            if stock not in self.stock_peaks:
                self.stock_peaks[stock] = value
            else:
                self.stock_peaks[stock] = max(self.stock_peaks[stock], value)
        
        self.portfolio_peak = max(self.portfolio_peak, portfolio_value)
    
    def calculate_drawdown(
        self, 
        current_value: float, 
        peak_value: float
    ) -> float:
        """计算回撤幅度"""
        if peak_value <= 0:
            return 0
        return (peak_value - current_value) / peak_value
    
    def check_stock_drawdown(
        self, 
        stock: str, 
        current_value: float
    ) -> bool:
        """
        检查单只股票是否触发止损
        
        Returns:
            True 表示触发止损
        """
        peak = self.stock_peaks.get(stock, current_value)
        dd = self.calculate_drawdown(current_value, peak)
        
        if dd >= self.max_stock_dd:
            self.logger.warning(
                f"股票 {stock} 触发止损: 回撤 {dd:.2%} >= {self.max_stock_dd:.2%}"
            )
            return True
        return False
    
    def check_portfolio_drawdown(
        self, 
        current_value: float
    ) -> bool:
        """
        检查组合是否触发止损
        
        Returns:
            True 表示触发止损
        """
        dd = self.calculate_drawdown(current_value, self.portfolio_peak)
        
        if dd >= self.max_portfolio_dd:
            self.logger.warning(
                f"组合触发止损: 回撤 {dd:.2%} >= {self.max_portfolio_dd:.2%}"
            )
            return True
        return False
    
    def check_and_adjust(
        self,
        current_positions: Dict[str, float],
        current_values: Dict[str, float],
        portfolio_value: float
    ) -> Dict[str, float]:
        """
        检查并调整仓位
        
        Args:
            current_positions: 当前持仓权重
            current_values: 当前市值
            portfolio_value: 组合总值
            
        Returns:
            调整后的目标权重
        """
        self.update_peaks(current_values, portfolio_value)
        
        adjusted = current_positions.copy()
        
        # 检查组合回撤
        if self.check_portfolio_drawdown(portfolio_value):
            # 全部减半
            adjusted = {k: v * 0.5 for k, v in adjusted.items()}
            self.logger.info("组合回撤触发，全部仓位减半")
            return adjusted
        
        # 检查个股回撤
        for stock, value in current_values.items():
            if self.check_stock_drawdown(stock, value):
                # 清仓该股票
                adjusted[stock] = 0
                self.logger.info(f"股票 {stock} 回撤触发，清仓")
        
        return adjusted
