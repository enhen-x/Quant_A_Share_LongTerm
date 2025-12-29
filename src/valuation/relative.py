# src/valuation/relative.py
"""相对估值模型"""

from typing import Dict, Optional
import pandas as pd
import numpy as np


class RelativeValuation:
    """相对估值: 历史分位 + 同业对比"""
    
    def __init__(self):
        pass
    
    def calculate_percentile(
        self, 
        current_value: float,
        history: pd.Series
    ) -> float:
        """
        计算当前值在历史中的分位数
        
        Returns:
            分位数 (0-1)
        """
        if len(history) == 0:
            return 0.5
        return (history < current_value).sum() / len(history)
    
    def calculate_zscore(
        self, 
        current_value: float,
        history: pd.Series
    ) -> float:
        """
        计算 Z-Score
        
        Z = (X - μ) / σ
        """
        mean = history.mean()
        std = history.std()
        if std == 0:
            return 0
        return (current_value - mean) / std
    
    def assess_historical(
        self, 
        current_pe: float,
        pe_history: pd.Series,
        current_pb: float = None,
        pb_history: pd.Series = None
    ) -> Dict:
        """
        历史分位评估
        
        Returns:
            {
                "pe_percentile": PE 历史分位,
                "pb_percentile": PB 历史分位,
                "overall_verdict": 综合判断
            }
        """
        pe_pct = self.calculate_percentile(current_pe, pe_history)
        
        result = {
            "current_pe": current_pe,
            "pe_percentile": pe_pct,
            "pe_verdict": self._percentile_to_verdict(pe_pct),
        }
        
        if current_pb is not None and pb_history is not None:
            pb_pct = self.calculate_percentile(current_pb, pb_history)
            result.update({
                "current_pb": current_pb,
                "pb_percentile": pb_pct,
                "pb_verdict": self._percentile_to_verdict(pb_pct),
            })
            
            # 综合判断
            avg_pct = (pe_pct + pb_pct) / 2
        else:
            avg_pct = pe_pct
        
        result["overall_verdict"] = self._percentile_to_verdict(avg_pct)
        result["temperature"] = self._percentile_to_temperature(avg_pct)
        
        return result
    
    def _percentile_to_verdict(self, pct: float) -> str:
        """分位数转换为判断"""
        if pct < 0.1:
            return "极度低估"
        elif pct < 0.25:
            return "明显低估"
        elif pct < 0.4:
            return "轻度低估"
        elif pct < 0.6:
            return "估值合理"
        elif pct < 0.75:
            return "轻度高估"
        elif pct < 0.9:
            return "明显高估"
        else:
            return "极度高估"
    
    def _percentile_to_temperature(self, pct: float) -> str:
        """分位数转换为温度"""
        if pct < 0.3:
            return "🟢 偏冷"
        elif pct < 0.7:
            return "🟡 中性"
        else:
            return "🔴 偏热"
    
    def compare_with_peers(
        self, 
        stock_metrics: Dict[str, float],
        peer_metrics: pd.DataFrame
    ) -> Dict:
        """
        同业对比
        
        Args:
            stock_metrics: 目标股票指标 {"pe": 10, "pb": 1.5, ...}
            peer_metrics: 同业指标 DataFrame
            
        Returns:
            各指标相对同业的位置
        """
        result = {}
        
        for metric, value in stock_metrics.items():
            if metric in peer_metrics.columns:
                peers = peer_metrics[metric].dropna()
                median = peers.median()
                pct = self.calculate_percentile(value, peers)
                
                vs_median = (value - median) / median if median != 0 else 0
                
                result[metric] = {
                    "value": value,
                    "peer_median": median,
                    "vs_median_pct": vs_median,
                    "percentile_in_peers": pct,
                    "verdict": "高于同业" if vs_median > 0.1 else (
                        "低于同业" if vs_median < -0.1 else "接近同业"
                    )
                }
        
        return result
