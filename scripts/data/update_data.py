"""
数据更新脚本

批量更新股票和指数数据
使用进度条显示更新进度
"""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tqdm import tqdm

from src.data_source import DataHub
from src.utils.logger import get_logger
from src.utils.config import get_config

STOCK_MAX_WORKERS = 30


def _download_stock_daily(ts_code: str):
    datahub = DataHub()
    datahub.get_daily(ts_code, force_update=True)
    return ts_code


def _update_stocks_parallel(ts_codes, logger, desc):
    success_count = 0
    fail_count = 0
    failed_codes = []

    if not ts_codes:
        return success_count, fail_count, failed_codes

    max_workers = min(STOCK_MAX_WORKERS, len(ts_codes))
    with tqdm(total=len(ts_codes), desc=desc, unit="只",
              bar_format="{l_bar}{bar:30}{r_bar}", ncols=80) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_download_stock_daily, ts_code): ts_code
                for ts_code in ts_codes
            }
            for future in as_completed(futures):
                ts_code = futures[future]
                try:
                    future.result()
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    failed_codes.append(ts_code)
                    logger.error(f"更新 {ts_code} 失败: {e}")
                pbar.set_postfix_str(ts_code, refresh=True)
                pbar.update(1)

    return success_count, fail_count, failed_codes


def update_data():
    """更新所有数据"""
    logger = get_logger("update_data")

    print("=" * 60)
    print("开始数据更新")
    print("=" * 60)

    config = get_config()

    # 初始化数据中心
    datahub = DataHub()

    # 更新基础数据
    print("\n[1/5] 更新基础数据...")
    try:
        datahub.get_stock_basic(force_update=True)
        datahub.get_trade_cal(force_update=True)
        print("      ✓ 基础数据更新完成")
    except Exception as e:
        print(f"      ✗ 基础数据更新失败: {e}")
        logger.error(f"基础数据更新失败: {e}")
        return

    # 获取股票列表
    print("\n[2/5] 获取股票列表...")
    try:
        stock_list = datahub.get_stock_list(
            exclude_st=config.get("data.stock_pool.exclude_st", True),
            exclude_kcb=config.get("data.stock_pool.exclude_kcb", True),
            exclude_bj=config.get("data.stock_pool.exclude_bj", True),
            min_market_cap=config.get("data.stock_pool.min_market_cap"),
            min_list_days=config.get("data.stock_pool.min_list_days")
        )
        print(f"      ✓ 获取到 {len(stock_list)} 只股票")
    except Exception as e:
        print(f"      ✗ 获取股票列表失败: {e}")
        logger.error(f"获取股票列表失败: {e}")
        return

    # 获取指数列表
    print("\n[3/5] 获取指数列表...")
    index_list = datahub.get_index_list()
    print(f"      ✓ 获取到 {len(index_list)} 个指数")

    # 更新股票日线数据
    print("\n[4/5] 更新股票日线数据...")
    ts_codes = stock_list["ts_code"].tolist()
    success_count, fail_count, failed_codes = _update_stocks_parallel(
        ts_codes,
        logger,
        "      股票数据"
    )

    print(f"      ✓ 完成: 成功 {success_count} 只, 失败 {fail_count} 只")
    if failed_codes:
        logger.warning(f"失败的股票: {failed_codes[:20]}{'...' if len(failed_codes) > 20 else ''}")

    # 更新指数数据
    print("\n[5/5] 更新指数数据...")
    index_success = 0
    index_fail = 0

    with tqdm(index_list, desc="      指数数据", unit="个",
              bar_format="{l_bar}{bar:30}{r_bar}", ncols=80) as pbar:
        for index_code in pbar:
            pbar.set_postfix_str(index_code, refresh=True)
            try:
                datahub.get_index_daily(index_code, force_update=True)
                index_success += 1
            except Exception as e:
                index_fail += 1
                logger.error(f"更新 {index_code} 失败: {e}")

    print(f"      ✓ 完成: 成功 {index_success} 个, 失败 {index_fail} 个")

    print("\n" + "=" * 60)
    print("数据更新完成")
    print(f"  股票: {success_count}/{len(ts_codes)} 成功")
    print(f"  指数: {index_success}/{len(index_list)} 成功")
    print("=" * 60)


def update_stock_only(ts_codes: list):
    """只更新指定股票的数据"""
    logger = get_logger("update_data")

    print(f"更新 {len(ts_codes)} 只股票的数据...")

    success, fail, failed_codes = _update_stocks_parallel(
        ts_codes,
        logger,
        "股票数据"
    )

    print(f"\n完成: 成功 {success} 只, 失败 {fail} 只")
    if failed_codes:
        logger.warning(f"失败的股票: {failed_codes[:20]}{'...' if len(failed_codes) > 20 else ''}")


def update_indices_only():
    """只更新指数数据"""
    logger = get_logger("update_data")
    datahub = DataHub()

    index_list = datahub.get_index_list()
    print(f"更新 {len(index_list)} 个指数的数据...")

    success = 0
    fail = 0

    with tqdm(index_list, desc="指数数据", unit="个",
              bar_format="{l_bar}{bar:30}{r_bar}", ncols=80) as pbar:
        for index_code in pbar:
            pbar.set_postfix_str(index_code, refresh=True)
            try:
                datahub.get_index_daily(index_code, force_update=True)
                success += 1
            except Exception as e:
                fail += 1
                logger.error(f"{index_code} 更新失败: {e}")

    print(f"\n完成: 成功 {success} 个, 失败 {fail} 个")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据更新脚本")
    parser.add_argument("--type", type=str, default="all",
                       choices=["all", "basic", "stocks", "indices"],
                       help="更新类型: all=全部, basic=基础数据, stocks=股票, indices=指数")
    parser.add_argument("--codes", type=str, nargs="*",
                       help="指定股票代码，仅当 type=stocks 时有效")

    args = parser.parse_args()

    if args.type == "all":
        update_data()
    elif args.type == "basic":
        datahub = DataHub()
        datahub.get_stock_basic(force_update=True)
        datahub.get_trade_cal(force_update=True)
        print("基础数据更新完成")
    elif args.type == "stocks":
        if args.codes:
            update_stock_only(args.codes)
        else:
            update_data()
    elif args.type == "indices":
        update_indices_only()
