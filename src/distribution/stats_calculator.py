import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Union, Any

class StatsCalculator:
    """
    偏移率分布统计量计算器
    """
    
    @staticmethod
    def calculate_basic_stats(data: Union[np.ndarray, pd.Series, List[float]]) -> Dict[str, float]:
        """
        计算基础统计量
        
        Args:
            data: 输入数据
            
        Returns:
            包含均值、标准差、最小值、最大值、中位数、众数的字典
        """
        if isinstance(data, list):
            data = np.array(data)
        
        # 移除空值
        if isinstance(data, pd.Series):
            clean_data = data.dropna().values
        else:
            clean_data = data[~np.isnan(data)]
            
        if len(clean_data) == 0:
            return {
                "mean": np.nan, "std": np.nan, "min": np.nan, "max": np.nan,
                "median": np.nan, "mode": np.nan, "count": 0
            }
            
        # 众数计算
        mode_res = stats.mode(clean_data, keepdims=True)
        mode_val = mode_res.mode[0] if len(mode_res.mode) > 0 else np.nan
        
        return {
            "mean": float(np.mean(clean_data)),
            "std": float(np.std(clean_data, ddof=1)) if len(clean_data) > 1 else 0.0,
            "min": float(np.min(clean_data)),
            "max": float(np.max(clean_data)),
            "median": float(np.median(clean_data)),
            "mode": float(mode_val),
            "count": int(len(clean_data))
        }
    
    @staticmethod
    def calculate_distribution_stats(data: Union[np.ndarray, pd.Series]) -> Dict[str, float]:
        """
        计算分布特征统计量 (偏度、峰度、正态性检验)
        
        Args:
            data: 输入数据
            
        Returns:
            包含偏度、峰度、JB统计量、JB-p值的字典
        """
        if isinstance(data, pd.Series):
            clean_data = data.dropna().values
        else:
            clean_data = data[~np.isnan(data)]
            
        if len(clean_data) < 3:
            return {
                "skew": np.nan, "kurtosis": np.nan, 
                "jb_stat": np.nan, "jb_pvalue": np.nan
            }
            
        # 偏度 (Skewness)
        skew = float(stats.skew(clean_data))
        
        # 峰度 (Kurtosis) - Fisher定义 (正态分布为0)
        kurt = float(stats.kurtosis(clean_data))
        
        # Jarque-Bera 正态性检验
        jb_stat, jb_p = stats.jarque_bera(clean_data)
        
        return {
            "skew": skew,
            "kurtosis": kurt,
            "jb_stat": float(jb_stat),
            "jb_pvalue": float(jb_p)
        }
        
    @staticmethod
    def calculate_quantiles(data: Union[np.ndarray, pd.Series], 
                           qs: List[float] = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]) -> Dict[str, float]:
        """
        计算分位数
        
        Args:
            data: 输入数据
            qs: 分位数列表 (0-1之间)
            
        Returns:
            分位数映射字典
        """
        if isinstance(data, pd.Series):
            clean_data = data.dropna().values
        else:
            clean_data = data[~np.isnan(data)]
            
        if len(clean_data) == 0:
            return {f"q{int(q*100)}": np.nan for q in qs}
            
        quantiles = np.quantile(clean_data, qs)
        
        return {f"q{int(q*100)}": float(val) for q, val in zip(qs, quantiles)}

    @classmethod
    def calculate_all(cls, data: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """
        计算所有统计量汇总
        """
        res = {}
        res.update(cls.calculate_basic_stats(data))
        res.update(cls.calculate_distribution_stats(data))
        res.update(cls.calculate_quantiles(data))
        return res
