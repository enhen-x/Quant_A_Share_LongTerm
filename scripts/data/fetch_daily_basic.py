"""
获取股票市值和估值数据

从Tushare获取daily_basic数据，包含：
- 总市值 (total_mv)
- 流通市值 (circ_mv)
- 换手率 (turnover_rate)
- 市盈率 (pe, pe_ttm)
- 市净率 (pb)
- 市销率 (ps, ps_ttm)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from tqdm import tqdm

from src.data_source import TushareSource
from src.utils.logger import get_logger
from src.utils.config import get_config
from src.utils.io import ensure_dir, save_parquet

logger = get_logger("fetch_daily_basic")

MAX_WORKERS = 30  # 降低并发数，避免超过Tushare限流


def fetch_daily_basic_by_date(ts_api, trade_date: str, max_retries: int = 3) -> pd.DataFrame:
    """
    获取指定日期的所有股票市值数据（带重试机制）
    
    Args:
        ts_api: Tushare API对象
        trade_date: 交易日期 (YYYYMMDD)
        max_retries: 最大重试次数
    
    Returns:
        DataFrame
    """
    for attempt in range(max_retries):
        try:
            df = ts_api.daily_basic(
                trade_date=trade_date,
                fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,'
                       'volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,'
                       'total_share,float_share,free_share,total_mv,circ_mv'
            )
            
            if df is not None and not df.empty:
                return df
            else:
                logger.warning(f"日期 {trade_date} 无数据")
                return pd.DataFrame()
                
        except Exception as e:
            if attempt < max_retries - 1:
                # 只记录到日志文件，不在终端显示
                logger.debug(f"获取 {trade_date} 数据失败 (尝试 {attempt + 1}/{max_retries}): {e}，2秒后重试...")
                time.sleep(2)
            else:
                # 最终失败也只记录到日志文件
                logger.debug(f"获取 {trade_date} 数据失败，已重试{max_retries}次: {e}")
                return pd.DataFrame()
    
    return pd.DataFrame()


def get_latest_trade_date():
    """
    获取最新交易日期
    
    Returns:
        str: 最新交易日期 (YYYYMMDD)
    """
    try:
        trade_cal = pd.read_parquet("data/meta/trade_cal.parquet")
        today = datetime.now().strftime('%Y%m%d')
        latest = trade_cal[
            (trade_cal['cal_date'] <= today) &
            (trade_cal['is_open'] == 1)
        ]['cal_date'].max()
        return latest
    except Exception as e:
        logger.warning(f"获取最新交易日失败: {e}，使用今天日期")
        return datetime.now().strftime('%Y%m%d')


def check_local_data_latest(file_path: Path, latest_trade_date: str) -> bool:
    """
    检查本地数据是否已是最新
    
    Args:
        file_path: 本地文件路径
        latest_trade_date: 最新交易日期
    
    Returns:
        bool: True表示已是最新，无需下载
    """
    if not file_path.exists():
        return False
    
    try:
        df = pd.read_parquet(file_path)
        if df.empty:
            return False
        
        local_latest = df['trade_date'].max()
        return local_latest >= latest_trade_date
    except Exception as e:
        logger.debug(f"检查本地文件失败: {e}")
        return False


def fetch_daily_basic_by_stock(ts_api, ts_code: str, start_date: str, end_date: str, max_retries: int = 3) -> pd.DataFrame:
    """
    获取指定股票的市值数据（带重试机制）
    
    Args:
        ts_api: Tushare API对象
        ts_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        max_retries: 最大重试次数
    
    Returns:
        DataFrame
    """
    for attempt in range(max_retries):
        try:
            df = ts_api.daily_basic(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,'
                       'volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,'
                       'total_share,float_share,free_share,total_mv,circ_mv'
            )
            
            if df is not None and not df.empty:
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            if attempt < max_retries - 1:
                # 只记录到日志文件，不在终端显示
                logger.debug(f"获取 {ts_code} 数据失败 (尝试 {attempt + 1}/{max_retries}): {e}，2秒后重试...")
                time.sleep(2)
            else:
                # 最终失败也只记录到日志文件
                logger.debug(f"获取 {ts_code} 数据失败，已重试{max_retries}次: {e}")
                return pd.DataFrame()
    
    return pd.DataFrame()


def get_trade_dates(start_date: str, end_date: str) -> list:
    """
    获取交易日期列表
    
    Args:
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
    
    Returns:
        交易日期列表
    """
    try:
        trade_cal = pd.read_parquet("data/meta/trade_cal.parquet")
        trade_cal = trade_cal[
            (trade_cal['cal_date'] >= start_date) &
            (trade_cal['cal_date'] <= end_date) &
            (trade_cal['is_open'] == 1)
        ]
        return trade_cal['cal_date'].tolist()
    except Exception as e:
        logger.error(f"获取交易日历失败: {e}")
        return []


def fetch_by_date_mode(start_date: str, end_date: str):
    """
    按日期模式获取数据（适合获取历史数据）
    
    Args:
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
    """
    logger.info("使用按日期模式获取数据")
    
    # 初始化Tushare
    config = get_config()
    token = config.get("tushare.token")
    ts_source = TushareSource(token=token)
    ts_api = ts_source.pro
    
    # 获取交易日期
    trade_dates = get_trade_dates(start_date, end_date)
    logger.info(f"共 {len(trade_dates)} 个交易日")
    
    if not trade_dates:
        logger.error("无交易日期数据")
        return
    
    # 创建输出目录
    output_dir = Path("data/meta/daily_basic")
    ensure_dir(output_dir)
    
    # 按日期获取数据
    all_data = []
    success_count = 0
    fail_count = 0
    
    with tqdm(total=len(trade_dates), desc="获取市值数据", unit="日") as pbar:
        for trade_date in trade_dates:
            df = fetch_daily_basic_by_date(ts_api, trade_date)
            
            if not df.empty:
                all_data.append(df)
                success_count += 1
            else:
                fail_count += 1
            
            pbar.set_postfix_str(f"{trade_date} | 成功:{success_count} 失败:{fail_count}")
            pbar.update(1)
    
        # 按日期保存（不生成合并文件，避免部分失败影响全部）
    if all_data:
        logger.info("按日期保存数据...")
        saved_count = 0
        for df in tqdm(all_data, desc="保存数据"):
            if not df.empty:
                trade_date = df['trade_date'].iloc[0]
                date_file = output_dir / "by_date" / f"{trade_date}.parquet"
                ensure_dir(date_file.parent)
                save_parquet(df, date_file)
                saved_count += 1
        
        logger.info(f"完成: 成功 {success_count} 日, 失败 {fail_count} 日, 已保存 {saved_count} 个文件")
        logger.info(f"数据保存在: {output_dir / 'by_date'}")
    else:
        logger.error("未获取到任何数据")


def fetch_by_stock_mode(start_date: str, end_date: str, force_update: bool = False):
    """
    按股票模式获取数据（适合增量更新，支持跳过已是最新的股票）
    
    Args:
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        force_update: 是否强制更新（忽略本地检查）
    """
    logger.info("使用按股票模式获取数据")
    
    # 获取最新交易日期
    latest_trade_date = get_latest_trade_date()
    logger.debug(f"最新交易日: {latest_trade_date}")
    
    # 初始化Tushare
    config = get_config()
    token = config.get("tushare.token")
    ts_source = TushareSource(token=token)
    ts_api = ts_source.pro
    
    # 获取股票列表
    try:
        stock_basic = pd.read_parquet("data/meta/stock_basic.parquet")
        stock_list = stock_basic['ts_code'].tolist()
        logger.info(f"共 {len(stock_list)} 只股票")
    except Exception as e:
        logger.error(f"读取股票列表失败: {e}")
        return
    
    # 创建输出目录
    output_dir = Path("data/meta/daily_basic")
    ensure_dir(output_dir)
    
    # 如果不是强制更新，先过滤掉已是最新的股票
    if not force_update:
        stocks_to_update = []
        for ts_code in stock_list:
            stock_file = output_dir / "by_stock" / f"{ts_code}.parquet"
            if not check_local_data_latest(stock_file, latest_trade_date):
                stocks_to_update.append(ts_code)
        
                skip_count = len(stock_list) - len(stocks_to_update)
        if skip_count > 0:
            logger.info(f"跳过 {skip_count} 只已是最新的股票，需要更新 {len(stocks_to_update)} 只")
        stock_list = stocks_to_update
    
    if not stock_list:
        logger.info("所有股票数据已是最新，无需更新")
        return
    
            # 并行获取数据（单独保存，不生成合并文件）
    success_count = 0
    fail_count = 0
    failed_stocks = []
    
    def _fetch_and_save_stock(ts_code):
        """获取并立即保存单个股票数据"""
        # 检查本地数据，如果有则增量更新
        stock_file = output_dir / "by_stock" / f"{ts_code}.parquet"
        actual_start_date = start_date
        
        if stock_file.exists():
            try:
                local_df = pd.read_parquet(stock_file)
                if not local_df.empty:
                    local_latest = local_df['trade_date'].max()
                    # 从本地最新日期的下一天开始
                    actual_start_date = (pd.to_datetime(local_latest, format='%Y%m%d') + pd.Timedelta(days=1)).strftime('%Y%m%d')
            except Exception as e:
                logger.debug(f"{ts_code} 读取本地文件失败: {e}")
        
        # 获取数据（修复缩进错误）
        df = fetch_daily_basic_by_stock(ts_api, ts_code, actual_start_date, end_date)
        
        # 如果返回空数据，可能是股票停牌或该期间无交易，不算失败
        if not df.empty:
            # 如果是增量更新，合并数据
            if stock_file.exists():
                try:
                    local_df = pd.read_parquet(stock_file)
                    df = pd.concat([local_df, df], ignore_index=True)
                    df = df.drop_duplicates(subset=['trade_date'], keep='last')
                    df = df.sort_values('trade_date')
                except Exception as e:
                    logger.debug(f"{ts_code} 合并本地数据失败: {e}")
            
                        # 立即保存
            ensure_dir(stock_file.parent)
            save_parquet(df, stock_file)
            return ts_code, True
        else:
            # 返回空数据，可能是停牌，也算成功（不需要更新）
            return ts_code, True
    
            
    with tqdm(total=len(stock_list), desc="获取市值数据", unit="只") as pbar:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(_fetch_and_save_stock, ts_code): ts_code
                for ts_code in stock_list
            }
            
            for future in as_completed(futures):
                ts_code = futures[future]
                try:
                    _, success = future.result()
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                        failed_stocks.append(ts_code)
                except Exception as e:
                    fail_count += 1
                    failed_stocks.append(ts_code)
                    logger.debug(f"{ts_code} 处理失败: {e}")
                
                pbar.set_postfix_str(f"{ts_code} | 成功:{success_count} 失败:{fail_count}")
                pbar.update(1)
    
                    # 数据已在获取时立即保存
    if fail_count == 0:
        print(f"\n✓ 全部完成: {success_count} 只股票")
    else:
        print(f"\n完成: 成功 {success_count} 只, 失败 {fail_count} 只")
        if len(failed_stocks) <= 10:
            logger.warning(f"失败的股票: {', '.join(failed_stocks)}")
        else:
            logger.warning(f"失败的股票: {len(failed_stocks)} 只（详见日志文件）")


def update_latest_data():
    """
    增量更新最新数据（只更新最近几天）
    """
    logger.info("增量更新最新数据")
    
    # 检查现有数据
    output_file = Path("data/meta/daily_basic/daily_basic_all.parquet")
    
    if output_file.exists():
        existing_df = pd.read_parquet(output_file)
        latest_date = existing_df['trade_date'].max()
        logger.info(f"现有数据最新日期: {latest_date}")
        
        # 从最新日期的下一天开始更新
        start_date = (datetime.strptime(latest_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
    else:
        logger.info("未找到现有数据，将获取全部历史数据")
        start_date = "20100101"
    
    end_date = datetime.now().strftime('%Y%m%d')
    
    logger.info(f"更新日期范围: {start_date} ~ {end_date}")
    
    # 使用按日期模式更新
    fetch_by_date_mode(start_date, end_date)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="获取股票市值和估值数据")
    parser.add_argument(
        "--mode",
        type=str,
        default="update",
        choices=["date", "stock", "update"],
        help="获取模式: date=按日期, stock=按股票, update=增量更新"
    )
    parser.add_argument(
        "--start_date",
        type=str,
        default="20100101",
        help="开始日期 (YYYYMMDD)"
    )
    parser.add_argument(
        "--end_date",
        type=str,
        default=datetime.now().strftime('%Y%m%d'),
        help="结束日期 (YYYYMMDD)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("获取股票市值和估值数据")
    print("=" * 80)
    print(f"模式: {args.mode}")
    print(f"日期范围: {args.start_date} ~ {args.end_date}")
    print("=" * 80)
    
    if args.mode == "date":
        fetch_by_date_mode(args.start_date, args.end_date)
    elif args.mode == "stock":
        fetch_by_stock_mode(args.start_date, args.end_date)
    elif args.mode == "update":
        update_latest_data()
    
    print("=" * 80)
    print("完成")
    print("=" * 80)


if __name__ == "__main__":
    main()