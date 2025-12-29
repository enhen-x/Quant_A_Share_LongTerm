# src/data_source/datahub.py
"""统一数据入口"""

from typing import Optional, Dict, Any, List, Union
from pathlib import Path

import pandas as pd

from ..utils.config import load_config, get_data_path
from ..utils.logger import get_logger
from ..utils.io import load_parquet, save_parquet, ensure_dir
from .tushare_source import TushareSource


class DataHub:
    """
    统一数据入口
    
    提供数据获取的统一接口，支持:
    - 从 Tushare API 实时获取
    - 从本地缓存读取
    - 自动缓存管理
    """
    
    def __init__(self, use_cache: bool = True):
        """
        初始化数据中心
        
        Args:
            use_cache: 是否使用本地缓存
        """
        self.logger = get_logger('datahub')
        self.use_cache = use_cache
        self.config = load_config()
        
        # 初始化数据源
        self._ts_source = None
        
        # 数据路径
        self.raw_path = get_data_path('raw')
        self.processed_path = get_data_path('processed')
        self.meta_path = get_data_path('meta')
        
        self.logger.info("DataHub 初始化完成")
    
    @property
    def ts(self) -> TushareSource:
        """获取 Tushare 数据源 (惰性初始化)"""
        if self._ts_source is None:
            self._ts_source = TushareSource()
        return self._ts_source
    
    # =========================================================================
    # 股票基础信息
    # =========================================================================
    
    def get_stock_list(
        self, 
        force_update: bool = False
    ) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            force_update: 强制从 API 更新
            
        Returns:
            DataFrame: 股票基础信息
        """
        cache_file = self.meta_path / 'stock_basic.parquet'
        
        if self.use_cache and cache_file.exists() and not force_update:
            return load_parquet(cache_file)
        
        df = self.ts.get_stock_list()
        
        if self.use_cache and not df.empty:
            save_parquet(df, cache_file)
        
        return df
    
    def get_trade_calendar(
        self, 
        start_date: str = None, 
        end_date: str = None,
        force_update: bool = False
    ) -> pd.DataFrame:
        """获取交易日历"""
        cache_file = self.meta_path / 'trade_cal.parquet'
        
        if self.use_cache and cache_file.exists() and not force_update:
            df = load_parquet(cache_file)
            if start_date or end_date:
                if start_date:
                    df = df[df['cal_date'] >= start_date]
                if end_date:
                    df = df[df['cal_date'] <= end_date]
            return df
        
        df = self.ts.get_trade_calendar(start_date, end_date)
        
        if self.use_cache and not df.empty:
            save_parquet(df, cache_file)
        
        return df
    
    # =========================================================================
    # 市场行情
    # =========================================================================
    
    def get_daily(
        self, 
        ts_code: str = None,
        trade_date: str = None,
        start_date: str = None, 
        end_date: str = None,
        use_cache: bool = None
    ) -> pd.DataFrame:
        """
        获取日线行情
        
        支持按股票代码或按交易日期获取
        """
        if use_cache is None:
            use_cache = self.use_cache
        
        # 直接从 API 获取
        return self.ts.get_daily(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_daily_basic(
        self, 
        ts_code: str = None,
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取每日指标 (PE/PB/市值等)"""
        return self.ts.get_daily_basic(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_adj_factor(
        self, 
        ts_code: str = None,
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取复权因子"""
        return self.ts.get_adj_factor(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
    
    # =========================================================================
    # 基本面数据
    # =========================================================================
    
    def get_income(
        self, 
        ts_code: str = None,
        period: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取利润表"""
        return self.ts.get_income(
            ts_code=ts_code,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_balancesheet(
        self, 
        ts_code: str = None,
        period: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取资产负债表"""
        return self.ts.get_balancesheet(
            ts_code=ts_code,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_cashflow(
        self, 
        ts_code: str = None,
        period: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取现金流量表"""
        return self.ts.get_cashflow(
            ts_code=ts_code,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_fina_indicator(
        self, 
        ts_code: str = None,
        period: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取财务指标"""
        return self.ts.get_fina_indicator(
            ts_code=ts_code,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_dividend(
        self, 
        ts_code: str = None,
        ann_date: str = None
    ) -> pd.DataFrame:
        """获取分红送股"""
        return self.ts.get_dividend(ts_code=ts_code, ann_date=ann_date)
    
    # =========================================================================
    # 宏观数据
    # =========================================================================
    
    def get_cn_gdp(self) -> pd.DataFrame:
        """获取 GDP 数据"""
        return self.ts.get_cn_gdp()
    
    def get_cn_cpi(
        self, 
        start_m: str = None,
        end_m: str = None
    ) -> pd.DataFrame:
        """获取 CPI 数据"""
        return self.ts.get_cn_cpi(start_m=start_m, end_m=end_m)
    
    def get_cn_ppi(
        self, 
        start_m: str = None,
        end_m: str = None
    ) -> pd.DataFrame:
        """获取 PPI 数据"""
        return self.ts.get_cn_ppi(start_m=start_m, end_m=end_m)
    
    def get_shibor(
        self, 
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取 SHIBOR 利率"""
        return self.ts.get_shibor(start_date=start_date, end_date=end_date)
    
    # =========================================================================
    # 行业数据
    # =========================================================================
    
    def get_sw_industry(
        self, 
        level: str = 'L1'
    ) -> pd.DataFrame:
        """获取申万行业分类"""
        return self.ts.get_index_classify(level=level)
    
    def get_sw_members(
        self, 
        index_code: str = None,
        ts_code: str = None
    ) -> pd.DataFrame:
        """获取申万行业成分股"""
        return self.ts.get_index_member(
            index_code=index_code,
            ts_code=ts_code
        )
    
    def get_sw_daily(
        self, 
        ts_code: str = None,
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取申万指数日线"""
        return self.ts.get_sw_daily(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
    
    # =========================================================================
    # 指数数据
    # =========================================================================
    
    def get_index_daily(
        self, 
        ts_code: str = None,
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取指数日线"""
        return self.ts.get_index_daily(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_index_weight(
        self, 
        index_code: str,
        trade_date: str = None
    ) -> pd.DataFrame:
        """获取指数成分和权重"""
        return self.ts.get_index_weight(
            index_code=index_code,
            trade_date=trade_date
        )
