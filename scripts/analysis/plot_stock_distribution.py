"""
个股偏移率分布可视化脚本

功能:
- 计算个股偏移率
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

# 价格类型名称映射
PRICE_TYPE_NAMES = {
    "close": "收盘价",
    "vwap": "VWAP (成交额加权)",
    "typical": "典型价格 (H+L+C)/3",
    "weighted_close": "加权收盘价 (H+L+2C)/4",
    "median": "中间价 (H+L)/2",
    "ohlc4": "OHLC4 (O+H+L+C)/4",
}


def calculate_price_series(df, price_type: str = "vwap"):
    """
    根据指定的价格类型计算价格序列
    
    Args:
        df: 数据 DataFrame
        price_type: 价格类型
        
    Returns:
        (价格序列, 实际使用的价格类型)
    """
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


def plot_stock_distribution(ts_code: str, data_dir: Path, figures_dir: Path, 
                            window: int = 20, price_type: str = "vwap") -> bool:
    """
    绘制单个股票的偏移率分布图
    
    Args:
        ts_code: 股票代码
        data_dir: 数据目录
        figures_dir: 图表输出目录
        window: 移动均值窗口
        price_type: 价格类型 (推荐 vwap，能体现真实成交价格)
    """
    data_file = data_dir / f"{ts_code}.parquet"
    
    if not data_file.exists():
        logger.warning(f"数据文件不存在: {data_file}")
        return False
        
    try:
        df = read_parquet(data_file)
        df = df.sort_values('trade_date').reset_index(drop=True)
        
        # 获取股票名称
        stock_name = df['ts_code'].iloc[0] if 'ts_code' in df.columns else ts_code
        
        # 根据价格类型计算价格序列
        prices, actual_price_type = calculate_price_series(df, price_type)
        
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
        fig.suptitle(f'{stock_name} 偏移率分布分析\n价格基准: {price_type_name} | 窗口: {window}日', 
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
        ax1.set_title('原始偏移率分布 (price - MA) / MA')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        
        # === 子图2: Z-score 标准化偏移率 ===
        ax2 = axes[0, 1]
        stats_zscore = StatsCalculator.calculate_all(dr_zscore)
        hist_data_z = HistogramAnalyzer.calculate_histogram(dr_zscore, bins=50)
        ax2.bar(hist_data_z['bin_centers'], hist_data_z['densities'], 
                width=hist_data_z['bin_width']*0.9, alpha=0.6, color='coral', label='直方图')
        
        kde_result_z = KDEEstimator.estimate_density(dr_zscore)
        ax2.plot(kde_result_z['x'], kde_result_z['y'], 'b-', linewidth=2, label='KDE')
        
        ax2.axvline(x=0, color='gray', linestyle='--', alpha=0.7)
        ax2.axvline(x=-2, color='green', linestyle=':', alpha=0.5, label='±2σ')
        ax2.axvline(x=2, color='green', linestyle=':', alpha=0.5)
        ax2.set_xlabel('偏移率 (Z-score)')
        ax2.set_ylabel('密度')
        ax2.set_title('标准化偏移率分布 (Z-score)')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        
        # === 子图3: 时间序列图 ===
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
        print(f"  ✓ {stock_name}")
        return True
        
    except Exception as e:
        logger.error(f"绘制分布图失败 {ts_code}: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_visualization(config_path: str = "config/main.yaml", window: int = 20, 
                     price_type: str = "vwap", codes: list = None, limit: int = None):
    """
    运行个股分布可视化
    
    Args:
        config_path: 配置文件路径
        window: 移动均值窗口
        price_type: 价格类型（对于个股，推荐 vwap）
        codes: 指定股票代码列表（如果为空则处理所有股票）
        limit: 限制处理的股票数量（用于测试）
    """
    config = Config(config_path)
    
    data_dir = Path(config.get("data.raw_dir", "data/raw")) / "market" / "daily"
    figures_dir = Path("figures") / "distribution" / "stocks"
    ensure_dir(figures_dir)
    
    # 获取所有股票文件
    if not data_dir.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        return
    
    if codes:
        # 处理指定代码
        ts_codes = codes
    else:
        # 获取所有股票
        files = list(data_dir.glob("*.parquet"))
        ts_codes = [f.stem for f in files]
        
        if limit:
            ts_codes = ts_codes[:limit]
    
    price_type_name = PRICE_TYPE_NAMES.get(price_type, price_type)
    print(f"\n开始绘制 {len(ts_codes)} 只个股的分布图")
    print(f"价格基准: {price_type_name}")
    print(f"移动均值窗口: {window}日\n")
    
    success_count = 0
    for i, ts_code in enumerate(ts_codes, 1):
        print(f"[{i}/{len(ts_codes)}] {ts_code}...", end=" ")
        if plot_stock_distribution(ts_code, data_dir, figures_dir, window, price_type):
            success_count += 1
        else:
            print("  ✗ 失败")
            
    print(f"\n完成! 成功绘制 {success_count}/{len(ts_codes)} 只个股")
    print(f"图表已保存到: {figures_dir.absolute()}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='个股偏移率分布可视化')
    parser.add_argument('--window', type=int, default=20, help='移动均值窗口 (默认20)')
    parser.add_argument('--price-type', type=str, default='vwap',
                       choices=['close', 'vwap', 'typical', 'weighted_close', 'median', 'ohlc4'],
                       help='价格类型: vwap=成交额加权价(默认,推荐), typical=(H+L+C)/3, ohlc4=(O+H+L+C)/4')
    parser.add_argument('--codes', type=str, nargs='+', help='指定股票代码，如: 000001.SZ 600519.SH')
    parser.add_argument('--limit', type=int, help='限制处理数量（用于测试）')
    args = parser.parse_args()
    
    run_visualization(window=args.window, price_type=args.price_type, 
                     codes=args.codes, limit=args.limit)
