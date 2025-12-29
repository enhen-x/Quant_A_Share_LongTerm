# src/factors/valuation.py
"""估值因子计算"""

from typing import Optional
import pandas as pd
import numpy as np


class ValuationFactors:
    """估值因子计算器"""
    
    def __init__(self, config: dict = None):
        """
        初始化估值因子计算器
        
        Args:
            config: 因子配置
        """
        self.config = config or {}
        self.pe_window = self.config.get('pe_percentile_window', 1260)
        self.pb_window = self.config.get('pb_percentile_window', 1260)
    
    def calc_pe_percentile(
        self, 
        df: pd.DataFrame, 
        window: int = None
    ) -> pd.Series:
        """
        计算 PE 历史分位数
        
        Args:
            df: 包含 pe_ttm 列的数据
            window: 滚动窗口 (默认 5 年)
            
        Returns:
            PE 分位数序列 (0-1)
        """
        if window is None:
            window = self.pe_window
        
        pe = df['pe_ttm']
        
        def percentile_rank(x):
            if len(x) < 10:
                return np.nan
            return (x.values[-1] > x.values[:-1]).sum() / (len(x) - 1)
        
        return pe.rolling(window=window, min_periods=100).apply(
            percentile_rank, raw=False
        )
    
    def calc_pb_percentile(
        self, 
        df: pd.DataFrame, 
        window: int = None
    ) -> pd.Series:
        """计算 PB 历史分位数"""
        if window is None:
            window = self.pb_window
        
        pb = df['pb']
        
        def percentile_rank(x):
            if len(x) < 10:
                return np.nan
            return (x.values[-1] > x.values[:-1]).sum() / (len(x) - 1)
        
        return pb.rolling(window=window, min_periods=100).apply(
            percentile_rank, raw=False
        )
    
    def calc_pb_roe_score(self, df: pd.DataFrame) -> pd.Series:
        """
        PB-ROE 打分: 低 PB + 高 ROE = 高分
        
        适用于金融、地产等行业
        """
        # 需要 pb 和 roe 数据
        if 'pb' not in df.columns or 'roe' not in df.columns:
            raise ValueError("需要 pb 和 roe 列")
        
        # PB 越低越好，ROE 越高越好
        # 使用 ROE/PB 作为评分基础
        score = df['roe'] / df['pb'].clip(lower=0.1)
        
        # 标准化到 0-100
        score_pct = score.rank(pct=True) * 100
        return score_pct
    
    def calc_peg(
        self, 
        pe: pd.Series, 
        eps_growth: pd.Series
    ) -> pd.Series:
        """
        计算 PEG = PE / 预期盈利增速
        
        PEG < 1 表示相对成长性低估
        """
        # 避免除以 0 或负数
        growth = eps_growth.clip(lower=1)  # 最低 1%
        peg = pe / growth
        return peg
    
    def calc_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有估值因子"""
        result = pd.DataFrame(index=df.index)
        
        if 'pe_ttm' in df.columns:
            result['factor_pe_ttm'] = df['pe_ttm']
            result['factor_pe_percentile'] = self.calc_pe_percentile(df)
        
        if 'pb' in df.columns:
            result['factor_pb'] = df['pb']
            result['factor_pb_percentile'] = self.calc_pb_percentile(df)
        
        if 'ps_ttm' in df.columns:
            result['factor_ps_ttm'] = df['ps_ttm']
        
        return result
