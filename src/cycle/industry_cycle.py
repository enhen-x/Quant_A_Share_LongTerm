# src/cycle/industry_cycle.py
"""行业景气周期分析"""

from typing import Dict, List
import pandas as pd
import numpy as np

from ..utils.logger import get_logger


class IndustryCycleAnalyzer:
    """行业景气周期分析器"""
    
    def __init__(self):
        self.logger = get_logger('industry_cycle')
    
    def calculate_industry_sentiment(
        self, 
        industry_data: pd.DataFrame
    ) -> pd.Series:
        """
        计算行业景气度指标
        
        基于行业内公司的:
        - 平均营收增速
        - 平均利润增速
        - 平均 ROE 变化
        """
        sentiment = pd.Series(dtype=float)
        
        if 'revenue_yoy' in industry_data.columns:
            sentiment['revenue_growth'] = industry_data['revenue_yoy'].mean()
        
        if 'profit_yoy' in industry_data.columns:
            sentiment['profit_growth'] = industry_data['profit_yoy'].mean()
        
        if 'roe' in industry_data.columns:
            sentiment['avg_roe'] = industry_data['roe'].mean()
        
        return sentiment
    
    def classify_industry_phase(
        self, 
        revenue_growth: float,
        profit_growth: float
    ) -> str:
        """
        划分行业周期阶段
        
        Returns:
            - 'growth': 成长期 (营收↑, 利润↑)
            - 'mature': 成熟期 (营收→, 利润↑)
            - 'decline': 衰退期 (营收↓, 利润↓)
            - 'recovery': 复苏期 (营收↑, 利润→)
        """
        rev_up = revenue_growth > 10
        profit_up = profit_growth > 10
        
        if rev_up and profit_up:
            return 'growth'
        elif rev_up and not profit_up:
            return 'recovery'
        elif not rev_up and profit_up:
            return 'mature'
        else:
            return 'decline'
    
    def rank_industries(
        self, 
        industry_metrics: pd.DataFrame
    ) -> pd.DataFrame:
        """
        行业排名
        
        综合考虑增速、估值、景气度
        """
        rank_df = industry_metrics.copy()
        
        # 各指标排名 (越高越好)
        if 'revenue_growth' in rank_df.columns:
            rank_df['rev_rank'] = rank_df['revenue_growth'].rank(ascending=False)
        
        if 'profit_growth' in rank_df.columns:
            rank_df['profit_rank'] = rank_df['profit_growth'].rank(ascending=False)
        
        if 'avg_roe' in rank_df.columns:
            rank_df['roe_rank'] = rank_df['avg_roe'].rank(ascending=False)
        
        # 估值排名 (PE 越低越好)
        if 'avg_pe' in rank_df.columns:
            rank_df['pe_rank'] = rank_df['avg_pe'].rank(ascending=True)
        
        # 综合排名
        rank_cols = [c for c in rank_df.columns if c.endswith('_rank')]
        if rank_cols:
            rank_df['overall_rank'] = rank_df[rank_cols].mean(axis=1)
            rank_df = rank_df.sort_values('overall_rank')
        
        return rank_df
