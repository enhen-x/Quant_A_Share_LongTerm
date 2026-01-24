import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional, Union

class HistogramAnalyzer:
    """
    直方图分析器，用于计算分布的频数和密度
    """
    
    @staticmethod
    def calculate_histogram(data: Union[np.ndarray, pd.Series], 
                           bins: Union[int, str] = 'auto') -> Dict[str, Any]:
        """
        计算直方图数据
        
        Args:
            data: 输入数据
            bins: 分箱数量或方法 ('auto', 'fd', 'sturges' 等)
            
        Returns:
            包含 counts, bin_edges, bin_centers, bin_width 的字典
        """
        if isinstance(data, pd.Series):
            clean_data = data.dropna().values
        else:
            clean_data = data[~np.isnan(data)]
            
        if len(clean_data) == 0:
            return {"counts": [], "bin_edges": [], "bin_centers": [], "bin_width": 0}
            
        counts, bin_edges = np.histogram(clean_data, bins=bins, density=False)
        
        # 计算密度
        densities, _ = np.histogram(clean_data, bins=bin_edges, density=True)
        
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_width = float(bin_edges[1] - bin_edges[0]) if len(bin_edges) > 1 else 0.0
        
        return {
            "counts": counts.tolist(),
            "densities": densities.tolist(),
            "bin_edges": bin_edges.tolist(),
            "bin_centers": bin_centers.tolist(),
            "bin_width": bin_width,
            "total_count": int(len(clean_data))
        }

    @staticmethod
    def detect_peaks(bin_centers: List[float], densities: List[float], 
                    min_height_ratio: float = 0.1) -> List[Dict[str, float]]:
        """
        简单的峰值检测
        
        Args:
            bin_centers: 箱中心位置
            densities: 对应密度
            min_height_ratio: 最小高度比例 (相对于最大密度)
            
        Returns:
            峰值列表，每个峰值包含 location 和 density
        """
        if not densities:
            return []
            
        densities = np.array(densities)
        max_density = np.max(densities)
        threshold = max_density * min_height_ratio
        
        peaks = []
        for i in range(1, len(densities) - 1):
            if densities[i] > densities[i-1] and densities[i] > densities[i+1] and densities[i] > threshold:
                peaks.append({
                    "location": float(bin_centers[i]),
                    "density": float(densities[i])
                })
        
        # 边界检查
        if len(densities) > 1:
            if densities[0] > densities[1] and densities[0] > threshold:
                peaks.insert(0, {"location": float(bin_centers[0]), "density": float(densities[0])})
            if densities[-1] > densities[-2] and densities[-1] > threshold:
                peaks.append({"location": float(bin_centers[-1]), "density": float(densities[-1])})
                
        return sorted(peaks, key=lambda x: x["density"], reverse=True)
