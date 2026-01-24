#!/usr/bin/env python
"""
偏移率计算脚本

批量计算股票、指数、行业的偏移率
结果保存到 data/processed/deviation/

用法:
    python scripts/analysis/calc_deviation.py                    # 计算所有
    python scripts/analysis/calc_deviation.py --type stock       # 只计算股票
    python scripts/analysis/calc_deviation.py --codes 600519.SH  # 计算指定代码
    python scripts/analysis/calc_deviation.py --window 60        # 使用60日窗口
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Optional, List, Tuple, Union

import pandas as pd
import numpy as np

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_config
from src.utils.io import read_parquet, write_parquet, ensure_dir, list_files
from src.deviation.calculator import DeviationCalculator, MultiWindowDeviationCalculator
from src.deviation.rolling_stats import RollingStats


logger = get_logger("scripts.calc_deviation")


def _silence_console_logger(target_logger: logging.Logger, level: int = logging.CRITICAL) -> None:
    for handler in target_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(level)


_silence_console_logger(logger)


def _default_workers() -> int:
    cpu_count = os.cpu_count() or 4
    return max(1, min(32, cpu_count))


def _build_executor(executor_type: str, max_workers: int):
    if executor_type == "process":
        return ProcessPoolExecutor(max_workers=max_workers)
    return ThreadPoolExecutor(max_workers=max_workers)


def calculate_price_series(df: pd.DataFrame, price_type: str = "close", data_type: str = "stock") -> Optional[pd.Series]:
    """
    根据指定的价格类型计算价格序列
    
    Args:
        df: 包含价格数据的 DataFrame
        price_type: 价格类型
            - 'close': 收盘价
            - 'vwap': 成交量加权平均价 (仅适用于个股数据)
            - 'typical': 典型价格 (high + low + close) / 3
            - 'weighted_close': 加权收盘价 (high + low + 2*close) / 4
            - 'median': 中间价 (high + low) / 2
            - 'ohlc4': 四价均价 (open + high + low + close) / 4
        data_type: 数据类型 ('stock', 'index', 'industry')
            
    Returns:
        价格序列
        
    Note:
        对于指数数据，VWAP 不适用（因为 amount/vol 算出的是成分股平均价格，
        不是指数的 VWAP），会自动使用 OHLC4 替代，更能体现全天价格水平。
    """
    # 对于指数数据，VWAP 不适用，使用 OHLC4 替代（更能体现全天价格水平）
    if price_type == "vwap" and data_type == "index":
        logger.info("指数数据不支持 VWAP（amount/vol 算出的是成分股均价），使用 OHLC4 替代")
        price_type = "ohlc4"
    
    if price_type == "close":
        if "close" not in df.columns:
            return None
        return df["close"]
    
    elif price_type == "vwap":
        # VWAP = 成交额 / 成交量 (仅适用于个股)
        # 注意：Tushare 个股数据中 amount 单位是千元，vol 单位是手
        # VWAP = amount * 1000 / (vol * 100) = amount * 10 / vol
        if "amount" in df.columns and "vol" in df.columns:
            # 避免除零
            vol = df["vol"].replace(0, np.nan)
            vwap = df["amount"] * 10 / vol  # 单位转换: 千元/手 -> 元/股
            # 对于成交量为0的情况，使用收盘价替代
            if "close" in df.columns:
                vwap = vwap.fillna(df["close"])
            return vwap
        else:
            logger.warning("缺少 amount 或 vol 列，无法计算 VWAP，使用 close 替代")
            return df.get("close")
    
    elif price_type == "typical":
        # 典型价格 = (high + low + close) / 3
        if all(col in df.columns for col in ["high", "low", "close"]):
            return (df["high"] + df["low"] + df["close"]) / 3
        else:
            logger.warning("缺少 high/low/close 列，无法计算 typical，使用 close 替代")
            return df.get("close")
    
    elif price_type == "weighted_close":
        # 加权收盘价 = (high + low + 2*close) / 4
        if all(col in df.columns for col in ["high", "low", "close"]):
            return (df["high"] + df["low"] + 2 * df["close"]) / 4
        else:
            logger.warning("缺少 high/low/close 列，无法计算 weighted_close，使用 close 替代")
            return df.get("close")
    
    elif price_type == "median":
        # 中间价 = (high + low) / 2
        if all(col in df.columns for col in ["high", "low"]):
            return (df["high"] + df["low"]) / 2
        else:
            logger.warning("缺少 high/low 列，无法计算 median，使用 close 替代")
            return df.get("close")
    
    elif price_type == "ohlc4":
        # 四价均价 = (open + high + low + close) / 4
        if all(col in df.columns for col in ["open", "high", "low", "close"]):
            return (df["open"] + df["high"] + df["low"] + df["close"]) / 4
        else:
            logger.warning("缺少 OHLC 列，无法计算 ohlc4，使用 close 替代")
            return df.get("close")
    
    else:
        logger.warning(f"未知的价格类型: {price_type}，使用 close")
        return df.get("close")


def get_available_stocks(raw_dir: Path) -> List[str]:
    """获取所有可用的股票代码"""
    daily_dir = raw_dir / "market" / "daily"
    if not daily_dir.exists():
        return []
    
    files = list_files(daily_dir, "*.parquet")
    ts_codes = [f.stem for f in files]
    return ts_codes


def get_available_indices(raw_dir: Path) -> List[str]:
    """获取所有可用的指数代码"""
    index_dir = raw_dir / "index"
    if not index_dir.exists():
        return []
    
    files = list_files(index_dir, "*.parquet")
    ts_codes = [f.stem for f in files]
    return ts_codes


def load_price_data(
    ts_code: str, 
    data_type: str, 
    raw_dir: Path
) -> Optional[pd.DataFrame]:
    """
    加载价格数据
    
    Args:
        ts_code: 代码
        data_type: 数据类型 ('stock', 'index')
        raw_dir: 原始数据目录
        
    Returns:
        DataFrame 或 None
    """
    if data_type == "stock":
        file_path = raw_dir / "market" / "daily" / f"{ts_code}.parquet"
    elif data_type == "index":
        file_path = raw_dir / "index" / f"{ts_code}.parquet"
    else:
        logger.error(f"未知的数据类型: {data_type}")
        return None
    
    if not file_path.exists():
        logger.warning(f"数据文件不存在: {file_path}")
        return None
    
    try:
        df = read_parquet(file_path)
        return df
    except Exception as e:
        logger.error(f"读取数据失败 {ts_code}: {e}")
        return None


def calculate_single_deviation(
    ts_code: str,
    data_type: str,
    raw_dir: Path,
    window: int = 252,
    window_type: str = "simple",
    multi_window: bool = True,
    method: str = "all",
    price_type: str = "close",
) -> Optional[pd.DataFrame]:
    """
    计算单个标的的偏移率
    
    Args:
        ts_code: 代码
        data_type: 数据类型
        raw_dir: 原始数据目录
        window: 窗口大小
        window_type: 窗口类型
        multi_window: 是否计算多窗口
        price_type: 价格类型 (close, vwap, typical, weighted_close, median, ohlc4)
        
    Returns:
        偏移率 DataFrame
    """
    # 加载数据
    df = load_price_data(ts_code, data_type, raw_dir)
    if df is None or df.empty:
        return None
    
    # 确保按日期排序
    if "trade_date" in df.columns:
        df = df.sort_values("trade_date").reset_index(drop=True)
        # 转换日期格式
        df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
        df = df.set_index("trade_date")
    
    # 根据价格类型计算价格序列
    prices = calculate_price_series(df, price_type)
    if prices is None or prices.empty:
        logger.warning(f"{ts_code} 无法计算 {price_type} 价格序列")
        return None
    
    try:
        if multi_window:
            # 多窗口计算
            calc = MultiWindowDeviationCalculator(
                windows=[20, 60, 120, 252],
                window_type=window_type,
            )
            multi_method = method
            if method == "percentile":
                multi_method = "all"
                logger.warning("多窗口不支持 percentile，已改为 all")
            result = calc.calculate(prices, method=multi_method)
        else:
            # 单窗口计算
            calc = DeviationCalculator(
                window=window,
                window_type=window_type,
            )
            result = calc.calculate(prices, method=method)
        
        # 添加代码列
        result["ts_code"] = ts_code
        result["data_type"] = data_type
        
        # 重置索引
        result = result.reset_index()
        if "index" in result.columns:
            result = result.rename(columns={"index": "trade_date"})
        
        return result
        
    except Exception as e:
        logger.error(f"计算偏移率失败 {ts_code}: {e}")
        return None


def calculate_batch_deviation(
    ts_codes: List[str],
    data_type: str,
    raw_dir: Path,
    output_dir: Path,
    window: int = 252,
    window_type: str = "simple",
    multi_window: bool = False,
    parallel_workers: int = 4,
    save_individual: bool = True,
    save_combined: bool = True,
    return_failed: bool = False,
    method: str = "zscore",
    price_type: str = "close",
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, List[str]]]:
    """
    批量计算偏移率
    
    Args:
        ts_codes: 代码列表
        data_type: 数据类型
        raw_dir: 原始数据目录
        output_dir: 输出目录
        window: 窗口大小
        window_type: 窗口类型
        multi_window: 是否多窗口
        parallel_workers: 并行工作线程数
        save_individual: 是否保存单个文件
        save_combined: 是否保存合并文件
        price_type: 价格类型 (close, vwap, typical 等)
        
    Returns:
        合并后的 DataFrame
    """
    logger.info(f"开始批量计算 {len(ts_codes)} 个 {data_type} 的偏移率 (价格类型: {price_type})")
    
    # 确保输出目录存在
    individual_dir = output_dir / data_type
    ensure_dir(individual_dir)
    
    results = []
    failed = []
    
    # 使用线程池并行计算，配合进度条
    from tqdm import tqdm
    
    with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
        futures = {
            executor.submit(
                calculate_single_deviation,
                ts_code,
                data_type,
                raw_dir,
                window,
                window_type,
                multi_window,
                method,
                price_type,
            ): ts_code
            for ts_code in ts_codes
        }
        
        with tqdm(total=len(ts_codes), desc=f"计算{data_type}偏移率", unit="个",
                  bar_format="{l_bar}{bar:30}{r_bar}", ncols=80) as pbar:
            for future in as_completed(futures):
                ts_code = futures[future]

                try:
                    result = future.result()
                    if result is not None and not result.empty:
                        results.append(result)
                        
                        # 保存单个文件
                        if save_individual:
                            output_file = individual_dir / f"{ts_code}.parquet"
                            write_parquet(result, output_file)
                    else:
                        failed.append(ts_code)
                        
                except Exception as e:
                    failed.append(ts_code)
                    logger.error(f"处理 {ts_code} 时出错: {e}")
                
                pbar.update(1)

    logger.info(f"完成计算，成功: {len(results)}，失败: {len(failed)}")

    if failed:
        logger.warning(f"失败的代码: {failed[:10]}{'...' if len(failed) > 10 else ''}")
    
    # 合并结果
    if results:
        combined_df = pd.concat(results, ignore_index=True)
        
        # 保存合并文件
        if save_combined:
            combined_file = output_dir / f"{data_type}_deviation.parquet"
            write_parquet(combined_df, combined_file)
            logger.info(f"合并文件已保存: {combined_file}")
        
        if return_failed:
            return combined_df, failed
        return combined_df
    else:
        empty_df = pd.DataFrame()
        if return_failed:
            return empty_df, failed
        return empty_df


def calculate_rolling_stats_batch(
    ts_codes: List[str],
    data_type: str,
    raw_dir: Path,
    output_dir: Path,
    window: int = 252,
    parallel_workers: int = 4,
    return_failed: bool = False,
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, List[str]]]:
    """
    批量计算滚动统计量
    
    Args:
        ts_codes: 代码列表
        data_type: 数据类型
        raw_dir: 原始数据目录
        output_dir: 输出目录
        window: 窗口大小
        parallel_workers: 并行工作线程数
        
    Returns:
        合并后的 DataFrame
    """
    logger.info(f"开始批量计算 {len(ts_codes)} 个 {data_type} 的滚动统计量")
    
    results = []
    failed = []

    def _calculate_single_rolling_stats(ts_code: str) -> Optional[pd.DataFrame]:
        df = load_price_data(ts_code, data_type, raw_dir)
        if df is None or df.empty:
            return None

        if "close" not in df.columns:
            return None

        if "trade_date" in df.columns:
            df = df.sort_values("trade_date").reset_index(drop=True)
            df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
            df = df.set_index("trade_date")

        prices = df["close"]
        stats_calculator = RollingStats(window=window)
        stats_df = stats_calculator.calculate_rolling_stats(
            prices, include_higher_moments=True
        )
        stats_df["ts_code"] = ts_code
        stats_df["data_type"] = data_type
        stats_df = stats_df.reset_index()
        if "index" in stats_df.columns:
            stats_df = stats_df.rename(columns={"index": "trade_date"})
        return stats_df

    from tqdm import tqdm

    with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
        futures = {
            executor.submit(_calculate_single_rolling_stats, ts_code): ts_code
            for ts_code in ts_codes
        }

        with tqdm(total=len(ts_codes), desc=f"计算{data_type}滚动统计", unit="个",
                  bar_format="{l_bar}{bar:30}{r_bar}", ncols=80) as pbar:
            for future in as_completed(futures):
                ts_code = futures[future]
                try:
                    stats_df = future.result()
                    if stats_df is not None and not stats_df.empty:
                        results.append(stats_df)
                    else:
                        failed.append(ts_code)
                except Exception as e:
                    failed.append(ts_code)
                    logger.error(f"计算滚动统计失败 {ts_code}: {e}")

                pbar.update(1)
    
    if results:
        combined_df = pd.concat(results, ignore_index=True)
        
        # 保存
        output_file = output_dir / f"{data_type}_rolling_stats.parquet"
        write_parquet(combined_df, output_file)
        logger.info(f"滚动统计文件已保存: {output_file}")
        
        if return_failed:
            return combined_df, failed
        return combined_df

    empty_df = pd.DataFrame()
    if return_failed:
        return empty_df, failed
    return empty_df


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="计算偏移率")
    parser.add_argument(
        "--type",
        type=str,
        choices=["stock", "index", "all"],
        default="all",
        help="计算类型",
    )
    parser.add_argument(
        "--codes",
        type=str,
        nargs="+",
        default=None,
        help="指定代码列表",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=252,
        help="计算窗口大小",
    )
    parser.add_argument(
        "--window-type",
        type=str,
        choices=["simple", "exponential", "adaptive"],
        default="simple",
        help="窗口类型",
    )
    parser.add_argument(
        "--multi-window",
        action="store_true",
        help="是否计算多窗口",
    )
    parser.add_argument(
        "--calc-stats",
        action="store_true",
        help="是否计算滚动统计量",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=_default_workers(),
        help="并行工作线程数",
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["raw", "zscore", "all"],
        default="zscore",
        help="计算方法: raw=原始偏移率, zscore=Z-score偏移率, all=全部(含百分位,较慢)",
    )
    parser.add_argument(
        "--price-type",
        type=str,
        choices=["close", "vwap", "typical", "weighted_close", "median", "ohlc4"],
        default="vwap",
        help="价格类型: close=收盘价, vwap=成交量加权均价, typical=(H+L+C)/3, weighted_close=(H+L+2C)/4, median=(H+L)/2, ohlc4=(O+H+L+C)/4",
    )
    parser.add_argument(
        "--no-individual",
        action="store_true",
        help="不保存单个文件",
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config = get_config()
    raw_dir = Path(config.get("paths.data_raw", "data/raw"))
    processed_dir = Path(config.get("paths.data_processed", "data/processed"))
    deviation_dir = processed_dir / "deviation"
    
    ensure_dir(deviation_dir)
    
    logger.info("=" * 60)
    logger.info("偏移率计算脚本")
    logger.info(f"计算类型: {args.type}")
    logger.info(f"价格类型: {args.price_type}")
    logger.info(f"窗口大小: {args.window}")
    logger.info(f"窗口类型: {args.window_type}")
    logger.info(f"多窗口: {args.multi_window}")
    logger.info("=" * 60)
    
    # 确定要计算的类型
    calc_types = []
    if args.type == "all":
        calc_types = ["stock", "index"]
    else:
        calc_types = [args.type]
    
    # 计算偏移率
    for data_type in calc_types:
        logger.info(f"\n{'='*40}")
        logger.info(f"计算 {data_type} 偏移率")
        logger.info(f"{'='*40}")
        
        # 获取代码列表
        if args.codes:
            ts_codes = args.codes
        elif data_type == "stock":
            ts_codes = get_available_stocks(raw_dir)
        elif data_type == "index":
            ts_codes = get_available_indices(raw_dir)
        else:
            ts_codes = []
        
        if not ts_codes:
            logger.warning(f"没有找到 {data_type} 数据")
            continue
        
        logger.info(f"找到 {len(ts_codes)} 个 {data_type}")
        
        # 计算偏移率
        _, failed = calculate_batch_deviation(
            ts_codes=ts_codes,
            data_type=data_type,
            raw_dir=raw_dir,
            output_dir=deviation_dir,
            window=args.window,
            window_type=args.window_type,
            multi_window=args.multi_window,
            parallel_workers=args.workers,
            save_individual=not args.no_individual,
            save_combined=True,
            return_failed=True,
            price_type=args.price_type,
        )

        print(f"{data_type} 偏移率失败 {len(failed)} 个: {failed}")
        
        # 计算滚动统计量
        if args.calc_stats:
            _, stats_failed = calculate_rolling_stats_batch(
                ts_codes=ts_codes,
                data_type=data_type,
                raw_dir=raw_dir,
                output_dir=deviation_dir,
                window=args.window,
                parallel_workers=args.workers,
                return_failed=True,
            )

            print(f"{data_type} 滚动统计失败 {len(stats_failed)} 个: {stats_failed}")
    
    logger.info("\n" + "=" * 60)
    logger.info("偏移率计算完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
