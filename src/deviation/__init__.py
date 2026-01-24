"""
偏移率计算模块

提供偏移率计算、滚动统计和数据标准化功能

主要类和函数:
- DeviationCalculator: 偏移率计算器
- MultiWindowDeviationCalculator: 多窗口偏移率计算器
- RollingStats: 滚动统计计算器
- EWMStats: 指数加权移动统计计算器
- ExpandingStats: 扩展窗口统计计算器
- 各种标准化方法 (ZScore, MinMax, Percentile, Robust)
"""

from .calculator import (
    DeviationCalculator,
    MultiWindowDeviationCalculator,
)

from .rolling_stats import (
    RollingStats,
    EWMStats,
    ExpandingStats,
)

from .normalization import (
    # 基类
    BaseNormalizer,
    # 标准化器类
    ZScoreNormalizer,
    MinMaxNormalizer,
    PercentileNormalizer,
    RobustNormalizer,
    DecimalScalingNormalizer,
    # 函数式接口
    zscore_normalize,
    minmax_normalize,
    percentile_normalize,
    robust_normalize,
    rolling_zscore_normalize,
    rolling_minmax_normalize,
    rolling_percentile_normalize,
    # 工厂函数
    get_normalizer,
    normalize,
)


__all__ = [
    # 偏移率计算
    "DeviationCalculator",
    "MultiWindowDeviationCalculator",
    # 滚动统计
    "RollingStats",
    "EWMStats",
    "ExpandingStats",
    # 标准化
    "BaseNormalizer",
    "ZScoreNormalizer",
    "MinMaxNormalizer",
    "PercentileNormalizer",
    "RobustNormalizer",
    "DecimalScalingNormalizer",
    "zscore_normalize",
    "minmax_normalize",
    "percentile_normalize",
    "robust_normalize",
    "rolling_zscore_normalize",
    "rolling_minmax_normalize",
    "rolling_percentile_normalize",
    "get_normalizer",
    "normalize",
]
