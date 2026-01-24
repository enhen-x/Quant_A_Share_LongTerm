"""
偏移率计算器

实现多种偏移率计算方法:
- 原始偏移率: (close - ma) / ma
- Z-score 偏移率: (close - ma) / std
- 百分位偏移率

支持多种窗口类型:
- simple: 简单移动窗口
- exponential: 指数加权移动窗口
- adaptive: 自适应窗口
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, Literal

from ..utils.logger import get_logger


class DeviationCalculator:
    """偏移率计算器"""

    def __init__(
        self,
        window: int = 252,
        window_type: Literal["simple", "exponential", "adaptive"] = "simple",
        min_periods: Optional[int] = None,
    ):
        """
        初始化偏移率计算器

        Args:
            window: 移动窗口大小（默认252交易日=1年）
            window_type: 窗口类型 ('simple' / 'exponential' / 'adaptive')
            min_periods: 最小观察期数，默认为 window // 2
        """
        self.window = window
        self.window_type = window_type
        self.min_periods = min_periods if min_periods is not None else window // 2
        self.logger = get_logger("deviation.calculator")

    def calculate(
        self,
        prices: pd.Series,
        method: Literal["raw", "zscore", "percentile", "all"] = "all",
    ) -> pd.DataFrame:
        """
        计算偏移率

        Args:
            prices: 价格序列（索引为日期）
            method: 计算方法
                - 'raw': 只计算原始偏移率
                - 'zscore': 只计算 Z-score 偏移率
                - 'percentile': 只计算百分位偏移率
                - 'all': 计算所有偏移率

        Returns:
            DataFrame 包含:
                - close: 收盘价
                - ma: 移动均值
                - std: 移动标准差
                - dr_raw: 原始偏移率 (close - ma) / ma
                - dr_zscore: Z-score偏移率 (close - ma) / std
                - dr_percentile: 百分位偏移率（仅当 method='all' 或 'percentile'）
        """
        if prices.empty:
            self.logger.warning("输入价格序列为空")
            return pd.DataFrame()

        # 确保索引是日期类型
        if not isinstance(prices.index, pd.DatetimeIndex):
            try:
                prices.index = pd.to_datetime(prices.index)
            except Exception:
                pass

        # 创建结果 DataFrame
        result = pd.DataFrame(index=prices.index)
        result["close"] = prices

        # 计算移动均值和标准差
        if self.window_type == "simple":
            result["ma"] = prices.rolling(
                window=self.window, min_periods=self.min_periods
            ).mean()
            result["std"] = prices.rolling(
                window=self.window, min_periods=self.min_periods
            ).std()
        elif self.window_type == "exponential":
            result["ma"] = prices.ewm(
                span=self.window, min_periods=self.min_periods
            ).mean()
            result["std"] = prices.ewm(
                span=self.window, min_periods=self.min_periods
            ).std()
        elif self.window_type == "adaptive":
            result["ma"], result["std"] = self._calculate_adaptive(prices)
        else:
            raise ValueError(f"未知的窗口类型: {self.window_type}")

        # 计算偏移率
        if method in ["raw", "all"]:
            result["dr_raw"] = self._calculate_raw_deviation(
                result["close"], result["ma"]
            )

        if method in ["zscore", "all"]:
            result["dr_zscore"] = self._calculate_zscore_deviation(
                result["close"], result["ma"], result["std"]
            )

        if method in ["percentile", "all"]:
            # 百分位偏移率基于 dr_raw
            if "dr_raw" not in result.columns:
                result["dr_raw"] = self._calculate_raw_deviation(
                    result["close"], result["ma"]
                )
            result["dr_percentile"] = self._calculate_percentile_deviation(
                result["dr_raw"]
            )

        # 添加窗口信息
        result["window_type"] = self.window_type
        result["window_size"] = self.window

        return result

    def calculate_raw(self, prices: pd.Series) -> pd.Series:
        """
        计算原始偏移率 (close - ma) / ma

        Args:
            prices: 价格序列

        Returns:
            原始偏移率序列
        """
        if self.window_type == "simple":
            ma = prices.rolling(window=self.window, min_periods=self.min_periods).mean()
        elif self.window_type == "exponential":
            ma = prices.ewm(span=self.window, min_periods=self.min_periods).mean()
        else:
            ma, _ = self._calculate_adaptive(prices)

        return self._calculate_raw_deviation(prices, ma)

    def calculate_zscore(self, prices: pd.Series) -> pd.Series:
        """
        计算 Z-score 偏移率 (close - ma) / std

        Args:
            prices: 价格序列

        Returns:
            Z-score 偏移率序列
        """
        if self.window_type == "simple":
            ma = prices.rolling(window=self.window, min_periods=self.min_periods).mean()
            std = prices.rolling(
                window=self.window, min_periods=self.min_periods
            ).std()
        elif self.window_type == "exponential":
            ma = prices.ewm(span=self.window, min_periods=self.min_periods).mean()
            std = prices.ewm(span=self.window, min_periods=self.min_periods).std()
        else:
            ma, std = self._calculate_adaptive(prices)

        return self._calculate_zscore_deviation(prices, ma, std)

    def calculate_percentile(
        self, prices: pd.Series, percentile_window: Optional[int] = None
    ) -> pd.Series:
        """
        计算历史百分位偏移率

        百分位偏移率表示当前偏移率在历史分布中的位置

        Args:
            prices: 价格序列
            percentile_window: 百分位计算窗口，默认为 5 * window (约5年)

        Returns:
            百分位偏移率序列 (0-100)
        """
        if percentile_window is None:
            percentile_window = self.window * 5

        # 先计算原始偏移率
        dr_raw = self.calculate_raw(prices)

        return self._calculate_percentile_deviation(dr_raw, percentile_window)

    def _calculate_raw_deviation(
        self, prices: pd.Series, ma: pd.Series
    ) -> pd.Series:
        """计算原始偏移率"""
        with np.errstate(divide="ignore", invalid="ignore"):
            dr = (prices - ma) / ma
            dr = dr.replace([np.inf, -np.inf], np.nan)
        return dr

    def _calculate_zscore_deviation(
        self, prices: pd.Series, ma: pd.Series, std: pd.Series
    ) -> pd.Series:
        """计算 Z-score 偏移率"""
        with np.errstate(divide="ignore", invalid="ignore"):
            dr = (prices - ma) / std
            dr = dr.replace([np.inf, -np.inf], np.nan)
        return dr

    def _calculate_percentile_deviation(
        self, dr_raw: pd.Series, percentile_window: Optional[int] = None
    ) -> pd.Series:
        """
        计算百分位偏移率（向量化实现）

        Args:
            dr_raw: 原始偏移率序列
            percentile_window: 百分位计算窗口

        Returns:
            百分位偏移率 (0-100)
        """
        if percentile_window is None:
            percentile_window = self.window * 5

        n = len(dr_raw)
        if n < self.min_periods:
            return pd.Series(np.nan, index=dr_raw.index)

        values = dr_raw.values
        result = np.full(n, np.nan)

        # 向量化滚动百分位计算
        for i in range(self.min_periods, n):
            start = max(0, i - percentile_window + 1)
            window_data = values[start:i]  # 不包括当前值
            valid_mask = ~np.isnan(window_data)
            valid_data = window_data[valid_mask]

            if len(valid_data) == 0 or np.isnan(values[i]):
                continue

            current = values[i]
            result[i] = np.sum(valid_data < current) / len(valid_data) * 100

        return pd.Series(result, index=dr_raw.index)

    def _calculate_adaptive(self, prices: pd.Series) -> tuple:
        """
        计算自适应移动均值和标准差

        自适应窗口根据价格波动率动态调整:
        - 高波动期使用较短窗口
        - 低波动期使用较长窗口

        Args:
            prices: 价格序列

        Returns:
            (ma, std) 元组
        """
        # 计算短期和长期标准差
        short_window = max(self.window // 4, 20)
        long_window = self.window

        short_vol = prices.rolling(window=short_window, min_periods=short_window // 2).std()
        long_vol = prices.rolling(window=long_window, min_periods=long_window // 2).std()

        # 计算波动率比率
        vol_ratio = short_vol / long_vol
        vol_ratio = vol_ratio.clip(0.5, 2.0)  # 限制范围

        # 根据波动率比率调整有效窗口
        # 高波动时使用较短窗口，低波动时使用较长窗口
        effective_window = (self.window / vol_ratio).astype(int)
        effective_window = effective_window.clip(short_window, long_window * 2)

        # 使用变化窗口计算均值和标准差（简化版：使用 EMA 近似）
        # 将窗口转换为衰减因子
        alpha = 2.0 / (effective_window + 1)
        alpha = alpha.fillna(2.0 / (self.window + 1))

        # 使用指数加权移动平均近似自适应窗口
        ma = prices.ewm(span=self.window, min_periods=self.min_periods).mean()
        std = prices.ewm(span=self.window, min_periods=self.min_periods).std()

        return ma, std


class MultiWindowDeviationCalculator:
    """多窗口偏移率计算器"""

    def __init__(
        self,
        windows: list = None,
        window_type: Literal["simple", "exponential"] = "simple",
    ):
        """
        初始化多窗口偏移率计算器

        Args:
            windows: 窗口列表，默认 [20, 60, 120, 252]
            window_type: 窗口类型
        """
        self.windows = windows or [20, 60, 120, 252]
        self.window_type = window_type
        self.logger = get_logger("deviation.multi_window")

    def calculate(
        self,
        prices: pd.Series,
        method: Literal["raw", "zscore", "all"] = "zscore",
    ) -> pd.DataFrame:
        """
        计算多窗口偏移率

        Args:
            prices: 价格序列
            method: 计算方法

        Returns:
            DataFrame 包含各窗口的偏移率
        """
        result = pd.DataFrame(index=prices.index)
        result["close"] = prices

        for window in self.windows:
            calc = DeviationCalculator(window=window, window_type=self.window_type)

            if method in ["raw", "all"]:
                result[f"dr_raw_{window}d"] = calc.calculate_raw(prices)

            if method in ["zscore", "all"]:
                result[f"dr_zscore_{window}d"] = calc.calculate_zscore(prices)

        return result

    def calculate_composite(
        self,
        prices: pd.Series,
        weights: Optional[list] = None,
    ) -> pd.Series:
        """
        计算加权复合偏移率

        Args:
            prices: 价格序列
            weights: 各窗口权重，默认等权

        Returns:
            复合偏移率序列
        """
        if weights is None:
            weights = [1.0 / len(self.windows)] * len(self.windows)

        if len(weights) != len(self.windows):
            raise ValueError("权重数量必须与窗口数量相同")

        df = self.calculate(prices, method="zscore")

        # 计算加权平均
        composite = pd.Series(0.0, index=prices.index)
        for window, weight in zip(self.windows, weights):
            col_name = f"dr_zscore_{window}d"
            if col_name in df.columns:
                composite += df[col_name].fillna(0) * weight

        return composite
