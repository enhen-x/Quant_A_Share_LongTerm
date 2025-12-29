# src/strategy/scorer.py
"""因子评分系统"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from ..utils.config import load_config
from ..utils.logger import get_logger


class FactorScorer:
    """因子评分器: 将因子转换为综合得分"""
    
    def __init__(self, config: dict = None):
        self.logger = get_logger('scorer')
        
        if config is None:
            full_config = load_config()
            config = full_config.get('strategy', {})
        
        self.config = config
        
        # 因子权重
        self.weights = config.get('weights', {
            'valuation': 0.25,
            'quality': 0.30,
            'growth': 0.20,
            'momentum': 0.15,
            'dividend': 0.10,
        })
    
    def score_factors(
        self, 
        factors: pd.DataFrame,
        weights: Dict[str, float] = None
    ) -> pd.DataFrame:
        """
        计算因子得分
        
        Args:
            factors: 因子数据
            weights: 因子权重
            
        Returns:
            包含各维度得分和总分的 DataFrame
        """
        if weights is None:
            weights = self.weights
        
        result = pd.DataFrame(index=factors.index)
        
        # 估值因子得分 (越低越好，需要反转)
        val_cols = [c for c in factors.columns if 'pe' in c or 'pb' in c or 'ps' in c]
        if val_cols:
            # 使用分位数排名，PE 越低排名越高
            val_scores = []
            for col in val_cols:
                if 'percentile' in col:
                    # 分位数越低越好，所以用 1 - 分位数
                    score = (1 - factors[col]) * 100
                else:
                    # 估值越低越好，反向排名
                    score = (1 - factors[col].rank(pct=True)) * 100
                val_scores.append(score)
            result['score_valuation'] = pd.concat(val_scores, axis=1).mean(axis=1)
        
        # 质量因子得分 (ROE/ROA 越高越好)
        quality_cols = [c for c in factors.columns if 'roe' in c or 'roa' in c or 'margin' in c]
        if quality_cols:
            quality_scores = []
            for col in quality_cols:
                if 'debt' in col:
                    # 负债率越低越好
                    score = (1 - factors[col].rank(pct=True)) * 100
                else:
                    score = factors[col].rank(pct=True) * 100
                quality_scores.append(score)
            result['score_quality'] = pd.concat(quality_scores, axis=1).mean(axis=1)
        
        # 成长因子得分
        growth_cols = [c for c in factors.columns if 'yoy' in c or 'growth' in c]
        if growth_cols:
            growth_scores = factors[growth_cols].rank(pct=True).mean(axis=1) * 100
            result['score_growth'] = growth_scores
        
        # 动量因子得分
        mom_cols = [c for c in factors.columns if 'ret' in c or 'momentum' in c]
        if mom_cols:
            mom_scores = factors[mom_cols].rank(pct=True).mean(axis=1) * 100
            result['score_momentum'] = mom_scores
        
        # 股息因子得分
        div_cols = [c for c in factors.columns if 'dv' in c or 'dividend' in c]
        if div_cols:
            div_scores = factors[div_cols].rank(pct=True).mean(axis=1) * 100
            result['score_dividend'] = div_scores
        
        # 计算加权总分
        total = pd.Series(0, index=factors.index)
        for category, weight in weights.items():
            col = f'score_{category}'
            if col in result.columns:
                total += result[col].fillna(50) * weight  # 缺失值用 50 分
        
        result['score_total'] = total
        result['rank'] = result['score_total'].rank(ascending=False)
        
        return result
    
    def get_top_stocks(
        self, 
        scores: pd.DataFrame,
        top_k: int = None
    ) -> pd.DataFrame:
        """获取得分最高的 Top K 股票"""
        if top_k is None:
            top_k = self.config.get('top_k', 30)
        
        sorted_df = scores.sort_values('score_total', ascending=False)
        return sorted_df.head(top_k)
