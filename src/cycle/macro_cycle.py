# src/cycle/macro_cycle.py
"""宏观经济周期分析"""

from typing import Dict, List
from ..utils.config import load_config
from ..utils.logger import get_logger


class MacroCycleAnalyzer:
    """宏观经济周期分析器"""
    
    PHASES = ['recovery', 'expansion', 'stagflation', 'recession']
    
    def __init__(self, config: dict = None):
        self.logger = get_logger('macro_cycle')
        
        if config is None:
            full_config = load_config()
            config = full_config.get('macro_cycle', {})
        
        self.config = config
        self.gdp_threshold = config.get('gdp_growth_threshold', 6.0)
        self.cpi_threshold = config.get('cpi_inflation_threshold', 3.0)
        self.sector_rotation = config.get('sector_rotation', {})
    
    def get_cycle_phase(
        self, 
        gdp_growth: float, 
        cpi: float
    ) -> str:
        """
        判断当前宏观周期位置
        
        Args:
            gdp_growth: GDP 同比增速 (%)
            cpi: CPI 同比 (%)
            
        Returns:
            周期阶段:
            - 'recovery': 复苏期 (GDP↑, CPI↓)
            - 'expansion': 扩张期 (GDP↑, CPI↑)
            - 'stagflation': 滞胀期 (GDP↓, CPI↑)
            - 'recession': 衰退期 (GDP↓, CPI↓)
        """
        gdp_up = gdp_growth >= self.gdp_threshold
        cpi_up = cpi >= self.cpi_threshold
        
        if gdp_up and not cpi_up:
            return 'recovery'
        elif gdp_up and cpi_up:
            return 'expansion'
        elif not gdp_up and cpi_up:
            return 'stagflation'
        else:
            return 'recession'
    
    def get_sector_allocation(self, phase: str = None) -> List[str]:
        """
        基于周期阶段的行业配置建议
        
        Returns:
            推荐行业列表
        """
        default_rotation = {
            'recovery': ['消费', '金融', '房地产'],
            'expansion': ['科技', '周期', '工业'],
            'stagflation': ['能源', '原材料', '必选消费'],
            'recession': ['公用事业', '医药', '债券'],
        }
        
        rotation = self.sector_rotation or default_rotation
        return rotation.get(phase, [])
    
    def analyze(
        self, 
        gdp_growth: float, 
        cpi: float,
        pmi: float = None,
        m2_growth: float = None
    ) -> Dict:
        """
        综合宏观分析
        
        Returns:
            {
                "phase": 周期阶段,
                "phase_cn": 中文名称,
                "recommended_sectors": 推荐行业,
                "indicators": 指标详情,
                "outlook": 展望
            }
        """
        phase = self.get_cycle_phase(gdp_growth, cpi)
        
        phase_names = {
            'recovery': '复苏期',
            'expansion': '扩张期',
            'stagflation': '滞胀期',
            'recession': '衰退期',
        }
        
        outlook_map = {
            'recovery': '经济回暖，可适度增加风险敞口',
            'expansion': '经济过热，注意回调风险',
            'stagflation': '谨慎防守，关注抗通胀资产',
            'recession': '防守为主，保持流动性',
        }
        
        return {
            "phase": phase,
            "phase_cn": phase_names.get(phase, '未知'),
            "recommended_sectors": self.get_sector_allocation(phase),
            "indicators": {
                "gdp_growth": gdp_growth,
                "cpi": cpi,
                "pmi": pmi,
                "m2_growth": m2_growth,
            },
            "outlook": outlook_map.get(phase, ''),
        }
