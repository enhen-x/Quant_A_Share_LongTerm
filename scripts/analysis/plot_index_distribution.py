"""
指数偏移率分布可视化脚本

功能:
- 计算指数偏移率
- 绘制分布直方图和KDE曲线
- 保存图表到 figures/ 目录
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.logger import get_logger
from src.utils.io import ensure_dir, read_parquet
from src.deviation import DeviationCalculator
from src.distribution import StatsCalculator, ShapeAnalyzer, HistogramAnalyzer, KDEEstimator

logger = get_logger(__name__)

# 指数名称映射
INDEX_NAMES = {
    "000001.SH": "上证指数",
    "000300.SH": "沪深300",
    "000905.SH": "中证500",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
}

# 价格类型名称映射
PRICE_TYPE_NAMES = {
    "close": "收盘价",
    "vwap": "VWAP",
    "typical": "典型价格 (H+L+C)/3",
    "weighted_close": "加权收盘价 (H+L+2C)/4",
    "median": "中间价 (H+L)/2",
    "ohlc4": "OHLC4 (O+H+L+C)/4",
}

# 指数不支持的价格类型（会自动回退到 typical）
INDEX_UNSUPPORTED_PRICE_TYPES = {"vwap"}


def calculate_price_series(df, price_type: str = "close", is_index: bool = False):
    """
    根据指定的价格类型计算价格序列
    
    Args:
        df: 数据 DataFrame
        price_type: 价格类型
        is_index: 是否是指数数据
        
    Note:
        对于指数数据，VWAP 不适用（amount/vol 算出的是成分股平均价格，不是指数 VWAP），
        会自动使用 typical price 替代。
    """
    # 指数数据不支持 VWAP
    if is_index and price_type == "vwap":
        print(f"  注意: 指数不支持 VWAP（amount/vol 是成分股均价，不是指数 VWAP），使用 OHLC4 替代")
        price_type = "ohlc4"
    
    if price_type == "close":
        return df["close"], "close"
    elif price_type == "vwap":
        # 个股 VWAP: amount 单位千元, vol 单位手
        # VWAP = amount * 1000 / (vol * 100) = amount * 10 / vol
        if "amount" in df.columns and "vol" in df.columns:
            vol = df["vol"].replace(0, np.nan)
            vwap = df["amount"] * 10 / vol
            return vwap.fillna(df["close"]), "vwap"
        return df["close"], "close"
    elif price_type == "typical":
        return (df["high"] + df["low"] + df["close"]) / 3, "typical"
    elif price_type == "weighted_close":
        return (df["high"] + df["low"] + 2 * df["close"]) / 4, "weighted_close"
    elif price_type == "median":
        return (df["high"] + df["low"]) / 2, "median"
    elif price_type == "ohlc4":
        return (df["open"] + df["high"] + df["low"] + df["close"]) / 4, "ohlc4"
    return df["close"], "close"


def plot_index_distribution(ts_code: str, data_dir: Path, figures_dir: Path, 
                            window: int = 20, price_type: str = "ohlc4") -> bool:
    """
    绘制单个指数的偏移率分布图
    
    Args:
        ts_code: 指数代码
        data_dir: 数据目录
        figures_dir: 图表输出目录
        window: 移动均值窗口
        price_type: 价格类型
                   推荐: ohlc4=(O+H+L+C)/4 能体现全天价格水平
                   注意: 对于指数，vwap 会自动回退到 ohlc4
    """
    data_file = data_dir / f"{ts_code}.parquet"
    
    if not data_file.exists():
        logger.warning(f"数据文件不存在: {data_file}")
        return False
        
    try:
        df = read_parquet(data_file)
        df = df.sort_values('trade_date').reset_index(drop=True)
        
        # 根据价格类型计算价格序列（指数数据会自动处理不支持的类型）
        prices, actual_price_type = calculate_price_series(df, price_type, is_index=True)
        
        # 计算偏移率
        calculator = DeviationCalculator(window=window, window_type='simple')
        result = calculator.calculate(prices)
        
        dr_raw = result['dr_raw'].dropna()
        dr_zscore = result['dr_zscore'].dropna()
        
        if len(dr_raw) < 30:
            logger.warning(f"数据量不足: {ts_code}")
            return False
        
        # 计算统计量
        stats_raw = StatsCalculator.calculate_all(dr_raw)
        analyzer = ShapeAnalyzer()
        shape_summary = analyzer.get_summary(stats_raw)
        
        # 使用实际使用的价格类型名称
        price_type_name = PRICE_TYPE_NAMES.get(actual_price_type, actual_price_type)
        
        # 创建图表 (2x2 布局)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        index_name = INDEX_NAMES.get(ts_code, ts_code)
        fig.suptitle(f'{index_name} ({ts_code}) 偏移率分布分析\n价格基准: {price_type_name} | 窗口: {window}日', 
                     fontsize=14, fontweight='bold')
        
        # === 子图1: 原始偏移率直方图 + KDE ===
        ax1 = axes[0, 0]
        hist_data = HistogramAnalyzer.calculate_histogram(dr_raw, bins=50)
        ax1.bar(hist_data['bin_centers'], hist_data['densities'], 
                width=hist_data['bin_width']*0.9, alpha=0.6, color='steelblue', label='直方图')
        
        # KDE 曲线
        kde_result = KDEEstimator.estimate_density(dr_raw)
        ax1.plot(kde_result['x'], kde_result['y'], 'r-', linewidth=2, label='KDE')
        
        ax1.axvline(x=0, color='gray', linestyle='--', alpha=0.7)
        ax1.axvline(x=stats_raw['mean'], color='green', linestyle='-', alpha=0.7, label=f"均值: {stats_raw['mean']:.4f}")
        ax1.set_xlabel('偏移率 (原始)')
        ax1.set_ylabel('密度')
        ax1.set_title('原始偏移率分布 (close - MA) / MA')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        
        # === 子图2: Z-score 偏移率直方图 ===
        ax2 = axes[0, 1]
        stats_z = StatsCalculator.calculate_all(dr_zscore)
        hist_z = HistogramAnalyzer.calculate_histogram(dr_zscore, bins=50)
        ax2.bar(hist_z['bin_centers'], hist_z['densities'], 
                width=hist_z['bin_width']*0.9, alpha=0.6, color='coral', label='直方图')
        
        kde_z = KDEEstimator.estimate_density(dr_zscore)
        ax2.plot(kde_z['x'], kde_z['y'], 'darkred', linewidth=2, label='KDE')
        
        # 叠加标准正态分布
        from scipy import stats as sp_stats
        x_norm = np.linspace(-4, 4, 100)
        y_norm = sp_stats.norm.pdf(x_norm)
        ax2.plot(x_norm, y_norm, 'g--', linewidth=1.5, alpha=0.7, label='标准正态')
        
        ax2.axvline(x=0, color='gray', linestyle='--', alpha=0.7)
        ax2.set_xlabel('偏移率 (Z-score)')
        ax2.set_ylabel('密度')
        ax2.set_title('Z-score 偏移率分布 vs 标准正态')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(-4, 4)
        
        # === 子图3: 时间序列 ===
        ax3 = axes[1, 0]
        dates = pd.to_datetime(df['trade_date'].astype(str))
        # 对齐日期和偏移率数据
        valid_idx = result['dr_raw'].dropna().index
        ax3.plot(dates.iloc[valid_idx], dr_raw.values, linewidth=0.8, color='steelblue', alpha=0.7)
        ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
        ax3.axhline(y=stats_raw['q5'], color='green', linestyle=':', alpha=0.7, label=f"5%分位: {stats_raw['q5']:.4f}")
        ax3.axhline(y=stats_raw['q95'], color='red', linestyle=':', alpha=0.7, label=f"95%分位: {stats_raw['q95']:.4f}")
        ax3.set_xlabel('日期')
        ax3.set_ylabel('偏移率')
        ax3.set_title('偏移率时间序列')
        ax3.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)
        
        # === 子图4: 统计信息表 ===
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        info_text = f"""
【基础统计量】
  样本数: {stats_raw['count']}
  均值: {stats_raw['mean']:.6f}
  标准差: {stats_raw['std']:.6f}
  最小值: {stats_raw['min']:.6f}
  最大值: {stats_raw['max']:.6f}

