"""
IO 工具模块

提供文件读写、目录管理等通用 IO 功能
"""

import pandas as pd
from pathlib import Path
from typing import Union, Optional


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path 对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_parquet(path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    读取 Parquet 文件

    Args:
        path: 文件路径
        **kwargs: pandas.read_parquet 的其他参数

    Returns:
        DataFrame
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    return pd.read_parquet(path, **kwargs)


def write_parquet(
    df: pd.DataFrame,
    path: Union[str, Path],
    index: bool = False,
    **kwargs
) -> None:
    """
    写入 Parquet 文件

    Args:
        df: DataFrame
        path: 文件路径
        index: 是否保存索引
        **kwargs: DataFrame.to_parquet 的其他参数
    """
    path = Path(path)
    ensure_dir(path.parent)
    df.to_parquet(path, index=index, **kwargs)


# 别名函数，为了兼容性
save_parquet = write_parquet


def read_csv(path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    读取 CSV 文件

    Args:
        path: 文件路径
        **kwargs: pandas.read_csv 的其他参数

    Returns:
        DataFrame
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    return pd.read_csv(path, **kwargs)


def write_csv(
    df: pd.DataFrame,
    path: Union[str, Path],
    index: bool = False,
    **kwargs
) -> None:
    """
    写入 CSV 文件

    Args:
        df: DataFrame
        path: 文件路径
        index: 是否保存索引
        **kwargs: DataFrame.to_csv 的其他参数
    """
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=index, **kwargs)


def read_excel(path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    读取 Excel 文件

    Args:
        path: 文件路径
        **kwargs: pandas.read_excel 的其他参数

    Returns:
        DataFrame
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    return pd.read_excel(path, **kwargs)


def write_excel(
    df: pd.DataFrame,
    path: Union[str, Path],
    index: bool = False,
    **kwargs
) -> None:
    """
    写入 Excel 文件

    Args:
        df: DataFrame
        path: 文件路径
        index: 是否保存索引
        **kwargs: DataFrame.to_excel 的其他参数
    """
    path = Path(path)
    ensure_dir(path.parent)
    df.to_excel(path, index=index, **kwargs)


def file_exists(path: Union[str, Path]) -> bool:
    """
    检查文件是否存在

    Args:
        path: 文件路径

    Returns:
        文件是否存在
    """
    return Path(path).exists()


def list_files(
    dir_path: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> list:
    """
    列出目录下的文件

    Args:
        dir_path: 目录路径
        pattern: 文件匹配模式
        recursive: 是否递归

    Returns:
        文件路径列表
    """
    dir_path = Path(dir_path)
    if recursive:
        return list(dir_path.rglob(pattern))
    else:
        return list(dir_path.glob(pattern))
