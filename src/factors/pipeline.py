# src/factors/pipeline.py
"""因子计算流水线"""

from typing import Dict, List, Optional
import pandas as pd

from ..utils.config import load_config
from ..utils.logger import get_logger
from .valuation import ValuationFactors
from .quality import QualityFactors
from .growth import GrowthFactors
from .momentum import MomentumFactors
from .dividend import DividendFactors


class FactorPipeline:
    """因子计算流水线"""
    
    def __init__(self, config: dict = None):
        """
        初始化因子流水线
        
        Args:
            config: 因子配置
        """
        self.logger = get_logger('factor_pipeline')
        
        if config is None:
            full_config = load_config()
            config = full_config.get('factors', {})
        
        self.config = config
        
        # 初始化各类因子计算器
        self.valuation = ValuationFactors(config.get('valuation', {}))
        self.quality = QualityFactors(config.get('quality', {}))
        self.growth = GrowthFactors(config.get('growth', {}))
        self.momentum = MomentumFactors(config.get('momentum', {}))
        self.dividend = DividendFactors(config.get('dividend', {}))
        
        self.logger.info("因子流水线初始化完成")
    
    def calculate_all_factors(
        self, 
        market_data: pd.DataFrame,
        fundamental_data: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        计算所有因子
        
        Args:
            market_data: 市场数据 (daily_basic)
            fundamental_data: 基本面数据 (fina_indicator)
            
        Returns:
            包含所有因子的 DataFrame
        """
        self.logger.info("开始计算因子...")
        
        results = []
        
        # 估值因子
        self.logger.info("计算估值因子...")
        val_factors = self.valuation.calc_all(market_data)
        results.append(val_factors)
        
        # 动量因子 (基于市场数据)
        if 'close' in market_data.columns:
            self.logger.info("计算动量因子...")
            mom_factors = self.momentum.calc_all(market_data)
            results.append(mom_factors)
        
        # 股息因子
        self.logger.info("计算股息因子...")
        div_factors = self.dividend.calc_all(market_data)
        results.append(div_factors)
        
        # 基本面因子 (如果有数据)
        if fundamental_data is not None and not fundamental_data.empty:
            self.logger.info("计算质量因子...")
            quality_factors = self.quality.calc_all(fundamental_data)
            results.append(quality_factors)
            
            self.logger.info("计算成长因子...")
            growth_factors = self.growth.calc_all(fundamental_data)
            results.append(growth_factors)
        
        # 合并所有因子
        if results:
            all_factors = pd.concat(results, axis=1)
        else:
            all_factors = pd.DataFrame()
        
        self.logger.info(f"因子计算完成，共 {len(all_factors.columns)} 个因子")
        return all_factors
    
    def normalize_factors(
        self, 
        factors: pd.DataFrame,
        method: str = 'zscore'
    ) -> pd.DataFrame:
        """
        因子标准化
        
        Args:
            factors: 因子数据
            method: 标准化方法 ('zscore', 'rank', 'minmax')
            
        Returns:
            标准化后的因子
        """
        if method == 'zscore':
            return (factors - factors.mean()) / factors.std()
        elif method == 'rank':
            return factors.rank(pct=True)
        elif method == 'minmax':
            return (factors - factors.min()) / (factors.max() - factors.min())
        else:
            raise ValueError(f"未知的标准化方法: {method}")
    
    def winsorize_factors(
        self, 
        factors: pd.DataFrame,
        lower: float = 0.01,
        upper: float = 0.99
    ) -> pd.DataFrame:
        """
        因子去极值
        
        Args:
            factors: 因子数据
            lower: 下分位数
            upper: 上分位数
            
        Returns:
            去极值后的因子
        """
        def winsorize_col(col):
            lower_val = col.quantile(lower)
            upper_val = col.quantile(upper)
            return col.clip(lower=lower_val, upper=upper_val)
        
        return factors.apply(winsorize_col)
