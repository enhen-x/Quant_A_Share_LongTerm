"""
测试基础设施

验证配置、日志、IO 工具是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.io import ensure_dir, file_exists


def test_config():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")
    config = get_config()

    # 测试嵌套配置
    tushare_token = config.get("tushare.token")
    print(f"Tushare Token: {tushare_token[:20]}..." if tushare_token else "Tushare Token: 未设置")

    deviation_window = config.get("deviation.window.size")
    print(f"偏移率窗口大小: {deviation_window}")

    grid_n_zones = config.get("grid.n_zones")
    print(f"网格数量: {grid_n_zones}")

    # 测试默认值
    non_exist = config.get("non.exist.key", "default_value")
    print(f"不存在的键: {non_exist}")


def test_logger():
    """测试日志系统"""
    print("\n=== 测试日志系统 ===")
    logger = get_logger("test", level="DEBUG")

    logger.debug("这是 DEBUG 级别日志")
    logger.info("这是 INFO 级别日志")
    logger.warning("这是 WARNING 级别日志")
    logger.error("这是 ERROR 级别日志")

    print("日志已输出到终端和 logs/test.log")


def test_io():
    """测试 IO 工具"""
    print("\n=== 测试 IO 工具 ===")

    # 测试目录创建
    test_dir = Path("data/test")
    ensure_dir(test_dir)
    print(f"创建目录: {test_dir}")

    # 测试文件检查
    config_file = Path("config/main.yaml")
    exists = file_exists(config_file)
    print(f"配置文件存在: {exists}")


if __name__ == "__main__":
    print("=" * 50)
    print("基础设施测试")
    print("=" * 50)

    try:
        test_config()
        test_logger()
        test_io()
        print("\n" + "=" * 50)
        print("所有测试通过！")
        print("=" * 50)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
