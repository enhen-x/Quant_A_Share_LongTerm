"""
标准化方法模块

提供多种数据标准化方法:
- Z-score 标准化
- Min-Max 标准化
- 百分位标准化
- Robust 标准化（基于中位数和 IQR）
- 小数定标标准化
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, Literal, Tuple
from abc import ABC, abstractmethod

from ..utils.logger import get_logger


class BaseNormalizer(ABC):
    """标准化器基类"""

    @abstractmethod
    def fit(self, data: pd.Series) -> "BaseNormalizer":
        """拟合数据，计算标准化参数"""
        pass

    @abstractmethod
    def transform(self, data: pd.Series) -> pd.Series:
        """应用标准化转换"""
        pass

    @abstractmethod
    def inverse_transform(self, data: pd.Series) -> pd.Series:
        """逆标准化转换"""
        pass

    def fit_transform(self, data: pd.Series) -> pd.Series:
        """拟合并转换数据"""
        self.fit(data)
        return self.transform(data)


class ZScoreNormalizer(BaseNormalizer):
    """
    Z-score 标准化

    公式: z = (x - mean) / std

    适用场景:
    - 数据近似正态分布
    - 需要保留异常值的影响
    - 用于后续假设正态分布的分析
    """

    def __init__(self, ddof: int = 1):
        """
        初始化

        Args:
            ddof: 标准差自由度调整
        """
        self.ddof = ddof
        self.mean_: Optional[float] = None
        self.std_: Optional[float] = None
        self.logger = get_logger("deviation.normalization.zscore")

    def fit(self, data: pd.Series) -> "ZScoreNormalizer":
        """拟合数据"""
        clean_data = data.dropna()
        self.mean_ = clean_data.mean()
        self.std_ = clean_data.std(ddof=self.ddof)

        if self.std_ == 0 or pd.isna(self.std_):
            self.logger.warning("标准差为0或无效，设为1")
            self.std_ = 1.0

        return self

    def transform(self, data: pd.Series) -> pd.Series:
        """应用 Z-score 标准化"""
        if self.mean_ is None or self.std_ is None:
            raise ValueError("请先调用 fit() 方法")

        return (data - self.mean_) / self.std_

    def inverse_transform(self, data: pd.Series) -> pd.Series:
        """逆 Z-score 标准化"""
        if self.mean_ is None or self.std_ is None:
            raise ValueError("请先调用 fit() 方法")

        return data * self.std_ + self.mean_


class MinMaxNormalizer(BaseNormalizer):
    """
    Min-Max 标准化

    公式: x' = (x - min) / (max - min) * (new_max - new_min) + new_min

    适用场景:
    - 需要将数据缩放到固定范围
    - 数据分布不明确
    - 神经网络输入预处理
    """

    def __init__(
        self,
        feature_range: Tuple[float, float] = (0, 1),
    ):
        """
        初始化

        Args:
            feature_range: 目标范围，默认 (0, 1)
        """
        self.feature_range = feature_range
        self.min_: Optional[float] = None
        self.max_: Optional[float] = None
        self.logger = get_logger("deviation.normalization.minmax")

    def fit(self, data: pd.Series) -> "MinMaxNormalizer":
        """拟合数据"""
        clean_data = data.dropna()
        self.min_ = clean_data.min()
        self.max_ = clean_data.max()

        if self.max_ == self.min_:
            self.logger.warning("最大值等于最小值，范围设为1")
            self.max_ = self.min_ + 1.0

        return self

    def transform(self, data: pd.Series) -> pd.Series:
        """应用 Min-Max 标准化"""
        if self.min_ is None or self.max_ is None:
            raise ValueError("请先调用 fit() 方法")

        new_min, new_max = self.feature_range
        scale = (new_max - new_min) / (self.max_ - self.min_)
        return (data - self.min_) * scale + new_min

    def inverse_transform(self, data: pd.Series) -> pd.Series:
        """逆 Min-Max 标准化"""
        if self.min_ is None or self.max_ is None:
            raise ValueError("请先调用 fit() 方法")

        new_min, new_max = self.feature_range
        scale = (self.max_ - self.min_) / (new_max - new_min)
        return (data - new_min) * scale + self.min_


class PercentileNormalizer(BaseNormalizer):
    """
    百分位标准化

    将数据转换为其在历史分布中的百分位位置

    适用场景:
    - 数据分布不规则
    - 需要抵抗异常值
    - 比较不同标的的相对位置
    """

    def __init__(self):
        self.sorted_values_: Optional[np.ndarray] = None
        self.logger = get_logger("deviation.normalization.percentile")

    def fit(self, data: pd.Series) -> "PercentileNormalizer":
        """拟合数据"""
        clean_data = data.dropna()
        self.sorted_values_ = np.sort(clean_data.values)
        return self

    def transform(self, data: pd.Series) -> pd.Series:
        """应用百分位标准化"""
        if self.sorted_values_ is None:
            raise ValueError("请先调用 fit() 方法")

        def to_percentile(x):
            if pd.isna(x):
                return np.nan
            # 使用 searchsorted 找到百分位
            idx = np.searchsorted(self.sorted_values_, x)
            return idx / len(self.sorted_values_) * 100

        return data.apply(to_percentile)

    def inverse_transform(self, data: pd.Series) -> pd.Series:
        """逆百分位标准化（近似）"""
        if self.sorted_values_ is None:
            raise ValueError("请先调用 fit() 方法")

        def from_percentile(p):
            if pd.isna(p):
                return np.nan
            idx = int(p / 100 * len(self.sorted_values_))
            idx = min(idx, len(self.sorted_values_) - 1)
            idx = max(idx, 0)
            return self.sorted_values_[idx]

        return data.apply(from_percentile)


class RobustNormalizer(BaseNormalizer):
    """
    Robust 标准化（基于中位数和 IQR）

    公式: x' = (x - median) / IQR

    适用场景:
    - 数据存在较多异常值
    - 分布偏斜
    - 需要抵抗极端值的影响
    """

    def __init__(
        self,
        quantile_range: Tuple[float, float] = (0.25, 0.75),
        with_centering: bool = True,
        with_scaling: bool = True,
    ):
        """
        初始化

        Args:
            quantile_range: 用于计算 IQR 的分位数范围
            with_centering: 是否中心化（减去中位数）
            with_scaling: 是否缩放（除以 IQR）
        """
        self.quantile_range = quantile_range
        self.with_centering = with_centering
        self.with_scaling = with_scaling
        self.median_: Optional[float] = None
        self.iqr_: Optional[float] = None
        self.logger = get_logger("deviation.normalization.robust")

    def fit(self, data: pd.Series) -> "RobustNormalizer":
        """拟合数据"""
        clean_data = data.dropna()

        self.median_ = clean_data.median()

        q_low, q_high = self.quantile_range
        q_low_val = clean_data.quantile(q_low)
        q_high_val = clean_data.quantile(q_high)
        self.iqr_ = q_high_val - q_low_val

        if self.iqr_ == 0 or pd.isna(self.iqr_):
            self.logger.warning("IQR 为0或无效，设为1")
            self.iqr_ = 1.0

        return self

    def transform(self, data: pd.Series) -> pd.Series:
        """应用 Robust 标准化"""
        if self.median_ is None or self.iqr_ is None:
            raise ValueError("请先调用 fit() 方法")

        result = data.copy()

        if self.with_centering:
            result = result - self.median_

        if self.with_scaling:
            result = result / self.iqr_

        return result

    def inverse_transform(self, data: pd.Series) -> pd.Series:
        """逆 Robust 标准化"""
        if self.median_ is None or self.iqr_ is None:
            raise ValueError("请先调用 fit() 方法")

        result = data.copy()

        if self.with_scaling:
            result = result * self.iqr_

        if self.with_centering:
            result = result + self.median_

        return result


class DecimalScalingNormalizer(BaseNormalizer):
    """
    小数定标标准化

    通过移动小数点位置实现标准化
    公式: x' = x / 10^j，其中 j 是使 max(|x'|) < 1 的最小整数

    适用场景:
    - 简单快速的标准化
    - 保持数据相对大小关系
    """

    def __init__(self):
        self.scale_factor_: Optional[float] = None
        self.logger = get_logger("deviation.normalization.decimal")

    def fit(self, data: pd.Series) -> "DecimalScalingNormalizer":
        """拟合数据"""
        clean_data = data.dropna()
        max_abs = clean_data.abs().max()

        if max_abs == 0:
            self.scale_factor_ = 1.0
        else:
            # 计算使 max(|x|) / 10^j < 1 的最小 j
            j = int(np.ceil(np.log10(max_abs)))
            self.scale_factor_ = 10 ** j

        return self

    def transform(self, data: pd.Series) -> pd.Series:
        """应用小数定标标准化"""
        if self.scale_factor_ is None:
            raise ValueError("请先调用 fit() 方法")

        return data / self.scale_factor_

    def inverse_transform(self, data: pd.Series) -> pd.Series:
        """逆小数定标标准化"""
        if self.scale_factor_ is None:
            raise ValueError("请先调用 fit() 方法")

        return data * self.scale_factor_


# ============================================================================
# 函数式接口
# ============================================================================


def zscore_normalize(
    data: pd.Series,
    ddof: int = 1,
) -> pd.Series:
    """
    Z-score 标准化（函数式接口）

    Args:
        data: 输入数据
        ddof: 自由度调整

    Returns:
        标准化后的数据
    """
    normalizer = ZScoreNormalizer(ddof=ddof)
    return normalizer.fit_transform(data)


def minmax_normalize(
    data: pd.Series,
    feature_range: Tuple[float, float] = (0, 1),
) -> pd.Series:
    """
    Min-Max 标准化（函数式接口）

    Args:
        data: 输入数据
        feature_range: 目标范围

    Returns:
        标准化后的数据
    """
    normalizer = MinMaxNormalizer(feature_range=feature_range)
    return normalizer.fit_transform(data)


def percentile_normalize(data: pd.Series) -> pd.Series:
    """
    百分位标准化（函数式接口）

    Args:
        data: 输入数据

    Returns:
        标准化后的数据（0-100）
    """
    normalizer = PercentileNormalizer()
    return normalizer.fit_transform(data)


def robust_normalize(
    data: pd.Series,
    quantile_range: Tuple[float, float] = (0.25, 0.75),
) -> pd.Series:
    """
    Robust 标准化（函数式接口）

    Args:
        data: 输入数据
        quantile_range: 分位数范围

    Returns:
        标准化后的数据
    """
    normalizer = RobustNormalizer(quantile_range=quantile_range)
    return normalizer.fit_transform(data)


def rolling_zscore_normalize(
    data: pd.Series,
    window: int = 252,
    min_periods: Optional[int] = None,
) -> pd.Series:
    """
    滚动 Z-score 标准化

    使用滚动窗口计算 Z-score

    Args:
        data: 输入数据
        window: 窗口大小
        min_periods: 最小观察期数

    Returns:
        滚动标准化后的数据
    """
    if min_periods is None:
        min_periods = window // 2

    rolling_mean = data.rolling(window=window, min_periods=min_periods).mean()
    rolling_std = data.rolling(window=window, min_periods=min_periods).std()

    with np.errstate(divide="ignore", invalid="ignore"):
        result = (data - rolling_mean) / rolling_std
        result = result.replace([np.inf, -np.inf], np.nan)

    return result


def rolling_minmax_normalize(
    data: pd.Series,
    window: int = 252,
    min_periods: Optional[int] = None,
    feature_range: Tuple[float, float] = (0, 1),
) -> pd.Series:
    """
    滚动 Min-Max 标准化

    使用滚动窗口计算 Min-Max 标准化

    Args:
        data: 输入数据
        window: 窗口大小
        min_periods: 最小观察期数
        feature_range: 目标范围

    Returns:
        滚动标准化后的数据
    """
    if min_periods is None:
        min_periods = window // 2

    rolling_min = data.rolling(window=window, min_periods=min_periods).min()
    rolling_max = data.rolling(window=window, min_periods=min_periods).max()

    new_min, new_max = feature_range
    data_range = rolling_max - rolling_min

    with np.errstate(divide="ignore", invalid="ignore"):
        result = (data - rolling_min) / data_range * (new_max - new_min) + new_min
        result = result.replace([np.inf, -np.inf], np.nan)

    return result


def rolling_percentile_normalize(
    data: pd.Series,
    window: int = 252,
    min_periods: Optional[int] = None,
) -> pd.Series:
    """
    滚动百分位标准化

    计算当前值在滚动窗口中的百分位位置

    Args:
        data: 输入数据
        window: 窗口大小
        min_periods: 最小观察期数

    Returns:
        滚动百分位（0-100）
    """
    if min_periods is None:
        min_periods = window // 2

    def percentile_rank(x):
        if len(x) < 2:
            return np.nan
        current = x.iloc[-1]
        if pd.isna(current):
            return np.nan
        historical = x.iloc[:-1].dropna()
        if len(historical) == 0:
            return np.nan
        return (historical < current).sum() / len(historical) * 100

    return data.rolling(window=window, min_periods=min_periods).apply(
        percentile_rank, raw=False
    )


# ============================================================================
# 工厂函数
# ============================================================================


def get_normalizer(
    method: Literal["zscore", "minmax", "percentile", "robust", "decimal"],
    **kwargs,
) -> BaseNormalizer:
    """
    获取标准化器实例

    Args:
        method: 标准化方法
        **kwargs: 传递给标准化器的参数

    Returns:
        标准化器实例
    """
    normalizers = {
        "zscore": ZScoreNormalizer,
        "minmax": MinMaxNormalizer,
        "percentile": PercentileNormalizer,
        "robust": RobustNormalizer,
        "decimal": DecimalScalingNormalizer,
    }

    if method not in normalizers:
        raise ValueError(f"未知的标准化方法: {method}，可选: {list(normalizers.keys())}")

    return normalizers[method](**kwargs)


def normalize(
    data: pd.Series,
    method: Literal["zscore", "minmax", "percentile", "robust", "decimal"] = "zscore",
    **kwargs,
) -> pd.Series:
    """
    通用标准化函数

    Args:
        data: 输入数据
        method: 标准化方法
        **kwargs: 传递给标准化器的参数

    Returns:
        标准化后的数据
    """
    normalizer = get_normalizer(method, **kwargs)
    return normalizer.fit_transform(data)
