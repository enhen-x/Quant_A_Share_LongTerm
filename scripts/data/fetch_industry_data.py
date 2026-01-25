"""
获取行业数据脚本

功能：
1. 获取行业分类数据（申万一级、二级、三级）
2. 获取行业指数日线数据
3. 获取股票-行业映射关系
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_source import DataHub
from src.utils.logger import get_logger
from src.utils.io import ensure_dir, save_parquet
from tqdm import tqdm

logger = get_logger("fetch_industry_data")


# 申万一级行业指数代码（31个）
SW_L1_INDICES = [
    "801010.SI",  # 农林牧渔
    "801020.SI",  # 采掘
    "801030.SI",  # 化工
    "801040.SI",  # 钢铁
    "801050.SI",  # 有色金属
    "801080.SI",  # 电子
    "801110.SI",  # 家用电器
    "801120.SI",  # 食品饮料
    "801130.SI",  # 纺织服装
    "801140.SI",  # 轻工制造
    "801150.SI",  # 医药生物
    "801160.SI",  # 公用事业
    "801170.SI",  # 交通运输
    "801180.SI",  # 房地产
    "801200.SI",  # 商业贸易
    "801210.SI",  # 休闲服务
    "801230.SI",  # 综合
    "801710.SI",  # 建筑材料
    "801720.SI",  # 建筑装饰
    "801730.SI",  # 电气设备
    "801740.SI",  # 国防军工
    "801750.SI",  # 计算机
    "801760.SI",  # 传媒
    "801770.SI",  # 通信
    "801780.SI",  # 银行
    "801790.SI",  # 非银金融
    "801880.SI",  # 汽车
    "801890.SI",  # 机械设备
    "801950.SI",  # 煤炭
    "801960.SI",  # 石油石化
    "801970.SI",  # 环保
]


def check_data_date_range(file_path: Path, required_start: str, required_end: str) -> bool:
    """
    检查数据文件的日期范围是否满足要求
    
    Args:
        file_path: 数据文件路径
        required_start: 要求的开始日期 (YYYYMMDD)
        required_end: 要求的结束日期 (YYYYMMDD)
    
    Returns:
        True 表示数据已满足要求，无需更新；False 表示需要更新
    """
    if not file_path.exists():
        return False
    
    try:
        df = pd.read_parquet(file_path)
        
        if df.empty:
            return False
        
        # 检查是否有 trade_date 列
        if 'trade_date' not in df.columns:
            logger.debug(f"{file_path.name}: 无 trade_date 列，无法检查日期范围")
            return False
        
        # 获取数据的日期范围
        data_start = df['trade_date'].min()
        data_end = df['trade_date'].max()
        
        # 改进的检查逻辑：
        # 1. 数据的结束日期必须 >= 要求的结束日期（确保数据是最新的）
        # 2. 数据的开始日期应该接近要求的开始日期（允许一定误差，比如节假日）
        #    我们允许数据开始日期在要求日期的前后10天内
        
        if data_end >= required_end:
            # 检查开始日期是否在合理范围内
            start_diff = abs(int(data_start) - int(required_start))
            
            # 如果开始日期差异在10天以内（考虑到节假日等因素），认为数据是有效的
            if start_diff <= 10:
                logger.debug(f"{file_path.name}: 数据已是最新 ({data_start} ~ {data_end})")
                return True
            else:
                logger.debug(f"{file_path.name}: 开始日期差异过大 (现有: {data_start}, 需要: {required_start})")
                return False
        else:
            logger.debug(f"{file_path.name}: 需要更新 (现有: {data_start}~{data_end}, 需要: {required_start}~{required_end})")
            return False
            
    except Exception as e:
        logger.debug(f"{file_path.name}: 检查失败 - {e}")
        return False


def get_latest_trade_date() -> str:
    """获取最新交易日期"""
    from datetime import datetime, timedelta
    
    # 简单实现：返回今天或昨天（如果是周末则返回上周五）
    today = datetime.now()
    
    # 如果是周六，返回周五
    if today.weekday() == 5:
        today = today - timedelta(days=1)
    # 如果是周日，返回周五
    elif today.weekday() == 6:
        today = today - timedelta(days=2)
    
    return today.strftime('%Y%m%d')


def fetch_industry_classification():
    """获取行业分类数据"""
    logger.info("开始获取行业分类数据...")
    
    datahub = DataHub()
    datahub.init_source()  # 确保初始化数据源
    
    try:
        # 获取申万2021版行业分类（31个一级行业）
        df = datahub.source.pro.index_classify(
            level='L1',      # 一级行业
            src='SW2021'     # 申万2021版
        )
        
        if df is not None and not df.empty:
            output_path = project_root / "data" / "meta" / "industry_classification.parquet"
            ensure_dir(output_path.parent)
            save_parquet(df, output_path)
            logger.info(f"✓ 行业分类数据已保存: {output_path}")
            logger.info(f"  共 {len(df)} 个行业")
            return df
        else:
            logger.warning("未获取到行业分类数据")
            return None
            
    except Exception as e:
        logger.error(f"获取行业分类数据失败: {e}")
        return None


def fetch_stock_industry_mapping(fetch_detailed: bool = False):
    """
    获取股票-行业映射关系
    
    Args:
        fetch_detailed: 是否获取详细映射（遍历所有行业指数，耗时较长）
    """
    logger.info("开始获取股票-行业映射...")
    
    datahub = DataHub()
    datahub.init_source()  # 确保初始化数据源
    
    # 方法1: 从所有行业指数获取成分股（可选，耗时较长）
    if fetch_detailed:
        try:
            logger.info("方法1: 从申万行业指数获取成分股（耗时较长）...")
            all_members = []
            
            # 遍历所有申万一级行业指数
            for index_code in SW_L1_INDICES:
                try:
                    df = datahub.source.pro.index_member(
                        index_code=index_code,
                        is_new='1'  # 只获取最新成分
                    )
                    if df is not None and not df.empty:
                        all_members.append(df)
                except Exception as e:
                    logger.debug(f"获取 {index_code} 成分股失败: {e}")
                    continue
            
            if all_members:
                df_all = pd.concat(all_members, ignore_index=True)
                output_path = project_root / "data" / "meta" / "stock_industry_mapping_detailed.parquet"
                ensure_dir(output_path.parent)
                save_parquet(df_all, output_path)
                logger.info(f"✓ 详细股票-行业映射已保存: {output_path}")
                logger.info(f"  共 {len(df_all)} 条映射记录")
        except Exception as e:
            logger.warning(f"方法1失败: {e}")
    else:
        logger.info("跳过方法1（详细映射），如需获取请使用 --detailed 参数")
    
    # 方法2: 使用 stock_basic 获取行业信息（主要方法，快速）
    try:
        logger.info("方法2: 从 stock_basic 获取行业分类...")
        stock_basic = datahub.get_stock_basic()
        
        if stock_basic is not None and not stock_basic.empty and 'industry' in stock_basic.columns:
            output_path = project_root / "data" / "meta" / "stock_industry_mapping.parquet"
            ensure_dir(output_path.parent)
            save_parquet(stock_basic[['ts_code', 'name', 'industry']], output_path)
            logger.info(f"✓ 股票-行业映射已保存: {output_path}")
            logger.info(f"  共 {len(stock_basic)} 只股票")
            return stock_basic[['ts_code', 'name', 'industry']]
        else:
            logger.warning("未获取到股票行业信息")
            return None
    except Exception as e:
        logger.error(f"方法2失败: {e}")
        return None


def fetch_industry_indices(
    index_codes: List[str],
    start_date: str,
    end_date: str,
    max_retries: int = 3,
    retry_delay: int = 2,
    force_update: bool = False
):
    """
    获取行业指数日线数据（带重试机制和日期检查）
    
    Args:
        index_codes: 指数代码列表
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        force_update: 是否强制更新（忽略日期检查）
    """
    import time
    
    logger.info(f"开始获取 {len(index_codes)} 个行业指数数据...")
    logger.info(f"日期范围: {start_date} ~ {end_date}")
    
    datahub = DataHub()
    datahub.init_source()  # 确保初始化数据源
    
    output_dir = project_root / "data" / "raw" / "industry"
    ensure_dir(output_dir)
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    failed_codes = []
    
    with tqdm(index_codes, desc="行业指数", unit="个",
              bar_format="{l_bar}{bar:30}{r_bar}", ncols=80) as pbar:
        for index_code in pbar:
            pbar.set_postfix_str(index_code, refresh=True)
            
            # 检查是否需要更新
            output_path = output_dir / f"{index_code.replace('.', '_')}.parquet"
            
            if not force_update and check_data_date_range(output_path, start_date, end_date):
                skip_count += 1
                logger.debug(f"{index_code}: 数据已是最新，跳过")
                continue
            
            # 重试逻辑
            success = False
            for attempt in range(max_retries):
                try:
                    # 使用 sw_daily API 获取申万行业指数日线数据
                    # 注意：这需要 5000 积分权限
                    df = datahub.source.pro.sw_daily(
                        ts_code=index_code,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if df is not None and not df.empty:
                        # 保存到文件
                        save_parquet(df, output_path)
                        success_count += 1
                        logger.debug(f"{index_code}: 获取 {len(df)} 条记录")
                        success = True
                        break  # 成功后跳出重试循环
                    else:
                        if attempt < max_retries - 1:
                            logger.debug(f"{index_code}: 未获取到数据，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                        else:
                            logger.warning(f"{index_code}: 未获取到数据（可能需要更高积分权限）")
                        
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.debug(f"{index_code} 获取失败: {e}，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"{index_code} 获取失败（已重试{max_retries}次）: {e}")
            
            # 如果所有重试都失败
            if not success:
                fail_count += 1
                failed_codes.append(index_code)
    
    logger.info(f"✓ 行业指数数据获取完成")
    logger.info(f"  成功: {success_count} 个")
    logger.info(f"  跳过: {skip_count} 个（已是最新）")
    logger.info(f"  失败: {fail_count} 个")
    
    if failed_codes:
        logger.warning(f"  失败的指数: {failed_codes}")
    
    return success_count, fail_count, failed_codes


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="获取行业数据")
    parser.add_argument(
        "--task",
        type=str,
        default="all",
        choices=["all", "classification", "mapping", "indices"],
        help="任务类型: all=全部, classification=行业分类, mapping=股票映射, indices=指数数据"
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
    parser.add_argument(
        "--indices",
        type=str,
        nargs="*",
        help="指定行业指数代码（可选，默认使用申万一级31个行业）"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制更新，忽略日期检查"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="获取详细的股票-行业映射（遍历所有行业指数，耗时较长）"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("行业数据获取工具")
    print("=" * 80)
    print(f"任务: {args.task}")
    print(f"日期范围: {args.start_date} ~ {args.end_date}")
    if args.force:
        print("模式: 强制更新")
    if args.detailed:
        print("模式: 详细映射")
    print("=" * 80)
    
    # 1. 获取行业分类
    if args.task in ["all", "classification"]:
        print("\n[1/3] 获取行业分类...")
        print("-" * 80)
        fetch_industry_classification()
    
    # 2. 获取股票-行业映射
    if args.task in ["all", "mapping"]:
        print("\n[2/3] 获取股票-行业映射...")
        print("-" * 80)
        fetch_stock_industry_mapping(fetch_detailed=args.detailed)
    
    # 3. 获取行业指数数据
    if args.task in ["all", "indices"]:
        print("\n[3/3] 获取行业指数数据...")
        print("-" * 80)
        
        # 使用指定的指数代码或默认的申万一级行业指数
        index_codes = args.indices if args.indices else SW_L1_INDICES
        
        fetch_industry_indices(
            index_codes=index_codes,
            start_date=args.start_date,
            end_date=args.end_date,
            force_update=args.force
        )
    
    print("\n" + "=" * 80)
    print("行业数据获取完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
