# src/data_source/tushare_source.py
"""Tushare Pro API 数据源封装"""

import time
from typing import Optional, List, Dict, Any
from functools import wraps

import pandas as pd
import tushare as ts

from ..utils.config import load_config
from ..utils.logger import get_logger
from .base import DataSourceBase


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """API 调用重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


class TushareSource(DataSourceBase):
    """Tushare Pro API 数据源"""
    
    def __init__(
        self, 
        token: Optional[str] = None,
        http_url: Optional[str] = None
    ):
        """
        初始化 Tushare 数据源
        
        Args:
            token: Tushare Pro API Token (为 None 则从配置文件读取)
            http_url: 自定义 API 地址 (代理服务使用)
        """
        self.logger = get_logger('tushare_source')
        config = load_config()
        ts_config = config.get('tushare', {})
        
        # 获取 Token
        if token is None:
            token = ts_config.get('token')
        if not token:
            raise ValueError("未配置 Tushare Token")
        
        # 获取自定义 URL
        if http_url is None:
            http_url = ts_config.get('http_url')
        
        # 初始化 API
        self.pro = ts.pro_api(token)
        self.pro._DataApi__token = token
        
        # 设置代理服务地址
        if http_url:
            self.pro._DataApi__http_url = http_url
            self.logger.info(f"使用代理服务: {http_url}")
        
        # 配置参数
        self.timeout = ts_config.get('timeout', 30)
        self.max_retries = ts_config.get('retry', 3)
        self.rate_limit = ts_config.get('rate_limit', 200)
        
        self.logger.info("Tushare 数据源初始化完成")
    
    # =========================================================================
    # 基础信息
    # =========================================================================
    
    @retry_on_error()
    def get_stock_list(self, **kwargs) -> pd.DataFrame:
        """
        获取股票基础信息列表
        
        Returns:
            DataFrame: ts_code, symbol, name, area, industry, list_date, ...
        """
        df = self.pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,fullname,market,list_date,is_hs'
        )
        return df
    
    @retry_on_error()
    def get_trade_calendar(
        self, 
        start_date: str = None, 
        end_date: str = None
    ) -> pd.DataFrame:
        """
        获取交易日历
        
        Returns:
            DataFrame: exchange, cal_date, is_open, pretrade_date
        """
        df = self.pro.trade_cal(
            exchange='SSE',
            start_date=start_date,
            end_date=end_date,
            is_open=1
        )
        return df
    
    # =========================================================================
    # 市场行情数据
    # =========================================================================
    
    @retry_on_error()
    def get_daily(
        self, 
        ts_code: str = None, 
        trade_date: str = None,
        start_date: str = None, 
        end_date: str = None
    ) -> pd.DataFrame:
        """
        获取日线行情
        
        Args:
            ts_code: 股票代码 (如 000001.SZ)
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: ts_code, trade_date, open, high, low, close, 
                      pre_close, change, pct_chg, vol, amount
        """
        df = self.pro.daily(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        return df
    
    def get_daily_chunked(
        self, 
        ts_code: str, 
        start_date: str, 
        end_date: str,
        chunk_years: int = 3
    ) -> pd.DataFrame:
        """
        分段下载日线行情（代理服务优化版）
        
        将大的日期范围切分为多个小范围请求，避免代理服务超时
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            chunk_years: 每段年数 (默认3年)
            
        Returns:
            DataFrame: 合并后的日线数据
        """
        from datetime import datetime, timedelta
        
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        all_data = []
        current_start = start
        
        while current_start < end:
            current_end = min(
                current_start + timedelta(days=chunk_years * 365),
                end
            )
            
            try:
                df = self.get_daily(
                    ts_code=ts_code,
                    start_date=current_start.strftime('%Y%m%d'),
                    end_date=current_end.strftime('%Y%m%d')
                )
                if not df.empty:
                    all_data.append(df)
            except Exception as e:
                self.logger.warning(f"获取 {ts_code} {current_start.strftime('%Y%m%d')}-{current_end.strftime('%Y%m%d')} 失败: {e}")
            
            current_start = current_end + timedelta(days=1)
        
        if all_data:
            return pd.concat(all_data, ignore_index=True).drop_duplicates(
                subset=['ts_code', 'trade_date']
            ).sort_values('trade_date', ascending=False)
        return pd.DataFrame()
    
    @retry_on_error()
    def get_weekly(
        self, 
        ts_code: str = None, 
        trade_date: str = None,
        start_date: str = None, 
        end_date: str = None
    ) -> pd.DataFrame:
        """获取周线行情"""
        df = self.pro.weekly(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        return df
    
    @retry_on_error()
    def get_monthly(
        self, 
        ts_code: str = None, 
        trade_date: str = None,
        start_date: str = None, 
        end_date: str = None
    ) -> pd.DataFrame:
        """获取月线行情"""
        df = self.pro.monthly(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        return df
    
    @retry_on_error()
    def get_daily_basic(
        self, 
        ts_code: str = None,
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        获取每日指标
        
        Returns:
            DataFrame: ts_code, trade_date, close, turnover_rate, turnover_rate_f,
                      volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm,
                      total_share, float_share, free_share, total_mv, circ_mv
        """
        df = self.pro.daily_basic(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,'
                   'volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,'
                   'total_share,float_share,free_share,total_mv,circ_mv'
        )
        return df
    
    @retry_on_error()
    def get_adj_factor(
        self, 
        ts_code: str = None,
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        获取复权因子
        
        Returns:
            DataFrame: ts_code, trade_date, adj_factor
        """
        df = self.pro.adj_factor(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        return df
    
    @retry_on_error()
    def get_suspend(
        self, 
        ts_code: str = None,
        suspend_type: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取停复牌信息"""
        df = self.pro.suspend_d(
            ts_code=ts_code,
            suspend_type=suspend_type,
            start_date=start_date,
            end_date=end_date
        )
        return df
    
    # =========================================================================
    # 基本面数据
    # =========================================================================
    
    @retry_on_error()
    def get_income(
        self, 
        ts_code: str = None,
        ann_date: str = None,
        start_date: str = None,
        end_date: str = None,
        period: str = None,
        report_type: str = None
    ) -> pd.DataFrame:
        """
        获取利润表
        
        Returns:
            DataFrame: 包含营收、净利润、毛利等字段
        """
        df = self.pro.income(
            ts_code=ts_code,
            ann_date=ann_date,
            start_date=start_date,
            end_date=end_date,
            period=period,
            report_type=report_type
        )
        return df
    
    @retry_on_error()
    def get_balancesheet(
        self, 
        ts_code: str = None,
        ann_date: str = None,
        start_date: str = None,
        end_date: str = None,
        period: str = None,
        report_type: str = None
    ) -> pd.DataFrame:
        """
        获取资产负债表
        
        Returns:
            DataFrame: 包含资产、负债、所有者权益等字段
        """
        df = self.pro.balancesheet(
            ts_code=ts_code,
            ann_date=ann_date,
            start_date=start_date,
            end_date=end_date,
            period=period,
            report_type=report_type
        )
        return df
    
    @retry_on_error()
    def get_cashflow(
        self, 
        ts_code: str = None,
        ann_date: str = None,
        start_date: str = None,
        end_date: str = None,
        period: str = None,
        report_type: str = None
    ) -> pd.DataFrame:
        """
        获取现金流量表
        
        Returns:
            DataFrame: 包含经营、投资、筹资活动现金流
        """
        df = self.pro.cashflow(
            ts_code=ts_code,
            ann_date=ann_date,
            start_date=start_date,
            end_date=end_date,
            period=period,
            report_type=report_type
        )
        return df
    
    @retry_on_error()
    def get_fina_indicator(
        self, 
        ts_code: str = None,
        ann_date: str = None,
        start_date: str = None,
        end_date: str = None,
        period: str = None
    ) -> pd.DataFrame:
        """
        获取财务指标
        
        Returns:
            DataFrame: ROE, ROA, 毛利率, 净利率等财务指标
        """
        df = self.pro.fina_indicator(
            ts_code=ts_code,
            ann_date=ann_date,
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        return df
    
    @retry_on_error()
    def get_forecast(
        self, 
        ts_code: str = None,
        ann_date: str = None,
        start_date: str = None,
        end_date: str = None,
        period: str = None
    ) -> pd.DataFrame:
        """获取业绩预告"""
        df = self.pro.forecast(
            ts_code=ts_code,
            ann_date=ann_date,
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        return df
    
    @retry_on_error()
    def get_express(
        self, 
        ts_code: str = None,
        ann_date: str = None,
        start_date: str = None,
        end_date: str = None,
        period: str = None
    ) -> pd.DataFrame:
        """获取业绩快报"""
        df = self.pro.express(
            ts_code=ts_code,
            ann_date=ann_date,
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        return df
    
    @retry_on_error()
    def get_dividend(
        self, 
        ts_code: str = None,
        ann_date: str = None,
        record_date: str = None,
        ex_date: str = None
    ) -> pd.DataFrame:
        """获取分红送股信息"""
        df = self.pro.dividend(
            ts_code=ts_code,
            ann_date=ann_date,
            record_date=record_date,
            ex_date=ex_date
        )
        return df
    
    # =========================================================================
    # 宏观经济数据
    # =========================================================================
    
    @retry_on_error()
    def get_cn_gdp(self) -> pd.DataFrame:
        """获取中国 GDP 数据"""
        df = self.pro.cn_gdp()
        return df
    
    @retry_on_error()
    def get_cn_cpi(
        self, 
        start_m: str = None, 
        end_m: str = None
    ) -> pd.DataFrame:
        """获取中国 CPI 数据"""
        df = self.pro.cn_cpi(start_m=start_m, end_m=end_m)
        return df
    
    @retry_on_error()
    def get_cn_ppi(
        self, 
        start_m: str = None, 
        end_m: str = None
    ) -> pd.DataFrame:
        """获取中国 PPI 数据"""
        df = self.pro.cn_ppi(start_m=start_m, end_m=end_m)
        return df
    
    @retry_on_error()
    def get_cn_pmi(
        self, 
        start_m: str = None, 
        end_m: str = None
    ) -> pd.DataFrame:
        """获取中国 PMI 数据"""
        # 注意: 部分接口可能需要更高积分
        try:
            df = self.pro.cn_pmi(start_m=start_m, end_m=end_m)
            return df
        except Exception as e:
            self.logger.warning(f"获取 PMI 数据失败: {e}")
            return pd.DataFrame()
    
    @retry_on_error()
    def get_cn_m(self) -> pd.DataFrame:
        """获取货币供应量 (M0/M1/M2)"""
        df = self.pro.cn_m()
        return df
    
    @retry_on_error()
    def get_shibor(
        self, 
        start_date: str = None, 
        end_date: str = None
    ) -> pd.DataFrame:
        """获取 SHIBOR 利率"""
        df = self.pro.shibor(start_date=start_date, end_date=end_date)
        return df
    
    # =========================================================================
    # 行业数据
    # =========================================================================
    
    @retry_on_error()
    def get_index_classify(
        self, 
        index_code: str = None,
        level: str = None,
        src: str = 'SW2021'
    ) -> pd.DataFrame:
        """
        获取申万行业分类
        
        Args:
            level: 行业级别 (L1/L2/L3)
            src: 来源 (SW2021)
        """
        df = self.pro.index_classify(
            index_code=index_code,
            level=level,
            src=src
        )
        return df
    
    @retry_on_error()
    def get_index_member(
        self, 
        index_code: str = None,
        ts_code: str = None,
        is_new: str = None
    ) -> pd.DataFrame:
        """获取申万行业成分股"""
        df = self.pro.index_member(
            index_code=index_code,
            ts_code=ts_code,
            is_new=is_new
        )
        return df
    
    @retry_on_error()
    def get_sw_daily(
        self, 
        ts_code: str = None,
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取申万行业指数日线"""
        df = self.pro.sw_daily(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        return df
    
    # =========================================================================
    # 指数数据
    # =========================================================================
    
    @retry_on_error()
    def get_index_basic(
        self, 
        market: str = None,
        publisher: str = None,
        category: str = None
    ) -> pd.DataFrame:
        """获取指数基本信息"""
        df = self.pro.index_basic(
            market=market,
            publisher=publisher,
            category=category
        )
        return df
    
    @retry_on_error()
    def get_index_daily(
        self, 
        ts_code: str = None,
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取指数日线行情"""
        df = self.pro.index_daily(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        return df
    
    @retry_on_error()
    def get_index_weight(
        self, 
        index_code: str,
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取指数成分和权重"""
        df = self.pro.index_weight(
            index_code=index_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        return df
