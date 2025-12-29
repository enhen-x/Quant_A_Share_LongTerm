# src/position/base.py
"""仓位管理基类"""

from abc import ABC, abstractmethod
from typing import Dict, List
import pandas as pd


class PositionSizerBase(ABC):
    """仓位管理器抽象基类"""
    
    @abstractmethod
    def calculate_weights(
        self, 
        stocks: List[str], 
        **kwargs
    ) -> Dict[str, float]:
        """
        计算股票权重
        
        Args:
            stocks: 股票代码列表
            **kwargs: 其他参数 (如收益率、得分等)
            
        Returns:
            股票权重字典 {ts_code: weight}
        """
        pass
