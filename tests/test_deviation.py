"""
偏移率计算模块测试

测试内容:
- DeviationCalculator 偏移率计算
- RollingStats 滚动统计
- 各种标准化方法
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.deviation import (
    DeviationCalculator,
    MultiWindowDeviationCalculator,
    RollingStats,
    EWMStats,
    ExpandingStats,
    ZScoreNormalizer,
    MinMaxNormalizer,
    PercentileNormalizer,
    RobustNormalizer,
    zscore_normalize,
    minmax_normalize,
    rolling_zscore_normalize,
    normalize,
)


# ============================================================================
# 测试数据生成
# ============================================================================


def generate_test_prices(n_days: int = 500, seed: int = 42) -> pd.Series:
    """生成测试价格序列"""
    np.random.seed(seed)
    
    # 生成随机价格（几何布朗运动）
    returns = np.random.normal(0.0005, 0.02, n_days)  # 日收益率
    prices = 100 * np.exp(np.cumsum(returns))
    
    # 创建日期索引
    dates = pd.date_range(start="2020-01-01", periods=n_days, freq="B")
    
    return pd.Series(prices, index=dates, name="close")


def generate_normal_data(n: int = 1000, mean: float = 0, std: float = 1, seed: int = 42) -> pd.Series:
    """生成正态分布数据"""
    np.random.seed(seed)
    data = np.random.normal(mean, std, n)
    return pd.Series(data)


# ============================================================================
# DeviationCalculator 测试
# ============================================================================


class TestDeviationCalculator:
    """测试偏移率计算器"""
    
    def test_init(self):
        """测试初始化"""
        calc = DeviationCalculator(window=252, window_type="simple")
        assert calc.window == 252
        assert calc.window_type == "simple"
        assert calc.min_periods == 126  # 默认为 window // 2
    
    def test_calculate_all(self):
        """测试计算所有偏移率"""
        prices = generate_test_prices(300)
        calc = DeviationCalculator(window=60)
        
        result = calc.calculate(prices, method="all")
        
        # 检查列
        assert "close" in result.columns
        assert "ma" in result.columns
        assert "std" in result.columns
        assert "dr_raw" in result.columns
        assert "dr_zscore" in result.columns
        assert "dr_percentile" in result.columns
        
        # 检查非空值
        valid_data = result.dropna()
        assert len(valid_data) > 0
    
    def test_calculate_raw(self):
        """测试原始偏移率计算"""
        prices = generate_test_prices(200)
        calc = DeviationCalculator(window=50)
        
        dr_raw = calc.calculate_raw(prices)
        
        # 手动验证
        ma = prices.rolling(window=50, min_periods=25).mean()
        expected = (prices - ma) / ma
        
        # 比较（忽略 NaN）
        valid_idx = ~dr_raw.isna() & ~expected.isna()
        np.testing.assert_allclose(
            dr_raw[valid_idx].values,
            expected[valid_idx].values,
            rtol=1e-10
        )
    
    def test_calculate_zscore(self):
        """测试 Z-score 偏移率计算"""
        prices = generate_test_prices(200)
        calc = DeviationCalculator(window=50)
        
        dr_zscore = calc.calculate_zscore(prices)
        
        # 手动验证
        ma = prices.rolling(window=50, min_periods=25).mean()
        std = prices.rolling(window=50, min_periods=25).std()
        expected = (prices - ma) / std
        
        valid_idx = ~dr_zscore.isna() & ~expected.isna()
        np.testing.assert_allclose(
            dr_zscore[valid_idx].values,
            expected[valid_idx].values,
            rtol=1e-10
        )
    
    def test_exponential_window(self):
        """测试指数加权窗口"""
        prices = generate_test_prices(200)
        calc = DeviationCalculator(window=50, window_type="exponential")
        
        result = calc.calculate(prices, method="zscore")
        
        assert "dr_zscore" in result.columns
        valid_data = result["dr_zscore"].dropna()
        assert len(valid_data) > 0
    
    def test_empty_input(self):
        """测试空输入"""
        prices = pd.Series([], dtype=float)
        calc = DeviationCalculator()
        
        result = calc.calculate(prices)
        
        assert result.empty


class TestMultiWindowDeviationCalculator:
    """测试多窗口偏移率计算器"""
    
    def test_calculate(self):
        """测试多窗口计算"""
        prices = generate_test_prices(400)
        calc = MultiWindowDeviationCalculator(windows=[20, 60, 120])
        
        result = calc.calculate(prices, method="all")
        
        # 检查各窗口列
        assert "dr_raw_20d" in result.columns
        assert "dr_raw_60d" in result.columns
        assert "dr_raw_120d" in result.columns
        assert "dr_zscore_20d" in result.columns
        assert "dr_zscore_60d" in result.columns
        assert "dr_zscore_120d" in result.columns
    
    def test_composite(self):
        """测试复合偏移率"""
        prices = generate_test_prices(400)
        calc = MultiWindowDeviationCalculator(windows=[20, 60, 120])
        
        composite = calc.calculate_composite(prices)
        
        assert len(composite) == len(prices)


# ============================================================================
# RollingStats 测试
# ============================================================================


class TestRollingStats:
    """测试滚动统计"""
    
    def test_rolling_mean(self):
        """测试滚动均值"""
        data = generate_normal_data(200)
        stats = RollingStats(window=50)
        
        result = stats.rolling_mean(data)
        expected = data.rolling(window=50, min_periods=25).mean()
        
        valid_idx = ~result.isna() & ~expected.isna()
        np.testing.assert_allclose(
            result[valid_idx].values,
            expected[valid_idx].values,
            rtol=1e-10
        )
    
    def test_rolling_std(self):
        """测试滚动标准差"""
        data = generate_normal_data(200)
        stats = RollingStats(window=50)
        
        result = stats.rolling_std(data)
        expected = data.rolling(window=50, min_periods=25).std()
        
        valid_idx = ~result.isna() & ~expected.isna()
        np.testing.assert_allclose(
            result[valid_idx].values,
            expected[valid_idx].values,
            rtol=1e-10
        )
    
    def test_rolling_skew(self):
        """测试滚动偏度"""
        data = generate_normal_data(200)
        stats = RollingStats(window=50)
        
        result = stats.rolling_skew(data)
        
        # 正态分布的偏度应该接近 0
        valid_skew = result.dropna()
        assert valid_skew.mean() < 1  # 宽松检查
    
    def test_rolling_stats_all(self):
        """测试完整滚动统计"""
        data = generate_normal_data(200)
        stats = RollingStats(window=50)
        
        result = stats.calculate_rolling_stats(data)
        
        assert "rolling_mean" in result.columns
        assert "rolling_std" in result.columns
        assert "rolling_min" in result.columns
        assert "rolling_max" in result.columns
        assert "rolling_median" in result.columns
        assert "rolling_skew" in result.columns
        assert "rolling_kurt" in result.columns
    
    def test_rolling_quantiles(self):
        """测试滚动分位数"""
        data = generate_normal_data(200)
        stats = RollingStats(window=50)
        
        result = stats.rolling_quantiles(data)
        
        assert "q05" in result.columns
        assert "q50" in result.columns
        assert "q95" in result.columns


class TestEWMStats:
    """测试指数加权移动统计"""
    
    def test_ewm_mean(self):
        """测试 EWM 均值"""
        data = generate_normal_data(200)
        stats = EWMStats(span=50)
        
        result = stats.ewm_mean(data)
        expected = data.ewm(span=50, min_periods=25).mean()
        
        valid_idx = ~result.isna() & ~expected.isna()
        np.testing.assert_allclose(
            result[valid_idx].values,
            expected[valid_idx].values,
            rtol=1e-10
        )
    
    def test_ewm_stats(self):
        """测试完整 EWM 统计"""
        data = generate_normal_data(200)
        stats = EWMStats(span=50)
        
        result = stats.ewm_stats(data)
        
        assert "ewm_mean" in result.columns
        assert "ewm_std" in result.columns
        assert "ewm_zscore" in result.columns


# ============================================================================
# Normalization 测试
# ============================================================================


class TestZScoreNormalizer:
    """测试 Z-score 标准化"""
    
    def test_fit_transform(self):
        """测试拟合和转换"""
        data = generate_normal_data(1000, mean=10, std=2)
        normalizer = ZScoreNormalizer()
        
        result = normalizer.fit_transform(data)
        
        # 标准化后均值应接近 0，标准差应接近 1
        assert abs(result.mean()) < 0.1
        assert abs(result.std() - 1) < 0.1
    
    def test_inverse_transform(self):
        """测试逆转换"""
        data = generate_normal_data(1000, mean=10, std=2)
        normalizer = ZScoreNormalizer()
        
        normalized = normalizer.fit_transform(data)
        recovered = normalizer.inverse_transform(normalized)
        
        np.testing.assert_allclose(data.values, recovered.values, rtol=1e-10)


class TestMinMaxNormalizer:
    """测试 Min-Max 标准化"""
    
    def test_fit_transform_default(self):
        """测试默认范围 (0, 1)"""
        data = generate_normal_data(1000, mean=10, std=2)
        normalizer = MinMaxNormalizer()
        
        result = normalizer.fit_transform(data)
        
        assert result.min() >= 0
        assert result.max() <= 1
    
    def test_fit_transform_custom_range(self):
        """测试自定义范围"""
        data = generate_normal_data(1000)
        normalizer = MinMaxNormalizer(feature_range=(-1, 1))
        
        result = normalizer.fit_transform(data)
        
        assert result.min() >= -1
        assert result.max() <= 1
    
    def test_inverse_transform(self):
        """测试逆转换"""
        data = generate_normal_data(1000)
        normalizer = MinMaxNormalizer()
        
        normalized = normalizer.fit_transform(data)
        recovered = normalizer.inverse_transform(normalized)
        
        np.testing.assert_allclose(data.values, recovered.values, rtol=1e-10)


class TestPercentileNormalizer:
    """测试百分位标准化"""
    
    def test_fit_transform(self):
        """测试百分位转换"""
        data = generate_normal_data(1000)
        normalizer = PercentileNormalizer()
        
        result = normalizer.fit_transform(data)
        
        # 百分位范围应该是 0-100
        assert result.min() >= 0
        assert result.max() <= 100
        # 中位数应该接近 50
        assert abs(result.median() - 50) < 10


class TestRobustNormalizer:
    """测试 Robust 标准化"""
    
    def test_fit_transform(self):
        """测试 Robust 转换"""
        data = generate_normal_data(1000, mean=10, std=2)
        normalizer = RobustNormalizer()
        
        result = normalizer.fit_transform(data)
        
        # 中位数应该接近 0
        assert abs(result.median()) < 0.1
    
    def test_with_outliers(self):
        """测试含异常值的数据"""
        data = generate_normal_data(1000)
        # 添加异常值
        data.iloc[0] = 100
        data.iloc[1] = -100
        
        normalizer = RobustNormalizer()
        result = normalizer.fit_transform(data)
        
        # Robust 标准化应该不受异常值太大影响
        # 大部分数据应该在合理范围内
        within_range = (result.abs() < 10).sum() / len(result)
        assert within_range > 0.95


class TestNormalizationFunctions:
    """测试标准化函数接口"""
    
    def test_zscore_normalize(self):
        """测试 zscore_normalize 函数"""
        data = generate_normal_data(100, mean=10, std=2)
        result = zscore_normalize(data)
        
        assert abs(result.mean()) < 0.2
        assert abs(result.std() - 1) < 0.2
    
    def test_minmax_normalize(self):
        """测试 minmax_normalize 函数"""
        data = generate_normal_data(100)
        result = minmax_normalize(data)
        
        assert result.min() >= 0
        assert result.max() <= 1
    
    def test_normalize_factory(self):
        """测试 normalize 工厂函数"""
        data = generate_normal_data(100)
        
        for method in ["zscore", "minmax", "percentile", "robust", "decimal"]:
            result = normalize(data, method=method)
            assert len(result) == len(data)
    
    def test_rolling_zscore_normalize(self):
        """测试滚动 Z-score 标准化"""
        data = generate_normal_data(200)
        result = rolling_zscore_normalize(data, window=50)
        
        valid_result = result.dropna()
        # 滚动 Z-score 应该在合理范围内
        assert valid_result.mean() < 1


# ============================================================================
# 运行测试
# ============================================================================


if __name__ == "__main__":
    # 使用 pytest 运行
    pytest.main([__file__, "-v", "--tb=short"])
