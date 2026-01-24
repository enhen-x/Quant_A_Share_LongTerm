"""
Tushare API 封装

提供 Tushare 数据源的各种获取功能
"""

import time
import os
import threading
import tushare as ts
from typing import Optional, Union, List
from datetime import datetime
import pandas as pd
from pathlib import Path
from ..utils.logger import get_logger
from ..utils.config import get_config
from ..utils.io import ensure_dir, write_parquet


class TushareSource:
    """Tushare 数据源"""

    _proxy_log_lock = threading.Lock()
    _proxy_logged = False

    def __init__(self, token: Optional[str] = None):
        """
        初始化 Tushare 连接

        Args:
            token: Tushare API token，默认从配置读取
        """
        self.config = get_config()
        self.logger = get_logger("tushare")

        if token is None:
            token = self.config.get("tushare.token")

        if not token or token == "YOUR_TUSHARE_TOKEN":
            raise ValueError("请先设置 Tushare Token")

        self.token = token

        # 设置 token
        ts.set_token(token)

        # 创建 pro 对象
        self.pro = ts.pro_api(token, timeout=self.config.get("tushare.timeout", 30))

        # 设置代理 URL（根据 Tushare 试用接口说明）
        http_url = self.config.get("tushare.http_url")
        if http_url:
            try:
                self.pro._DataApi__token = token
                self.pro._DataApi__http_url = http_url
                with self._proxy_log_lock:
                    if not self._proxy_logged:
                        self.logger.info(f"设置代理 URL: {http_url}")
                        self.__class__._proxy_logged = True
            except Exception as e:
                self.logger.warning(f"设置代理 URL 失败: {e}")

        # 从配置获取其他参数
        self.timeout = self.config.get("tushare.timeout", 30)
        self.retry = self.config.get("tushare.retry", 3)
        self.rate_limit = self.config.get("tushare.rate_limit", 200)

        # 请求间隔控制
        self.request_delay = 1.0 / self.rate_limit

    def _request_with_retry(self, func, *args, **kwargs):
        """
        带重试机制的请求

        Args:
            func: 请求函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            请求结果
        """
        for attempt in range(self.retry):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                if attempt < self.retry - 1:
                    wait_time = (attempt + 1) * 2
                    self.logger.debug(f"请求失败 (尝试 {attempt + 1}/{self.retry}): {e}")
                    self.logger.debug(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"请求失败 (尝试 {attempt + 1}/{self.retry}): {e}")
                    self.logger.error("请求失败，已达最大重试次数")
                    raise

    def get_daily(
        self,
        ts_code: str,
        start_date: str = "20100101",
        end_date: str = None,
        save: bool = False,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取日线行情数据

        Args:
            ts_code: 股票代码，如 "600519.SH"
            start_date: 开始日期，格式 "YYYYMMDD"
            end_date: 结束日期，格式 "YYYYMMDD"，默认为当前日期
            save: 是否保存到文件
            save_path: 保存路径，默认为 data/raw/market/daily/{ts_code}.parquet

        Returns:
            DataFrame 包含 OHLCV 数据
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        self.logger.debug(f"获取 {ts_code} 日线数据: {start_date} ~ {end_date}")

        df = self._request_with_retry(
            self.pro.daily,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )

        if df.empty:
            self.logger.debug(f"{ts_code} 数据为空")
            return df

        # 排序
        df = df.sort_values("trade_date").reset_index(drop=True)

        self.logger.debug(f"获取到 {len(df)} 条记录")

        if save:
            if save_path is None:
                save_path = f"data/raw/market/daily/{ts_code}.parquet"
            ensure_dir(Path(save_path).parent)
            write_parquet(df, save_path)
            self.logger.debug(f"数据已保存到 {save_path}")

        return df

    def get_daily_basic(
        self,
        ts_code: str,
        start_date: str = "20100101",
        end_date: str = None,
        save: bool = False,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取每日指标数据 (PE/PB/市值等)

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            save: 是否保存
            save_path: 保存路径

        Returns:
            DataFrame 包含每日指标
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        self.logger.debug(f"获取 {ts_code} 每日指标: {start_date} ~ {end_date}")

        df = self._request_with_retry(
            self.pro.daily_basic,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )

        if df.empty:
            self.logger.debug(f"{ts_code} 每日指标为空")
            return df

        df = df.sort_values("trade_date").reset_index(drop=True)

        self.logger.debug(f"获取到 {len(df)} 条记录")

        if save:
            if save_path is None:
                save_path = f"data/raw/market/daily_basic/{ts_code}.parquet"
            ensure_dir(Path(save_path).parent)
            write_parquet(df, save_path)
            self.logger.debug(f"数据已保存到 {save_path}")

        return df

    def get_index_daily(
        self,
        ts_code: str,
        start_date: str = "20100101",
        end_date: str = None,
        save: bool = False,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取指数日线行情

        Args:
            ts_code: 指数代码，如 "000001.SH"
            start_date: 开始日期
            end_date: 结束日期
            save: 是否保存
            save_path: 保存路径

        Returns:
            DataFrame 包含指数行情
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        self.logger.debug(f"获取指数 {ts_code} 日线数据: {start_date} ~ {end_date}")

        df = self._request_with_retry(
            self.pro.index_daily,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )

        if df.empty:
            self.logger.debug(f"{ts_code} 指数数据为空")
            return df

        df = df.sort_values("trade_date").reset_index(drop=True)

        self.logger.debug(f"获取到 {len(df)} 条记录")

        if save:
            if save_path is None:
                save_path = f"data/raw/index/{ts_code}.parquet"
            ensure_dir(Path(save_path).parent)
            write_parquet(df, save_path)
            self.logger.debug(f"数据已保存到 {save_path}")

        return df

    def get_index_dailybasic(
        self,
        ts_code: str,
        start_date: str = "20100101",
        end_date: str = None,
        save: bool = False,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取指数每日指标

        Args:
            ts_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            save: 是否保存
            save_path: 保存路径

        Returns:
            DataFrame 包含指数指标
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        self.logger.debug(f"获取指数 {ts_code} 每日指标: {start_date} ~ {end_date}")

        df = self._request_with_retry(
            self.pro.index_dailybasic,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )

        if df.empty:
            self.logger.debug(f"{ts_code} 指数每日指标为空")
            return df

        df = df.sort_values("trade_date").reset_index(drop=True)

        self.logger.debug(f"获取到 {len(df)} 条记录")

        if save:
            if save_path is None:
                save_path = f"data/raw/index/{ts_code}_basic.parquet"
            ensure_dir(Path(save_path).parent)
            write_parquet(df, save_path)
            self.logger.debug(f"数据已保存到 {save_path}")

        return df

    def get_stock_basic(
        self,
        save: bool = False,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取股票基础信息

        Args:
            save: 是否保存
            save_path: 保存路径

        Returns:
            DataFrame 包含股票基础信息
        """
        self.logger.info("获取股票基础信息")

        df = self._request_with_retry(
            self.pro.stock_basic,
            exchange="",
            list_status="L",
            fields="ts_code,symbol,name,area,industry,list_date"
        )

        if df.empty:
            self.logger.warning("股票基础信息为空")
            return df

        self.logger.info(f"获取到 {len(df)} 只股票")

        if save:
            if save_path is None:
                save_path = "data/meta/stock_basic.parquet"
            ensure_dir(Path(save_path).parent)
            write_parquet(df, save_path)
            self.logger.info(f"数据已保存到 {save_path}")

        return df

    def get_trade_cal(
        self,
        exchange: str = "SSE",
        start_date: str = "20100101",
        end_date: str = None,
        save: bool = False,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取交易日历

        Args:
            exchange: 交易所，"SSE"=上交所，"SZSE"=深交所
            start_date: 开始日期
            end_date: 结束日期
            save: 是否保存
            save_path: 保存路径

        Returns:
            DataFrame 包含交易日历
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        self.logger.info(f"获取交易日历: {start_date} ~ {end_date}")

        df = self._request_with_retry(
            self.pro.trade_cal,
            exchange=exchange,
            start_date=start_date,
            end_date=end_date
        )

        if df.empty:
            self.logger.warning("交易日历为空")
            return df

        self.logger.info(f"获取到 {len(df)} 条记录")

        if save:
            if save_path is None:
                save_path = "data/meta/trade_cal.parquet"
            ensure_dir(Path(save_path).parent)
            write_parquet(df, save_path)
            self.logger.info(f"数据已保存到 {save_path}")

        return df

    def get_industry(
        self,
        save: bool = False,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取行业分类

        Args:
            save: 是否保存
            save_path: 保存路径

        Returns:
            DataFrame 包含行业分类
        """
        self.logger.info("获取行业分类")

        df = self._request_with_retry(
            self.pro.index_classify,
            level="L2",
            src="SW"
        )

        if df.empty:
            self.logger.warning("行业分类为空")
            return df

        self.logger.info(f"获取到 {len(df)} 条记录")

        if save:
            if save_path is None:
                save_path = "data/meta/industry.parquet"
            ensure_dir(Path(save_path).parent)
            write_parquet(df, save_path)
            self.logger.info(f"数据已保存到 {save_path}")

        return df

    def get_financial(
        self,
        ts_code: str,
        statement: str = "income",
        start_date: str = "20100101",
        end_date: str = None,
        save: bool = False,
        save_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取财务报表

        Args:
            ts_code: 股票代码
            statement: 报表类型，"income"=利润表，"balancesheet"=资产负债表，"cashflow"=现金流量表
            start_date: 开始日期
            end_date: 结束日期
            save: 是否保存
            save_path: 保存路径

        Returns:
            DataFrame 包含财务数据
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        self.logger.info(f"获取 {ts_code} {statement} 报表: {start_date} ~ {end_date}")

        # 根据报表类型选择接口
        if statement == "income":
            func = self.pro.income
        elif statement == "balancesheet":
            func = self.pro.balancesheet
        elif statement == "cashflow":
            func = self.pro.cashflow
        else:
            raise ValueError(f"不支持的报表类型: {statement}")

        df = self._request_with_retry(
            func,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )

        if df.empty:
            self.logger.warning(f"{ts_code} {statement} 报表为空")
            return df

        df = df.sort_values("end_date").reset_index(drop=True)

        self.logger.info(f"获取到 {len(df)} 条记录")

        if save:
            if save_path is None:
                save_path = f"data/raw/financial/{statement}/{ts_code}.parquet"
            ensure_dir(Path(save_path).parent)
            write_parquet(df, save_path)
            self.logger.info(f"数据已保存到 {save_path}")

        return df
