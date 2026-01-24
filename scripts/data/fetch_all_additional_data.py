"""
一键获取所有补充数据

按优先级顺序执行：
1. P0数据：市值数据、行业分类、行业指数
2. P1数据：财务数据、指数成分股（可选）
"""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger("fetch_all_additional_data")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="一键获取所有补充数据")
    parser.add_argument(
        "--priority",
        type=str,
        default="P0",
        choices=["P0", "P1", "all"],
        help="优先级: P0=必需数据, P1=重要数据, all=全部"
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
    print("一键获取所有补充数据")
    print("=" * 80)
    print(f"优先级: {args.priority}")
    print(f"日期范围: {args.start_date} ~ {args.end_date}")
    print("=" * 80)
    
    # P0数据：必需
    if args.priority in ["P0", "all"]:
        print("\n" + "=" * 80)
        print("【P0 - 必需数据】")
        print("=" * 80)
        
        # 1. 市值数据（使用增量更新模式，自动跳过已是最新的股票）
        print("\n[1/3] 获取市值和估值数据...")
        print("-" * 80)
        try:
            import subprocess
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/data/fetch_daily_basic.py",
                    "--mode", "stock",
                    "--start_date", args.start_date,
                    "--end_date", args.end_date
                ],
                check=True,
                capture_output=False
            )
            print("[OK] 市值数据获取完成")
        except Exception as e:
            print(f"[FAIL] 市值数据获取失败: {e}")
            logger.error(f"市值数据获取失败: {e}")
        
        # 2. 行业数据
        print("\n[2/3] 获取行业分类和行业指数...")
        print("-" * 80)
        try:
            import subprocess
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/data/fetch_industry_data.py",
                    "--task", "all",
                    "--start_date", args.start_date,
                    "--end_date", args.end_date
                ],
                check=True,
                capture_output=False
            )
            print("✓ 行业数据获取完成")
        except Exception as e:
            print(f"✗ 行业数据获取失败: {e}")
            logger.error(f"行业数据获取失败: {e}")
        
        # 3. 数据验证
        print("\n[3/3] 验证数据完整性...")
        print("-" * 80)
        validate_p0_data()
    
    # P1数据：重要（可选）
    if args.priority in ["P1", "all"]:
        print("\n" + "=" * 80)
        print("【P1 - 重要数据（可选）】")
        print("=" * 80)
        print("提示: P1数据需要Tushare高级权限，如果没有权限可以跳过")
        
        user_input = input("是否继续获取P1数据？(y/n): ")
        if user_input.lower() == 'y':
            # TODO: 实现P1数据获取
            print("P1数据获取功能待实现...")
        else:
            print("跳过P1数据获取")
    
    print("\n" + "=" * 80)
    print("所有数据获取完成")
    print("=" * 80)
    print("\n下一步建议：")
    print("1. 运行数据验证: python scripts/research/data_gap_analysis.py")
    print("2. 计算衍生数据: python scripts/calculation/calc_rolling_stats.py")
    print("3. 开始深度分析: python scripts/research/industry_analysis.py")


def validate_p0_data():
    """验证P0数据完整性"""
    import os
    from pathlib import Path
    
    checks = {
        "市值数据目录": "data/meta/daily_basic/by_stock",
        "行业分类": "data/meta/industry_classification.parquet",
        "行业映射": "data/meta/stock_industry_mapping.parquet",
        "行业指数目录": "data/raw/industry",
    }
    
    all_ok = True
    for name, path in checks.items():
        if os.path.exists(path):
            print(f"✓ {name}: {path}")
        else:
            print(f"✗ {name}: {path} (缺失)")
            all_ok = False
    
    if all_ok:
        print("\n✓ P0数据完整")
    else:
        print("\n✗ 部分P0数据缺失，请检查日志")
    
    return all_ok


if __name__ == "__main__":
    main()