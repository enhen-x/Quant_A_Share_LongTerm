# src/valuation/pb_roe.py
"""PB-ROE 估值模型"""

from typing import Optional, Dict
import pandas as pd
import numpy as np


class PBROEModel:
    """PB-ROE 估值模型: 适用于金融、地产等行业"""
    
    def __init__(self):
        pass
    
    def calculate_pb_roe_score(
        self, 
        pb: float, 
        roe: float
    ) -> float:
        """
        计算 PB-ROE 综合得分
        
        理念: 低 PB + 高 ROE = 高价值
        即: ROE/PB 越高越好
        """
        if pb <= 0:
            return 0
        return roe / pb
    
    def calculate_fair_pb(
        self, 
        roe: float, 
        cost_of_equity: float = 0.10,
        growth_rate: float = 0.03
    ) -> float:
        """
        基于 ROE 计算合理 PB
        
        Gordon Growth Model 推导:
        Fair PB = (ROE - g) / (r - g)
        
        Args:
            roe: 净资产收益率
            cost_of_equity: 股权成本 (折现率)
            growth_rate: 永续增长率
        """
        r = cost_of_equity
        g = growth_rate
        
        if r <= g:
            return float('inf')
        
        fair_pb = (roe - g) / (r - g)
        return max(fair_pb, 0)
    
    def assess_valuation(
        self, 
        current_pb: float,
        current_roe: float,
        cost_of_equity: float = 0.10
    ) -> Dict:
        """
        估值评估
        
        Returns:
            {
                "current_pb": 当前 PB,
                "fair_pb": 合理 PB,
                "upside": 隐含上涨空间,
                "verdict": 判断结论
            }
        """
        fair_pb = self.calculate_fair_pb(current_roe, cost_of_equity)
        
        if fair_pb == float('inf'):
            upside = 0
            verdict = "无法评估"
        else:
            upside = (fair_pb - current_pb) / current_pb if current_pb > 0 else 0
            
            if upside > 0.3:
                verdict = "明显低估"
            elif upside > 0.1:
                verdict = "轻度低估"
            elif upside > -0.1:
                verdict = "估值合理"
            elif upside > -0.3:
                verdict = "轻度高估"
            else:
                verdict = "明显高估"
        
        return {
            "current_pb": current_pb,
            "current_roe": current_roe,
            "fair_pb": fair_pb,
            "upside": upside,
            "verdict": verdict
        }