【分布特征】
  偏度: {stats_raw['skew']:.4f}  ({shape_summary['skew_label']})
  峰度: {stats_raw['kurtosis']:.4f}  ({shape_summary['kurt_label']})
  JB统计量: {stats_raw['jb_stat']:.2f}
  JB p-value: {stats_raw['jb_pvalue']:.4f}
  
【分位数】
  5%: {stats_raw['q5']:.6f}
  25%: {stats_raw['q25']:.6f}
  50%: {stats_raw['q50']:.6f}
  75%: {stats_raw['q75']:.6f}
  95%: {stats_raw['q95']:.6f}

【分布类型判定】
  {shape_summary['dist_type']}
"""
        ax4.text(0.1, 0.95, info_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        # 保存图表（使用实际使用的价格类型）
        output_file = figures_dir / f"distribution_{ts_code.replace('.', '_')}_{actual_price_type}_w{window}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"保存分布图: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"绑制分布图失败 {ts_code}: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_visualization(config_path: str = "config/main.yaml", window: int = 20, price_type: str = "ohlc4"):
    """
    运行指数分布可视化
    
    Args:
        config_path: 配置文件路径
        window: 移动均值窗口
        price_type: 价格类型（对于指数，默认 ohlc4=(O+H+L+C)/4，vwap 会自动回退到 ohlc4）
    """
    config = Config(config_path)
    
    data_dir = Path(config.get("data.raw_dir", "data/raw")) / "index"
    figures_dir = Path("figures") / "distribution" / "index"
    ensure_dir(figures_dir)
    
    # 获取所有指数文件
    if not data_dir.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        return
        
    files = list(data_dir.glob("*.parquet"))
    ts_codes = [f.stem for f in files]
    
    price_type_name = PRICE_TYPE_NAMES.get(price_type, price_type)
    logger.info(f"开始绑制 {len(ts_codes)} 个指数的分布图 (价格基准: {price_type_name})")
    
    success_count = 0
    for ts_code in ts_codes:
        if plot_index_distribution(ts_code, data_dir, figures_dir, window, price_type):
            success_count += 1
            
    logger.info(f"完成! 成功绘制 {success_count}/{len(ts_codes)} 个指数")
    print(f"\n图表已保存到: {figures_dir.absolute()}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='指数偏移率分布可视化')
    parser.add_argument('--window', type=int, default=20, help='移动均值窗口 (默认20)')
    parser.add_argument('--price-type', type=str, default='ohlc4',
                       choices=['close', 'vwap', 'typical', 'weighted_close', 'median', 'ohlc4'],
                       help='价格类型: ohlc4=(O+H+L+C)/4(默认,体现全天价格), typical=(H+L+C)/3, vwap(指数自动回退到ohlc4)')
    args = parser.parse_args()
    
    run_visualization(window=args.window, price_type=args.price_type)
