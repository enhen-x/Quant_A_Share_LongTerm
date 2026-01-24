"""
批量分布分析脚本

功能:
- 读取偏移率数据
- 计算分布统计量
- 分析分布形状
- 保存结果到 data/processed/distribution/




"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.logger import get_logger
from src.utils.io import ensure_dir, write_parquet, read_parquet
from src.distribution import StatsCalculator, ShapeAnalyzer, HistogramAnalyzer, KDEEstimator

logger = get_logger(__name__)

def analyze_single_stock(ts_code: str, deviation_dir: Path, config: Config) -> Optional[Dict[str, Any]]:
    """
    分析单只股票的偏移率分布
    """
    deviation_file = deviation_dir / f"{ts_code}.parquet"
    
    if not deviation_file.exists():
        logger.warning(f"偏移率文件不存在: {deviation_file}")
        return None
        
    try:
        df = read_parquet(deviation_file)
        
        # 获取主偏移率列
        dr_col = 'dr_raw' if 'dr_raw' in df.columns else 'dr_zscore'
        if dr_col not in df.columns:
            logger.warning(f"偏移率列不存在: {ts_code}")
            return None
            
        dr_data = df[dr_col].dropna()
        
        if len(dr_data) < 30:
            logger.warning(f"数据量不足: {ts_code}, count={len(dr_data)}")
            return None
            
        # 计算统计量
        stats = StatsCalculator.calculate_all(dr_data)
        
        # 分析形状
        analyzer = ShapeAnalyzer()
        shape_summary = analyzer.get_summary(stats)
        
        # 直方图峰值
        hist = HistogramAnalyzer.calculate_histogram(dr_data, bins='auto')
        peaks = HistogramAnalyzer.detect_peaks(hist['bin_centers'], hist['densities'])
        
        # KDE 众数
        kde_mode = KDEEstimator.get_mode_from_kde(dr_data)
        
        result = {
            "ts_code": ts_code,
            **stats,
            **shape_summary,
            "kde_mode": kde_mode,
            "num_peaks": len(peaks),
            "primary_peak": peaks[0]['location'] if peaks else np.nan
        }
        
        return result
        
    except Exception as e:
        logger.error(f"分析失败 {ts_code}: {e}")
        return None

def run_analysis(config_path: str = "config/main.yaml", max_workers: int = 4):
    """
    运行批量分布分析
    """
    config = Config(config_path)
    
    deviation_dir = Path(config.get("paths.data_processed", "data/processed")) / "deviation" / "stock"
    output_dir = Path(config.get("paths.data_processed", "data/processed")) / "distribution"
    ensure_dir(output_dir)
    
    # 获取所有偏移率文件
    if not deviation_dir.exists():
        logger.error(f"偏移率目录不存在: {deviation_dir}")
        return
        
    files = list(deviation_dir.glob("*.parquet"))
    ts_codes = [f.stem for f in files]
    
    logger.info(f"开始分析 {len(ts_codes)} 只股票的分布")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(analyze_single_stock, ts_code, deviation_dir, config): ts_code 
            for ts_code in ts_codes
        }
        
        for future in as_completed(futures):
            ts_code = futures[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"处理 {ts_code} 异常: {e}")
                
    if results:
        df = pd.DataFrame(results)
        output_file = output_dir / "distribution_summary.parquet"
        write_parquet(df, output_file)
        logger.info(f"保存分布分析结果: {output_file}, 共 {len(results)} 条记录")
        
        # 打印统计摘要
        print("\n=== 分布类型统计 ===")
        print(df['dist_type'].value_counts())
        
        print("\n=== 偏度类型统计 ===")
        print(df['skew_type'].value_counts())
        
        print("\n=== 峰度类型统计 ===")
        print(df['kurt_type'].value_counts())
    else:
        logger.warning("没有成功分析任何股票")

if __name__ == "__main__":
    run_analysis()
