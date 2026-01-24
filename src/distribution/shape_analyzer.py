from typing import Dict, Any, List
import numpy as np

class ShapeAnalyzer:
    """
    分布形状分析器，用于判定偏度和峰度的性质
    """
    
    def __init__(self, skew_threshold: float = 0.5, kurt_threshold: float = 1.0):
        """
        Args:
            skew_threshold: 判定偏斜的阈值 (通常 0.5 为轻微，1.0 为显著)
            kurt_threshold: 判定峰度的阈值 (通常 1.0 为显著偏离正态)
        """
        self.skew_threshold = skew_threshold
        self.kurt_threshold = kurt_threshold

    def analyze_skewness(self, skew: float) -> Dict[str, Any]:
        """
        分析偏度类型
        """
        if np.isnan(skew):
            return {"type": "Unknown", "label": "未知", "severity": 0}
            
        abs_skew = abs(skew)
        
        if abs_skew < self.skew_threshold:
            return {"type": "Symmetric", "label": "对称", "severity": 0}
        
        severity = 1 if abs_skew < 1.0 else 2
        
        if skew > 0:
            return {"type": "RightSkewed", "label": "右偏 (正偏)", "severity": severity}
        else:
            return {"type": "LeftSkewed", "label": "左偏 (负偏)", "severity": severity}

    def analyze_kurtosis(self, kurt: float) -> Dict[str, Any]:
        """
        分析峰度类型 (基于 Fisher 定义，正态分布为 0)
        """
        if np.isnan(kurt):
            return {"type": "Unknown", "label": "未知", "severity": 0}
            
        if abs(kurt) < self.kurt_threshold:
            return {"type": "Mesokurtic", "label": "常峰", "severity": 0}
            
        if kurt > 0:
            # 尖峰长尾
            severity = 1 if kurt < 3.0 else 2
            return {"type": "Leptokurtic", "label": "尖峰", "severity": severity}
        else:
            # 扁平
            severity = 1 if kurt > -1.0 else 2
            return {"type": "Platykurtic", "label": "扁平", "severity": severity}

    def determine_distribution_type(self, stats: Dict[str, float]) -> str:
        """
        综合判定分布类型，用于后续网格选择建议
        """
        skew = stats.get("skew", 0)
        kurt = stats.get("kurtosis", 0)
        jb_p = stats.get("jb_pvalue", 1.0)
        
        # 统计学意义上的非正态
        is_not_normal = jb_p < 0.05
        
        skew_info = self.analyze_skewness(skew)
        kurt_info = self.analyze_kurtosis(kurt)
        
        if not is_not_normal and skew_info["type"] == "Symmetric" and kurt_info["type"] == "Mesokurtic":
            return "Normal"
            
        if skew_info["type"] == "RightSkewed":
            return "RightSkewed_FatTail" if kurt_info["type"] == "Leptokurtic" else "RightSkewed"
            
        if skew_info["type"] == "LeftSkewed":
            return "LeftSkewed_FatTail" if kurt_info["type"] == "Leptokurtic" else "LeftSkewed"
            
        if kurt_info["type"] == "Leptokurtic":
            return "FatTail_Symmetric"
            
        if kurt_info["type"] == "Platykurtic":
            return "Platykurtic"
            
        return "Complex"

    def get_summary(self, stats: Dict[str, float]) -> Dict[str, Any]:
        """
        获取分布形状的完整摘要报告
        """
        skew = stats.get("skew", np.nan)
        kurt = stats.get("kurtosis", np.nan)
        
        skew_analysis = self.analyze_skewness(skew)
        kurt_analysis = self.analyze_kurtosis(kurt)
        dist_type = self.determine_distribution_type(stats)
        
        return {
            "skew_type": skew_analysis["type"],
            "skew_label": skew_analysis["label"],
            "skew_severity": skew_analysis["severity"],
            "kurt_type": kurt_analysis["type"],
            "kurt_label": kurt_analysis["label"],
            "kurt_severity": kurt_analysis["severity"],
            "dist_type": dist_type
        }
