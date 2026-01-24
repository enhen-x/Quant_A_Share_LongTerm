"""
数据中心

提供统一的数据入口和缓存机制
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union, List
from datetime import datetime, timedelta

from .tushare_source import TushareSource
from ..utils.logger import get_logger
from ..utils.config import get_config
from ..utils.io import read_parquet, write_parquet, ensure_dir


class DataHub:
    """数据中心 - 统一数据入口"""

    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化数据中心

        Args:
            data_dir: 数据根目录，默认为 config 中的路径
        """
        self.config = get_config()
        self.logger = get_logger("datahub")

        if data_dir is None:
            self.data_dir = Path(self.config.get("paths.data_processed", "data/processed"))
        else:
            self.data_dir = Path(data_dir)

        self.raw_dir = Path(self.config.get("paths.data_raw", "data/raw"))
        self.meta_dir = Path(self.config.get("paths.data_meta", "data/meta"))

        # Tushare 数据源
        self.source = None

        # 缓存
        self._cache = {}

    def init_source(self, token: Optional[str] = None):
        """初始化 Tushare 数据源"""
        if self.source is None:
            self.source = TushareSource(token)

    def get_daily(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        force_update: bool = False,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取日线行情（优先从缓存读取）

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            force_update: 是否强制更新
            use_cache: 是否使用缓存

        Returns:
            DataFrame 包含 OHLCV 数据
        """
        cache_key = f"daily_{ts_code}"

        # 检查缓存
        if use_cache and not force_update and cache_key in self._cache:
            df = self._cache[cache_key]
            self.logger.debug(f"从缓存读取 {ts_code} 日线数据")
            return df.copy()

        # 从文件读取
        file_path = self.raw_dir / "market" / "daily" / f"{ts_code}.parquet"

        if not force_update and file_path.exists():
            df = read_parquet(file_path)
            self.logger.debug(f"从文件读取 {ts_code} 日线数据")

            # 检查数据是否需要更新
            if not df.empty:
                last_date = df["trade_date"].max()
                today = datetime.now().strftime("%Y%m%d")
                if last_date >= today:
                    self._cache[cache_key] = df
                    return df.copy()
                else:
                    self.logger.debug(f"{ts_code} 数据需要更新 (最后日期: {last_date})")

        # 从 Tushare 获取
        if self.source is None:
            self.init_source()

        if not file_path.exists():
            # 全量下载
            config_start = self.config.get("data.start_date", "20100101")
            df = self.source.get_daily(
                ts_code=ts_code,
                start_date=config_start,
                end_date=end_date,
                save=True
            )
        else:
            # 增量更新
            df = read_parquet(file_path)
            if not df.empty:
                last_date = df["trade_date"].max()
                start_date = str(int(last_date) + 1)

                new_df = self.source.get_daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    save=True
                )

                if not new_df.empty:
                    df = pd.concat([df, new_df], ignore_index=True)
                    df = df.drop_duplicates(subset=["trade_date"]).sort_values("trade_date")
                    write_parquet(df, file_path)

        self._cache[cache_key] = df
        return df.copy()

    def get_index_daily(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        force_update: bool = False,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取指数日线行情

        Args:
            ts_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            force_update: 是否强制更新
            use_cache: 是否使用缓存

        Returns:
            DataFrame 包含指数行情
        """
        cache_key = f"index_{ts_code}"

        if use_cache and not force_update and cache_key in self._cache:
            df = self._cache[cache_key]
            return df.copy()

        file_path = self.raw_dir / "index" / f"{ts_code}.parquet"

        if not force_update and file_path.exists():
            df = read_parquet(file_path)
            if not df.empty:
                last_date = df["trade_date"].max()
                today = datetime.now().strftime("%Y%m%d")
                if last_date >= today:
                    self._cache[cache_key] = df
                    return df.copy()
                else:
                    self.logger.debug(f"{ts_code} 指数数据需要更新")

        if self.source is None:
            self.init_source()

        config_start = self.config.get("data.start_date", "20100101")
        df = self.source.get_index_daily(
            ts_code=ts_code,
            start_date=config_start,
            end_date=end_date,
            save=True
        )

        self._cache[cache_key] = df
        return df.copy()

    def get_stock_basic(
        self,
        force_update: bool = False,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取股票基础信息

        Args:
            force_update: 是否强制更新
            use_cache: 是否使用缓存

        Returns:
            DataFrame 包含股票基础信息
        """
        cache_key = "stock_basic"

        if use_cache and not force_update and cache_key in self._cache:
            return self._cache[cache_key].copy()

        file_path = self.meta_dir / "stock_basic.parquet"

        if not force_update and file_path.exists():
            df = read_parquet(file_path)
            self._cache[cache_key] = df
            return df.copy()

        if self.source is None:
            self.init_source()

        df = self.source.get_stock_basic(save=True)

        self._cache[cache_key] = df
        return df.copy()

    def get_trade_cal(
        self,
        exchange: str = "SSE",
        start_date: str = "20100101",
        end_date: Optional[str] = None,
        force_update: bool = False,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取交易日历

        Args:
            exchange: 交易所
            start_date: 开始日期
            end_date: 结束日期
            force_update: 是否强制更新
            use_cache: 是否使用缓存

        Returns:
            DataFrame 包含交易日历
        """
        cache_key = f"trade_cal_{exchange}"

        if use_cache and not force_update and cache_key in self._cache:
            df = self._cache[cache_key]
            return df.copy()

        file_path = self.meta_dir / "trade_cal.parquet"

        if not force_update and file_path.exists():
            df = read_parquet(file_path)
            self._cache[cache_key] = df
            return df.copy()

        if self.source is None:
            self.init_source()

        df = self.source.get_trade_cal(
            exchange=exchange,
            start_date=start_date,
            end_date=end_date,
            save=True
        )

        self._cache[cache_key] = df
        return df.copy()

    def get_stock_list(
        self,
        exclude_st: bool = True,
        exclude_kcb: bool = True,
        exclude_bj: bool = True,
        min_market_cap: Optional[float] = None,
        min_list_days: Optional[int] = None,
        force_update: bool = False
    ) -> pd.DataFrame:
        """
        获取筛选后的股票列表

        Args:
            exclude_st: 排除 ST 股
            exclude_kcb: 排除科创板
            exclude_bj: 排除北交所
            min_market_cap: 最小市值
            min_list_days: 最小上市天数
            force_update: 是否强制更新

        Returns:
            DataFrame 包含筛选后的股票列表
        """
        df = self.get_stock_basic(force_update=force_update)

        if df.empty:
            return df

        # 应用筛选条件
        if exclude_st:
            df = df[~df["name"].str.contains("ST", na=False)]

        if exclude_kcb:
            df = df[~df["ts_code"].str.startswith("688")]

        if exclude_bj:
            df = df[~df["ts_code"].str.startswith("8")]
            df = df[~df["ts_code"].str.startswith("4")]

        if min_list_days is not None and "list_date" in df.columns:
            today = datetime.now()
            df["list_date_dt"] = pd.to_datetime(df["list_date"])
            df["days_since_list"] = (today - df["list_date_dt"]).dt.days
            df = df[df["days_since_list"] >= min_list_days]

        if min_market_cap is not None and "total_mv" in df.columns:
            df = df[df["total_mv"] >= min_market_cap]

        return df.reset_index(drop=True)

    def get_index_list(
        self,
        force_update: bool = False
    ) -> List[str]:
        """
        获取关注的指数列表

        Args:
            force_update: 是否强制更新

        Returns:
            指数代码列表
        """
        index_list = self.config.get("data.index_list", [])
        return index_list

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self.logger.info("缓存已清空")

    def update_all_data(
        self,
        ts_codes: Optional[List[str]] = None,
        index_codes: Optional[List[str]] = None,
        update_basic: bool = True,
        update_indices: bool = True,
        show_progress: bool = True
    ):
        """
        批量更新数据

        Args:
            ts_codes: 股票代码列表，默认从配置获取
            index_codes: 指数代码列表，默认从配置获取
            update_basic: 是否更新基础数据
            update_indices: 是否更新指数数据
            show_progress: 是否显示进度条
        """
        try:
            from tqdm import tqdm
            use_tqdm = show_progress
        except ImportError:
            use_tqdm = False

        self.logger.info("开始批量更新数据")

        if update_basic:
            # 更新基础数据
            self.logger.info("更新股票基础信息...")
            self.get_stock_basic(force_update=True)

            self.logger.info("更新交易日历...")
            self.get_trade_cal(force_update=True)

            # 更新股票日线
            if ts_codes is None:
                ts_codes = self.get_stock_list(force_update=True)["ts_code"].tolist()

            self.logger.info(f"更新 {len(ts_codes)} 只股票的日线数据...")
            
            iterator = tqdm(ts_codes, desc="股票数据", unit="只") if use_tqdm else ts_codes
            for ts_code in iterator:
                if use_tqdm:
                    iterator.set_postfix_str(ts_code)
                try:
                    self.get_daily(ts_code, force_update=True)
                except Exception as e:
                    self.logger.error(f"更新 {ts_code} 失败: {e}")

        if update_indices:
            if index_codes is None:
                index_codes = self.get_index_list()

            self.logger.info(f"更新 {len(index_codes)} 个指数的日线数据...")
            
            iterator = tqdm(index_codes, desc="指数数据", unit="个") if use_tqdm else index_codes
            for index_code in iterator:
                if use_tqdm:
                    iterator.set_postfix_str(index_code)
                try:
                    self.get_index_daily(index_code, force_update=True)
                except Exception as e:
                    self.logger.error(f"更新 {index_code} 失败: {e}")

        self.logger.info("批量更新完成")
