"""
数据缺口分析脚本

分析当前数据的完整性，识别缺失的数据类型
为后续的深度分析提供数据准备建议
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.utils.logger import get_logger
from src.data_source import DataHub

logger = get_logger("data_gap_analysis")


def analyze_existing_data():
    """分析现有数据"""
    print("=" * 80)
    print("数据缺口分析报告")
    print("=" * 80)
    
    # 1. 基础数据
    print("\n【1. 基础数据】")
    print("-" * 80)
    
    try:
        stock_basic = pd.read_parquet("data/meta/stock_basic.parquet")
        print(f"[OK] 股票基础信息: {len(stock_basic)} 只股票")
        print(f"  字段: {stock_basic.columns.tolist()}")
        print(f"  行业数量: {stock_basic['industry'].nunique()}")
        print(f"  地区数量: {stock_basic['area'].nunique()}")
    except Exception as e:
        print(f"[MISS] 股票基础信息缺失: {e}")
    
    try:
        trade_cal = pd.read_parquet("data/meta/trade_cal.parquet")
        print(f"[OK] 交易日历: {len(trade_cal)} 条记录")
    except Exception as e:
        print(f"[MISS] 交易日历缺失: {e}")
    
    # 2. 行情数据
    print("\n【2. 行情数据】")
    print("-" * 80)
    
    import os
    stock_files = os.listdir("data/raw/market/daily")
    print(f"[OK] 股票日线数据: {len(stock_files)} 只股票")
    
    # 抽样检查数据质量
    sample_file = "data/raw/market/daily/000001.SZ.parquet"
    sample_df = pd.read_parquet(sample_file)
    print(f"  样本数据时间范围: {sample_df['trade_date'].min()} ~ {sample_df['trade_date'].max()}")
    print(f"  样本数据字段: {sample_df.columns.tolist()}")
    
    index_files = os.listdir("data/raw/index")
    print(f"[OK] 指数数据: {len(index_files)} 个指数")
    print(f"  指数列表: {[f.replace('.parquet', '') for f in index_files]}")
    
    # 3. 偏移率数据
    print("\n【3. 偏移率数据】")
    print("-" * 80)
    
    try:
        stock_deviation = pd.read_parquet("data/processed/deviation/stock_deviation.parquet")
        print(f"[OK] 股票偏移率: {stock_deviation.shape[0]:,} 条记录")
        print(f"  覆盖股票数: {stock_deviation['ts_code'].nunique()}")
        print(f"  字段: {stock_deviation.columns.tolist()}")
    except Exception as e:
        print(f"[MISS] 股票偏移率缺失: {e}")
    
    try:
        index_deviation = pd.read_parquet("data/processed/deviation/index_deviation.parquet")
        print(f"[OK] 指数偏移率: {index_deviation.shape[0]:,} 条记录")
        print(f"  覆盖指数数: {index_deviation['ts_code'].nunique()}")
    except Exception as e:
        print(f"[MISS] 指数偏移率缺失: {e}")
    
    # 4. 分布统计数据
    print("\n【4. 分布统计数据】")
    print("-" * 80)
    
    try:
        dist_summary = pd.read_parquet("data/processed/distribution/distribution_summary.parquet")
        print(f"[OK] 分布统计汇总: {len(dist_summary)} 只股票")
        print(f"  字段: {dist_summary.columns.tolist()}")
        print(f"  分布类型统计:")
        print(dist_summary['dist_type'].value_counts().to_string())
    except Exception as e:
        print(f"[MISS] 分布统计汇总缺失: {e}")


def identify_missing_data():
    """识别缺失的数据"""
    print("\n" + "=" * 80)
    print("缺失数据识别")
    print("=" * 80)
    
    missing_data = []
    
    # 检查各类数据
    checks = {
        "股票财务数据": "data/meta/stock_financial.parquet",
        "股票市值数据": "data/meta/stock_market_cap.parquet",
        "行业分类数据": "data/meta/industry_classification.parquet",
        "行业指数数据": "data/raw/industry/",
        "股票换手率数据": "data/processed/turnover/",
        "股票Beta数据": "data/processed/beta/",
        "股票估值数据": "data/processed/valuation/",
        "相关性矩阵": "data/processed/correlation/",
        "行业偏移率": "data/processed/deviation/industry_deviation.parquet",
        "滚动分布统计": "data/processed/distribution/rolling_stats/",
        "历史网格配置": "data/processed/grid/",
        "历史仓位数据": "data/processed/position/",
    }
    
    print("\n【缺失数据清单】")
    print("-" * 80)
    
    for name, path in checks.items():
        full_path = Path(path)
        if not full_path.exists():
            missing_data.append(name)
            print(f"[MISS] {name}: {path}")
    
    if not missing_data:
        print("[OK] 所有数据完整")
    
    return missing_data


def generate_data_requirements():
    """生成数据需求清单"""
    print("\n" + "=" * 80)
    print("数据需求清单（按优先级排序）")
    print("=" * 80)
    
    requirements = [
        {
            "priority": "P0 - 必需（深度分析必备）",
            "items": [
                {
                    "name": "股票市值数据",
                    "source": "Tushare daily_basic",
                    "fields": ["total_mv", "circ_mv", "turnover_rate", "pe", "pb"],
                    "purpose": "市值维度分析、流动性分析、估值分析",
                    "api": "pro.daily_basic(ts_code='', trade_date='')"
                },
                {
                    "name": "行业分类数据",
                    "source": "Tushare stock_basic 或 申万行业分类",
                    "fields": ["industry_code", "industry_name", "industry_level"],
                    "purpose": "行业维度分析、行业对比",
                    "api": "pro.stock_basic() 或 pro.index_classify()"
                },
                {
                    "name": "行业指数数据",
                    "source": "Tushare 申万行业指数",
                    "fields": ["close", "pct_chg"],
                    "purpose": "行业相对偏移率计算、行业轮动分析",
                    "api": "pro.index_daily(ts_code='801010.SI')"  # 申万一级行业
                },
            ]
        },
        {
            "priority": "P1 - 重要（增强分析深度）",
            "items": [
                {
                    "name": "股票财务数据",
                    "source": "Tushare income/balancesheet/cashflow",
                    "fields": ["revenue", "net_profit", "roe", "debt_ratio"],
                    "purpose": "基本面特征分析、质量因子",
                    "api": "pro.income(ts_code='', period='')"
                },
                {
                    "name": "指数成分股",
                    "source": "Tushare index_weight",
                    "fields": ["index_code", "con_code", "weight"],
                    "purpose": "指数成分股分析、风格分析",
                    "api": "pro.index_weight(index_code='000300.SH')"
                },
                {
                    "name": "复权因子",
                    "source": "Tushare adj_factor",
                    "fields": ["adj_factor"],
                    "purpose": "准确计算收益率",
                    "api": "pro.adj_factor(ts_code='')"
                },
            ]
        },
        {
            "priority": "P2 - 可选（扩展分析）",
            "items": [
                {
                    "name": "资金流向数据",
                    "source": "Tushare moneyflow",
                    "fields": ["buy_sm_amount", "sell_sm_amount", "net_mf_amount"],
                    "purpose": "资金流向分析",
                    "api": "pro.moneyflow(ts_code='')"
                },
                {
                    "name": "龙虎榜数据",
                    "source": "Tushare top_list",
                    "fields": ["buy_amount", "sell_amount"],
                    "purpose": "主力行为分析",
                    "api": "pro.top_list(trade_date='')"
                },
                {
                    "name": "限售解禁",
                    "source": "Tushare share_float",
                    "fields": ["float_share", "float_ratio"],
                    "purpose": "流通盘变化分析",
                    "api": "pro.share_float(ts_code='')"
                },
            ]
        },
        {
            "priority": "P3 - 衍生数据（需计算）",
            "items": [
                {
                    "name": "滚动分布统计",
                    "source": "基于偏移率数据计算",
                    "fields": ["rolling_skew", "rolling_kurt", "rolling_jb"],
                    "purpose": "时间一致性分析、分布演化",
                    "calculation": "滚动窗口计算偏度/峰度"
                },
                {
                    "name": "股票Beta系数",
                    "source": "基于收益率数据计算",
                    "fields": ["beta", "alpha", "r_squared"],
                    "purpose": "市场敏感度分析",
                    "calculation": "回归计算 Beta"
                },
                {
                    "name": "相关性矩阵",
                    "source": "基于收益率数据计算",
                    "fields": ["correlation_matrix"],
                    "purpose": "股票间相关性分析、聚类",
                    "calculation": "滚动相关系数"
                },
                {
                    "name": "行业相对偏移率",
                    "source": "基于个股和行业偏移率计算",
                    "fields": ["relative_dr"],
                    "purpose": "行业内相对位置分析",
                    "calculation": "DR_stock - DR_industry"
                },
            ]
        }
    ]
    
    for req in requirements:
        print(f"\n【{req['priority']}】")
        print("-" * 80)
        for i, item in enumerate(req['items'], 1):
            print(f"\n{i}. {item['name']}")
            print(f"   数据源: {item['source']}")
            if 'fields' in item:
                print(f"   字段: {', '.join(item['fields'])}")
            if 'api' in item:
                print(f"   API: {item['api']}")
            if 'calculation' in item:
                print(f"   计算方法: {item['calculation']}")
            print(f"   用途: {item['purpose']}")


def generate_implementation_plan():
    """生成数据补充实施计划"""
    print("\n" + "=" * 80)
    print("数据补充实施计划")
    print("=" * 80)
    
    plan = [
        {
            "phase": "第一阶段：核心数据补充（1-2天）",
            "tasks": [
                "1. 获取股票市值数据（daily_basic）",
                "   - 实现 DataHub.get_daily_basic() 方法",
                "   - 保存到 data/meta/daily_basic/",
                "   - 字段：total_mv, circ_mv, turnover_rate, pe, pb, ps",
                "",
                "2. 完善行业分类数据",
                "   - 从 stock_basic 提取行业信息",
                "   - 或使用申万行业分类 API",
                "   - 保存到 data/meta/industry_classification.parquet",
                "",
                "3. 获取行业指数数据",
                "   - 申万一级行业指数（28个）",
                "   - 保存到 data/raw/industry/",
                "   - 计算行业偏移率",
            ]
        },
        {
            "phase": "第二阶段：衍生数据计算（2-3天）",
            "tasks": [
                "1. 计算滚动分布统计",
                "   - 实现滚动窗口偏度/峰度计算",
                "   - 窗口：60日、120日、252日",
                "   - 保存到 data/processed/distribution/rolling_stats/",
                "",
                "2. 计算股票Beta系数",
                "   - 相对沪深300、中证500",
                "   - 滚动窗口：60日、252日",
                "   - 保存到 data/processed/beta/",
                "",
                "3. 计算行业相对偏移率",
                "   - DR_relative = DR_stock - DR_industry",
                "   - 保存到 data/processed/deviation/relative_deviation.parquet",
                "",
                "4. 计算相关性矩阵",
                "   - 股票间收益率相关性",
                "   - 滚动窗口：60日",
                "   - 保存到 data/processed/correlation/",
            ]
        },
        {
            "phase": "第三阶段：增强数据（可选，3-5天）",
            "tasks": [
                "1. 获取财务数据",
                "   - 利润表、资产负债表、现金流量表",
                "   - 季度数据",
                "   - 保存到 data/meta/financial/",
                "",
                "2. 获取指数成分股",
                "   - 沪深300、中证500、创业板指",
                "   - 历史成分股变动",
                "   - 保存到 data/meta/index_weight/",
                "",
                "3. 获取复权因子",
                "   - 前复权因子",
                "   - 保存到 data/meta/adj_factor/",
            ]
        }
    ]
    
    for phase in plan:
        print(f"\n【{phase['phase']}】")
        print("-" * 80)
        for task in phase['tasks']:
            print(task)


def main():
    """主函数"""
    # 分析现有数据
    analyze_existing_data()
    
    # 识别缺失数据
    missing_data = identify_missing_data()
    
    # 生成数据需求清单
    generate_data_requirements()
    
    # 生成实施计划
    generate_implementation_plan()
    
    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)
    print("\n建议：")
    print("1. 优先补充 P0 级别的数据（市值、行业分类、行业指数）")
    print("2. 然后计算衍生数据（滚动统计、Beta、相关性）")
    print("3. 最后根据需要补充 P1/P2 级别的数据")
    print("\n下一步：运行 scripts/data/fetch_additional_data.py 开始数据补充")


if __name__ == "__main__":
    main()