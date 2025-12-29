# src/valuation/dcf.py
"""现金流折现模型"""

from typing import Optional, Dict, Any
import numpy as np


class DCFModel:
    """现金流折现 (Discounted Cash Flow) 估值模型"""
    
    def __init__(
        self,
        discount_rate: float = 0.10,
        terminal_growth: float = 0.03,
        forecast_years: int = 5
    ):
        """
        Args:
            discount_rate: 折现率 (如 10%)
            terminal_growth: 永续增长率 (如 3%)
            forecast_years: 预测年数
        """
        self.discount_rate = discount_rate
        self.terminal_growth = terminal_growth
        self.forecast_years = forecast_years
    
    def calculate_intrinsic_value(
        self,
        current_fcf: float,
        growth_rates: list = None,
        shares_outstanding: float = 1
    ) -> Dict[str, Any]:
        """
        计算内在价值
        
        Args:
            current_fcf: 当前自由现金流
            growth_rates: 各年增长率列表 (不提供则使用默认)
            shares_outstanding: 总股本
            
        Returns:
            {
                "intrinsic_value": 内在价值,
                "per_share_value": 每股内在价值,
                "fcf_forecast": 预测现金流列表,
                "terminal_value": 终值
            }
        """
        if growth_rates is None:
            growth_rates = [0.15] * self.forecast_years  # 默认 15% 增速
        
        r = self.discount_rate
        g = self.terminal_growth
        
        # 预测各年现金流
        fcf_list = []
        fcf = current_fcf
        for rate in growth_rates:
            fcf = fcf * (1 + rate)
            fcf_list.append(fcf)
        
        # 折现各年现金流
        pv_fcf = sum(
            fcf_list[i] / ((1 + r) ** (i + 1)) 
            for i in range(len(fcf_list))
        )
        
        # 计算终值
        terminal_fcf = fcf_list[-1] * (1 + g)
        terminal_value = terminal_fcf / (r - g)
        
        # 终值折现到现在
        pv_terminal = terminal_value / ((1 + r) ** len(fcf_list))
        
        # 企业价值
        enterprise_value = pv_fcf + pv_terminal
        
        # 每股价值
        per_share = enterprise_value / shares_outstanding if shares_outstanding > 0 else 0
        
        return {
            "intrinsic_value": enterprise_value,
            "per_share_value": per_share,
            "fcf_forecast": fcf_list,
            "terminal_value": terminal_value,
            "pv_fcf": pv_fcf,
            "pv_terminal": pv_terminal,
        }
    
    def calculate_margin_of_safety(
        self,
        intrinsic_value: float,
        current_price: float
    ) -> float:
        """
        计算安全边际
        
        MoS = (内在价值 - 当前价格) / 内在价值
        """
        if intrinsic_value <= 0:
            return 0
        return (intrinsic_value - current_price) / intrinsic_value
