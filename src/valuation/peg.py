# src/valuation/peg.py
"""PEG 估值模型"""

from typing import Dict


class PEGModel:
    """PEG 估值模型: 适用于成长股"""
    
    def __init__(self):
        pass
    
    def calculate_peg(
        self, 
        pe: float, 
        growth_rate: float
    ) -> float:
        """
        计算 PEG = PE / 盈利增速
        
        Args:
            pe: 市盈率
            growth_rate: 盈利增速 (百分比，如 30 表示 30%)
        """
        if growth_rate <= 0:
            return float('inf')
        return pe / growth_rate
    
    def assess_valuation(
        self, 
        pe: float,
        growth_rate: float
    ) -> Dict:
        """
        PEG 估值评估
        
        经典标准 (Peter Lynch):
        - PEG < 0.5: 严重低估
        - PEG < 1.0: 低估
        - PEG = 1.0: 合理
        - PEG > 1.5: 高估
        - PEG > 2.0: 严重高估
        """
        peg = self.calculate_peg(pe, growth_rate)
        
        if peg == float('inf'):
            verdict = "无法评估 (增速为负)"
        elif peg < 0.5:
            verdict = "严重低估"
        elif peg < 1.0:
            verdict = "低估"
        elif peg < 1.5:
            verdict = "估值合理"
        elif peg < 2.0:
            verdict = "轻度高估"
        else:
            verdict = "严重高估"
        
        return {
            "pe": pe,
            "growth_rate": growth_rate,
            "peg": peg if peg != float('inf') else None,
            "verdict": verdict,
            "peter_lynch_view": "符合买入标准" if peg < 1.0 else "不符合买入标准"
        }
