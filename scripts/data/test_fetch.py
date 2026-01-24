"""
测试数据获取功能

在正式获取大量数据前，先测试API是否正常
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.data_source import TushareSource
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("test_fetch")


def test_daily_basic():
    """测试获取市值数据"""
    print("\n" + "=" * 80)
    print("测试获取市值数据 (daily_basic)")
    print("=" * 80)
    
    try:
        config = get_config()
        token = config.get("tushare.token")
        ts_source = TushareSource(token=token)
        ts_api = ts_source.pro
        
        # 测试获取单只股票的数据
        test_code = "000001.SZ"  # 平安银行
        print(f"\n测试股票: {test_code}")
        
        df = ts_api.daily_basic(
            ts_code=test_code,
            start_date='20240101',
            end_date='20240131',
            fields='ts_code,trade_date,close,turnover_rate,pe,pb,ps,total_mv,circ_mv'
        )
        
        if df is not None and not df.empty:
            print(f"[OK] 成功获取 {len(df)} 条记录")
            print("\n数据样本:")
            print(df.head())
            print("\n字段列表:")
            print(df.columns.tolist())
            return True
        else:
            print("[FAIL] 未获取到数据")
            return False
            
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        logger.error(f"测试daily_basic失败: {e}")
        return False


def test_industry_index():
    """测试获取行业指数"""
    print("\n" + "=" * 80)
    print("测试获取行业指数")
    print("=" * 80)
    
    try:
        config = get_config()
        token = config.get("tushare.token")
        ts_source = TushareSource(token=token)
        ts_api = ts_source.pro
        
        # 测试获取沪深300指数
        test_index = "000300.SH"  # 沪深300
        print(f"\n测试指数: {test_index} (沪深300)")
        
        df = ts_api.index_daily(
            ts_code=test_index,
            start_date='20240101',
            end_date='20240131'
        )
        
        if df is not None and not df.empty:
            print(f"[OK] 成功获取 {len(df)} 条记录")
            print("\n数据样本:")
            print(df.head())
            return True
        else:
            print("[FAIL] 未获取到数据")
            return False
            
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        logger.error(f"测试行业指数失败: {e}")
        return False


def test_stock_basic():
    """测试读取股票基础信息"""
    print("\n" + "=" * 80)
    print("测试读取股票基础信息")
    print("=" * 80)
    
    try:
        stock_basic = pd.read_parquet("data/meta/stock_basic.parquet")
        print(f"[OK] 成功读取 {len(stock_basic)} 只股票")
        print("\n字段列表:")
        print(stock_basic.columns.tolist())
        print("\n行业统计:")
        print(stock_basic['industry'].value_counts().head(10))
        return True
    except Exception as e:
        print(f"[FAIL] 读取失败: {e}")
        return False


def test_trade_calendar():
    """测试读取交易日历"""
    print("\n" + "=" * 80)
    print("测试读取交易日历")
    print("=" * 80)
    
    try:
        trade_cal = pd.read_parquet("data/meta/trade_cal.parquet")
        print(f"[OK] 成功读取 {len(trade_cal)} 条记录")
        
        # 统计2024年的交易日
        trade_days_2024 = trade_cal[
            (trade_cal['cal_date'] >= '20240101') &
            (trade_cal['cal_date'] <= '20241231') &
            (trade_cal['is_open'] == 1)
        ]
        print(f"\n2024年交易日数量: {len(trade_days_2024)}")
        return True
    except Exception as e:
        print(f"[FAIL] 读取失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("数据获取功能测试")
    print("=" * 80)
    print("\n说明: 在正式获取大量数据前，先测试API是否正常工作")
    print("=" * 80)
    
    results = {}
    
    # 测试基础数据读取
    results['股票基础信息'] = test_stock_basic()
    results['交易日历'] = test_trade_calendar()
    
    # 测试API功能
    results['市值数据API'] = test_daily_basic()
    results['行业指数API'] = test_industry_index()
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in results.items():
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("[OK] 所有测试通过，可以开始获取数据")
        print("\n下一步:")
        print("1. 获取市值数据: python scripts/data/fetch_daily_basic.py --mode update")
        print("2. 获取行业数据: python scripts/data/fetch_industry_data.py --task all")
        print("3. 一键获取全部: python scripts/data/fetch_all_additional_data.py --priority P0")
    else:
        print("[FAIL] 部分测试失败，请检查配置和网络连接")
        print("\n常见问题:")
        print("1. 检查 config/main.yaml 中的 Tushare Token 是否正确")
        print("2. 检查网络连接是否正常")
        print("3. 检查 Tushare 积分是否足够")
    print("=" * 80)


if __name__ == "__main__":
    main()