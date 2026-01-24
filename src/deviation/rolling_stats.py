"""
滚动统计模块

提供各种滚动窗口统计量的计算:
- 滚动均值
- 滚动标准差
- 滚动偏度
- 滚动峰度
- 滚动分位数
- 滚动最大/最小值
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, List, Literal
from scipy import stats as scipy_stats

from ..utils.logger import get_logger


class RollingStats:
    """滚动统计计算器"""

    def __init__(
        self,
        window: int = 252,
        min_periods: Optional[int] = None,
    ):
        """
        初始化滚动统计计算器

        Args:
            window: 滚动窗口大小
            min_periods: 最小观察期数，默认为 window // 2
        """
        self.window = window
        self.min_periods = min_periods if min_periods is not None else window // 2
        self.logger = get_logger("deviation.rolling_stats")

    def calculate_rolling_stats(
        self,
        series: pd.Series,
        include_higher_moments: bool = True,
    ) -> pd.DataFrame:
        """
        计算完整的滚动统计量

        Args:
            series: 输入序列
            include_higher_moments: 是否包含高阶矩（偏度、峰度）

        Returns:
            DataFrame 包含:
                - rolling_mean: 滚动均值
                - rolling_std: 滚动标准差
                - rolling_min: 滚动最小值
                - rolling_max: 滚动最大值
                - rolling_median: 滚动中位数
                - rolling_skew: 滚动偏度（可选）
                - rolling_kurt: 滚动峰度（可选）
        """
        result = pd.DataFrame(index=series.index)

        # 基础统计量
        result["rolling_mean"] = self.rolling_mean(series)
        result["rolling_std"] = self.rolling_std(series)
        result["rolling_min"] = self.rolling_min(series)
        result["rolling_max"] = self.rolling_max(series)
        result["rolling_median"] = self.rolling_median(series)

        # 高阶矩
        if include_higher_moments:
            result["rolling_skew"] = self.rolling_skew(series)
            result["rolling_kurt"] = self.rolling_kurt(series)

        return result

    def rolling_mean(self, series: pd.Series) -> pd.Series:
        """
        计算滚动均值

        Args:
            series: 输入序列

        Returns:
            滚动均值序列
        """
        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).mean()

    def rolling_std(
        self, series: pd.Series, ddof: int = 1
    ) -> pd.Series:
        """
        计算滚动标准差

        Args:
            series: 输入序列
            ddof: 自由度调整

        Returns:
            滚动标准差序列
        """
        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).std(ddof=ddof)

    def rolling_var(
        self, series: pd.Series, ddof: int = 1
    ) -> pd.Series:
        """
        计算滚动方差

        Args:
            series: 输入序列
            ddof: 自由度调整

        Returns:
            滚动方差序列
        """
        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).var(ddof=ddof)

    def rolling_min(self, series: pd.Series) -> pd.Series:
        """
        计算滚动最小值

        Args:
            series: 输入序列

        Returns:
            滚动最小值序列
        """
        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).min()

    def rolling_max(self, series: pd.Series) -> pd.Series:
        """
        计算滚动最大值

        Args:
            series: 输入序列

        Returns:
            滚动最大值序列
        """
        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).max()

    def rolling_median(self, series: pd.Series) -> pd.Series:
        """
        计算滚动中位数

        Args:
            series: 输入序列

        Returns:
            滚动中位数序列
        """
        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).median()

    def rolling_skew(self, series: pd.Series) -> pd.Series:
        """
        计算滚动偏度

        偏度衡量分布的不对称性:
        - 正偏度: 右尾较长
        - 负偏度: 左尾较长
        - 接近0: 对称分布

        Args:
            series: 输入序列

        Returns:
            滚动偏度序列
        """
        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).skew()

    def rolling_kurt(self, series: pd.Series) -> pd.Series:
        """
        计算滚动峰度（超额峰度）

        峰度衡量分布的尾部厚度:
        - 正峰度（尖峰）: 尾部厚，极端值多
        - 负峰度（扁平）: 尾部薄，极端值少
        - 接近0: 类似正态分布

        注意: pandas 计算的是超额峰度（正态分布为0）

        Args:
            series: 输入序列

        Returns:
            滚动峰度序列
        """
        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).kurt()

    def rolling_quantile(
        self, series: pd.Series, q: float
    ) -> pd.Series:
        """
        计算滚动分位数

        Args:
            series: 输入序列
            q: 分位数 (0-1)

        Returns:
            滚动分位数序列
        """
        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).quantile(q)

    def rolling_quantiles(
        self,
        series: pd.Series,
        quantiles: List[float] = None,
    ) -> pd.DataFrame:
        """
        计算多个滚动分位数

        Args:
            series: 输入序列
            quantiles: 分位数列表，默认 [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]

        Returns:
            DataFrame 包含各分位数序列
        """
        if quantiles is None:
            quantiles = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]

        result = pd.DataFrame(index=series.index)
        for q in quantiles:
            col_name = f"q{int(q * 100):02d}"
            result[col_name] = self.rolling_quantile(series, q)

        return result

    def rolling_range(self, series: pd.Series) -> pd.Series:
        """
        计算滚动极差（最大值 - 最小值）

        Args:
            series: 输入序列

        Returns:
            滚动极差序列
        """
        return self.rolling_max(series) - self.rolling_min(series)

    def rolling_iqr(self, series: pd.Series) -> pd.Series:
        """
        计算滚动四分位距 (IQR = Q3 - Q1)

        Args:
            series: 输入序列

        Returns:
            滚动 IQR 序列
        """
        q25 = self.rolling_quantile(series, 0.25)
        q75 = self.rolling_quantile(series, 0.75)
        return q75 - q25

    def rolling_cv(self, series: pd.Series) -> pd.Series:
        """
        计算滚动变异系数 (CV = std / mean)

        变异系数用于比较不同量级数据的离散程度

        Args:
            series: 输入序列

        Returns:
            滚动变异系数序列
        """
        mean = self.rolling_mean(series)
        std = self.rolling_std(series)
        with np.errstate(divide="ignore", invalid="ignore"):
            cv = std / mean.abs()
            cv = cv.replace([np.inf, -np.inf], np.nan)
        return cv

    def rolling_zscore(self, series: pd.Series) -> pd.Series:
        """
        计算滚动 Z-score

        Z-score = (value - rolling_mean) / rolling_std

        Args:
            series: 输入序列

        Returns:
            滚动 Z-score 序列
        """
        mean = self.rolling_mean(series)
        std = self.rolling_std(series)
        with np.errstate(divide="ignore", invalid="ignore"):
            zscore = (series - mean) / std
            zscore = zscore.replace([np.inf, -np.inf], np.nan)
        return zscore

    def rolling_percentile_rank(self, series: pd.Series) -> pd.Series:
        """
        计算滚动百分位排名

        返回当前值在历史窗口中的百分位位置

        Args:
            series: 输入序列

        Returns:
            滚动百分位排名序列 (0-100)
        """

        def percentile_rank(x):
            if len(x) < 2:
                return np.nan
            current = x.iloc[-1]
            historical = x.iloc[:-1]
            if pd.isna(current):
                return np.nan
            return (historical < current).sum() / len(historical) * 100

        return series.rolling(
            window=self.window, min_periods=self.min_periods
        ).apply(percentile_rank, raw=False)


class EWMStats:
    """指数加权移动统计计算器"""

    def __init__(
        self,
        span: int = 252,
        min_periods: Optional[int] = None,
        adjust: bool = True,
    ):
        """
        初始化指数加权移动统计计算器

        Args:
            span: 衰减期数（span 对应的 alpha = 2 / (span + 1)）
            min_periods: 最小观察期数
            adjust: 是否调整偏差
        """
        self.span = span
        self.min_periods = min_periods if min_periods is not None else span // 2
        self.adjust = adjust
        self.logger = get_logger("deviation.ewm_stats")

    def ewm_mean(self, series: pd.Series) -> pd.Series:
        """计算指数加权移动均值"""
        return series.ewm(
            span=self.span, min_periods=self.min_periods, adjust=self.adjust
        ).mean()

    def ewm_std(self, series: pd.Series) -> pd.Series:
        """计算指数加权移动标准差"""
        return series.ewm(
            span=self.span, min_periods=self.min_periods, adjust=self.adjust
        ).std()

    def ewm_var(self, series: pd.Series) -> pd.Series:
        """计算指数加权移动方差"""
        return series.ewm(
            span=self.span, min_periods=self.min_periods, adjust=self.adjust
        ).var()

    def ewm_zscore(self, series: pd.Series) -> pd.Series:
        """计算指数加权 Z-score"""
        mean = self.ewm_mean(series)
        std = self.ewm_std(series)
        with np.errstate(divide="ignore", invalid="ignore"):
            zscore = (series - mean) / std
            zscore = zscore.replace([np.inf, -np.inf], np.nan)
        return zscore

    def ewm_stats(self, series: pd.Series) -> pd.DataFrame:
        """
        计算完整的指数加权移动统计量

        Args:
            series: 输入序列

        Returns:
            DataFrame 包含 ewm_mean, ewm_std, ewm_var, ewm_zscore
        """
        result = pd.DataFrame(index=series.index)
        result["ewm_mean"] = self.ewm_mean(series)
        result["ewm_std"] = self.ewm_std(series)
        result["ewm_var"] = self.ewm_var(series)
        result["ewm_zscore"] = self.ewm_zscore(series)
        return result


class ExpandingStats:
    """扩展窗口统计计算器（累积统计）"""

    def __init__(self, min_periods: int = 1):
        """
        初始化扩展窗口统计计算器

        Args:
            min_periods: 最小观察期数
        """
        self.min_periods = min_periods
        self.logger = get_logger("deviation.expanding_stats")

    def expanding_mean(self, series: pd.Series) -> pd.Series:
        """计算累积均值"""
        return series.expanding(min_periods=self.min_periods).mean()

    def expanding_std(self, series: pd.Series) -> pd.Series:
        """计算累积标准差"""
        return series.expanding(min_periods=self.min_periods).std()

    def expanding_min(self, series: pd.Series) -> pd.Series:
        """计算累积最小值"""
        return series.expanding(min_periods=self.min_periods).min()

    def expanding_max(self, series: pd.Series) -> pd.Series:
        """计算累积最大值"""
        return series.expanding(min_periods=self.min_periods).max()

    def expanding_skew(self, series: pd.Series) -> pd.Series:
        """计算累积偏度"""
        return series.expanding(min_periods=self.min_periods).skew()

    def expanding_kurt(self, series: pd.Series) -> pd.Series:
        """计算累积峰度"""
        return series.expanding(min_periods=self.min_periods).kurt()

    def expanding_quantile(
        self, series: pd.Series, q: float
    ) -> pd.Series:
        """计算累积分位数"""
        return series.expanding(min_periods=self.min_periods).quantile(q)

    def expanding_stats(self, series: pd.Series) -> pd.DataFrame:
        """
        计算完整的扩展窗口统计量

        Args:
            series: 输入序列

        Returns:
            DataFrame 包含各统计量
        """
        result = pd.DataFrame(index=series.index)
        result["expanding_mean"] = self.expanding_mean(series)
        result["expanding_std"] = self.expanding_std(series)
        result["expanding_min"] = self.expanding_min(series)
        result["expanding_max"] = self.expanding_max(series)
        result["expanding_skew"] = self.expanding_skew(series)
        result["expanding_kurt"] = self.expanding_kurt(series)
        return result
