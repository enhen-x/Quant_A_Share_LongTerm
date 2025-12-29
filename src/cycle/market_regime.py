# src/cycle/market_regime.py
"""市场状态判断"""

import pandas as pd
import numpy as np

from ..utils.logger import get_logger


class MarketRegimeDetector:
    """市场状态检测器"""
    
    def __init__(self):
        self.logger = get_logger('market_regime')
    
    def detect_regime(
        self, 
        index_returns: pd.Series,
        volatility_window: int = 20
    ) -> str:
        """
        判断市场状态
        
        Returns:
            - 'bull': 牛市 (趋势向上 + 低波动)
            - 'bear': 熊市 (趋势向下 + 高波动)
            - 'volatile': 震荡市 (无明显趋势 + 高波动)
            - 'consolidation': 盘整期 (低波动 + 窄幅震荡)
        """
        # 计算近期波动率
        vol = index_returns.tail(volatility_window).std() * np.sqrt(252)
        
        # 计算趋势 (20日均线)
        price = (1 + index_returns).cumprod()
        ma20 = price.rolling(20).mean()
        trend = (price.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1]
        
        # 计算累计收益
        ret_20d = index_returns.tail(20).sum()
        
        # 判断阈值
        high_vol = vol > 0.25
        trend_up = trend > 0.03
        trend_down = trend < -0.03
        
        if trend_up and not high_vol:
            return 'bull'
        elif trend_down and high_vol:
            return 'bear'
        elif high_vol:
            return 'volatile'
        else:
            return 'consolidation'
    
    def get_regime_advice(self, regime: str) -> dict:
        """
        获取市场状态建议
        """
        advice_map = {
            'bull': {
                'position': '可满仓',
                'strategy': '持股待涨',
                'focus': '业绩增长股',
                'risk': '关注过热信号',
            },
            'bear': {
                'position': '轻仓防守',
                'strategy': '现金为王',
                'focus': '高股息防守股',
                'risk': '避免抄底',
            },
            'volatile': {
                'position': '中等仓位',
                'strategy': '波段操作',
                'focus': '低估值蓝筹',
                'risk': '控制回撤',
            },
            'consolidation': {
                'position': '标准仓位',
                'strategy': '精选个股',
                'focus': '行业龙头',
                'risk': '耐心等待突破',
            },
        }
        return advice_map.get(regime, {})
    
    def analyze(self, index_returns: pd.Series) -> dict:
        """
        综合市场分析
        """
        regime = self.detect_regime(index_returns)
        
        regime_names = {
            'bull': '牛市',
            'bear': '熊市',
            'volatile': '震荡市',
            'consolidation': '盘整期',
        }
        
        return {
            'regime': regime,
            'regime_cn': regime_names.get(regime, '未知'),
            'advice': self.get_regime_advice(regime),
            'volatility': index_returns.tail(20).std() * np.sqrt(252),
            'return_20d': index_returns.tail(20).sum(),
        }
