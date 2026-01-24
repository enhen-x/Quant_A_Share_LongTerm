import unittest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.distribution.stats_calculator import StatsCalculator
from src.distribution.shape_analyzer import ShapeAnalyzer
from src.distribution.histogram import HistogramAnalyzer
from src.distribution.kde_estimator import KDEEstimator

class TestDistribution(unittest.TestCase):
    
    def setUp(self):
        # 生成正态分布数据
        np.random.seed(42)
        self.normal_data = np.random.normal(0, 1, 1000)
        
        # 生成右偏分布数据 (对数正态)
        self.skewed_data = np.random.lognormal(0, 0.5, 1000)
        
        # 生成尖峰分布数据 (t分布，自由度低)
        self.fat_tail_data = np.random.standard_t(3, 1000)

    def test_stats_calculator(self):
        stats = StatsCalculator.calculate_all(self.normal_data)
        
        self.assertAlmostEqual(stats['mean'], 0, delta=0.1)
        self.assertAlmostEqual(stats['std'], 1, delta=0.1)
        self.assertIn('skew', stats)
        self.assertIn('kurtosis', stats)
        self.assertIn('q50', stats)
        
        # 验证偏度
        skew_val = StatsCalculator.calculate_distribution_stats(self.skewed_data)['skew']
        self.assertGreater(skew_val, 0)

    def test_shape_analyzer(self):
        analyzer = ShapeAnalyzer()
        
        # 正态分布分析
        normal_stats = StatsCalculator.calculate_all(self.normal_data)
        summary = analyzer.get_summary(normal_stats)
        self.assertEqual(summary['dist_type'], 'Normal')
        
        # 右偏分布分析
        skewed_stats = StatsCalculator.calculate_all(self.skewed_data)
        summary = analyzer.get_summary(skewed_stats)
        self.assertEqual(summary['skew_type'], 'RightSkewed')
        
        # 尖峰分布分析
        fat_stats = StatsCalculator.calculate_all(self.fat_tail_data)
        summary = analyzer.get_summary(fat_stats)
        self.assertEqual(summary['kurt_type'], 'Leptokurtic')

    def test_histogram_analyzer(self):
        hist = HistogramAnalyzer.calculate_histogram(self.normal_data, bins=20)
        self.assertEqual(len(hist['counts']), 20)
        self.assertEqual(len(hist['bin_centers']), 20)
        
        peaks = HistogramAnalyzer.detect_peaks(hist['bin_centers'], hist['densities'])
        self.assertGreater(len(peaks), 0)
        # 正态分布峰值应该在 0 附近
        self.assertAlmostEqual(peaks[0]['location'], 0, delta=0.5)

    def test_kde_estimator(self):
        res = KDEEstimator.estimate_density(self.normal_data)
        self.assertEqual(len(res['x']), 100)
        self.assertEqual(len(res['y']), 100)
        
        mode = KDEEstimator.get_mode_from_kde(self.normal_data)
        self.assertAlmostEqual(mode, 0, delta=0.5)

if __name__ == '__main__':
    unittest.main()
