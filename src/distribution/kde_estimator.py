import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional, Union

class KDEEstimator:
    """
    核密度估计器 (KDE)
    """
    
    @staticmethod
    def estimate_density(data: Union[np.ndarray, pd.Series], 
                        points: Optional[np.ndarray] = None,
                        bw_method: Optional[Union[str, float]] = None) -> Dict[str, Any]:
        """
        估算核密度
        
        Args:
            data: 输入数据
            points: 评估点，如果不提供则自动在数据范围内生成100个点
            bw_method: 带宽选择方法 ('scott', 'silverman' 或浮点数)
            
        Returns:
            包含 x (评估点) 和 y (密度值) 的字典
        """
        if isinstance(data, pd.Series):
            clean_data = data.dropna().values
        else:
            clean_data = data[~np.isnan(data)]
            
        if len(clean_data) < 2:
            return {"x": [], "y": [], "bw": np.nan}
            
        try:
            kde = stats.gaussian_kde(clean_data, bw_method=bw_method)
            
            if points is None:
                d_min, d_max = np.min(clean_data), np.max(clean_data)
                # 稍微扩大一点范围
                padding = (d_max - d_min) * 0.1
                points = np.linspace(d_min - padding, d_max + padding, 100)
                
            y = kde.evaluate(points)
            
            return {
                "x": points.tolist(),
                "y": y.tolist(),
                "bw": float(kde.factor)
            }
        except Exception:
            return {"x": [], "y": [], "bw": np.nan}

    @staticmethod
    def get_mode_from_kde(data: Union[np.ndarray, pd.Series]) -> float:
        """
        通过 KDE 找到分布的众数 (最高频点)
        """
        res = KDEEstimator.estimate_density(data)
        if not res["y"]:
            return np.nan
        
        idx = np.argmax(res["y"])
        return float(res["x"][idx])
