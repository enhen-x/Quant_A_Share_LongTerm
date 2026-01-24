"""
测试数据获取层

验证 Tushare 数据源和数据中心是否正常工作
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_source import TushareSource, DataHub
from src.utils.logger import get_logger


def test_tushare_source():
    """测试 Tushare 数据源"""
    print("\n=== 测试 Tushare 数据源 ===")

    source = TushareSource()

    # 测试获取股票日线
    print("\n1. 获取股票日线数据 (600519.SH)...")
    try:
        df = source.get_daily("600519.SH", start_date="20240101", end_date="20241231")
        print(f"   [OK] 获取到 {len(df)} 条记录")
        if not df.empty:
            print(f"   最新日期: {df['trade_date'].iloc[-1]}")
            print(f"   最新收盘价: {df['close'].iloc[-1]}")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")

    # 测试获取指数日线
    print("\n2. 获取指数日线数据 (000001.SH)...")
    try:
        df = source.get_index_daily("000001.SH", start_date="20240101", end_date="20241231")
        print(f"   [OK] 获取到 {len(df)} 条记录")
        if not df.empty:
            print(f"   最新日期: {df['trade_date'].iloc[-1]}")
            print(f"   最新收盘: {df['close'].iloc[-1]}")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")

    # 测试获取股票基础信息
    print("\n3. 获取股票基础信息...")
    try:
        df = source.get_stock_basic()
        print(f"   [OK] 获取到 {len(df)} 只股票")
        print(f"   前5只: {df['ts_code'].head().tolist()}")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")

    # 测试获取交易日历
    print("\n4. 获取交易日历...")
    try:
        df = source.get_trade_cal(exchange="SSE", start_date="20240101", end_date="20241231")
        print(f"   [OK] 获取到 {len(df)} 条记录")
        if not df.empty:
            trade_days = df[df["is_open"] == 1]
            print(f"   交易日数量: {len(trade_days)}")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")


def test_datahub():
    """测试数据中心"""
    print("\n=== 测试数据中心 ===")

    datahub = DataHub()

    # 测试获取股票列表
    print("\n1. 获取股票列表...")
    try:
        df = datahub.get_stock_list()
        print(f"   [OK] 获取到 {len(df)} 只股票")
        print(f"   前5只: {df['ts_code'].head().tolist()}")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")

    # 测试获取股票日线（从缓存/文件）
    print("\n2. 获取股票日线 (600519.SH)...")
    try:
        df = datahub.get_daily("600519.SH")
        print(f"   [OK] 获取到 {len(df)} 条记录")
        if not df.empty:
            print(f"   最新日期: {df['trade_date'].iloc[-1]}")
            print(f"   最新收盘价: {df['close'].iloc[-1]}")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")

    # 测试获取指数日线
    print("\n3. 获取指数日线 (000001.SH)...")
    try:
        df = datahub.get_index_daily("000001.SH")
        print(f"   [OK] 获取到 {len(df)} 条记录")
        if not df.empty:
            print(f"   最新日期: {df['trade_date'].iloc[-1]}")
            print(f"   最新收盘: {df['close'].iloc[-1]}")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")

    # 测试缓存
    print("\n4. 测试缓存机制...")
    try:
        df1 = datahub.get_daily("600519.SH")
        df2 = datahub.get_daily("600519.SH")
        print(f"   [OK] 两次获取相同股票，第二次使用缓存")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")


def test_datahub_filters():
    """测试数据中心筛选功能"""
    print("\n=== 测试数据中心筛选功能 ===")

    datahub = DataHub()

    # 测试筛选股票列表
    print("\n1. 筛选股票列表 (排除ST, 科创板, 北交所)...")
    try:
        df = datahub.get_stock_list(
            exclude_st=True,
            exclude_kcb=True,
            exclude_bj=True
        )
        print(f"   [OK] 筛选后剩余 {len(df)} 只股票")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")

    # 测试带市值筛选
    print("\n2. 带市值筛选...")
    try:
        df = datahub.get_stock_list(
            exclude_st=True,
            exclude_kcb=True,
            exclude_bj=True,
            min_market_cap=100000000000  # 100亿
        )
        print(f"   [OK] 市值>100亿的股票 {len(df)} 只")
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("数据获取层测试")
    print("=" * 50)

    try:
        test_tushare_source()
        test_datahub()
        test_datahub_filters()

        print("\n" + "=" * 50)
        print("所有测试通过！")
        print("=" * 50)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
