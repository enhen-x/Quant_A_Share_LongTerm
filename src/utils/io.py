# src/utils/io.py
"""数据 I/O 工具"""

import os
from pathlib import Path
from typing import Optional, Union, List

import pandas as pd


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


def save_parquet(
    df: pd.DataFrame, 
    path: Union[str, Path],
    partition_cols: Optional[List[str]] = None,
    **kwargs
) -> None:
    """
    保存 DataFrame 为 Parquet 格式
    
    Args:
        df: 要保存的数据
        path: 保存路径
        partition_cols: 分区列 (可选)
        **kwargs: 传递给 to_parquet 的其他参数
    """
    path = Path(path)
    ensure_dir(path.parent)
    
    if partition_cols:
        df.to_parquet(
            path, 
            partition_cols=partition_cols,
            engine='pyarrow',
            **kwargs
        )
    else:
        df.to_parquet(path, engine='pyarrow', **kwargs)


def load_parquet(
    path: Union[str, Path],
    columns: Optional[List[str]] = None,
    filters: Optional[List] = None,
    **kwargs
) -> pd.DataFrame:
    """
    读取 Parquet 文件
    
    Args:
        path: 文件路径
        columns: 要读取的列
        filters: 过滤条件 (PyArrow 格式)
        **kwargs: 传递给 read_parquet 的其他参数
        
    Returns:
        DataFrame
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    return pd.read_parquet(
        path, 
        columns=columns,
        filters=filters,
        engine='pyarrow',
        **kwargs
    )


def list_parquet_files(directory: Union[str, Path]) -> List[Path]:
    """
    列出目录下所有 Parquet 文件
    
    Args:
        directory: 目录路径
        
    Returns:
        Parquet 文件路径列表
    """
    directory = Path(directory)
    if not directory.exists():
        return []
    
    return sorted(directory.glob('*.parquet'))


def concat_parquet_files(
    directory: Union[str, Path],
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    合并目录下所有 Parquet 文件
    
    Args:
        directory: 目录路径
        columns: 要读取的列
        
    Returns:
        合并后的 DataFrame
    """
    files = list_parquet_files(directory)
    
    if not files:
        return pd.DataFrame()
    
    dfs = [load_parquet(f, columns=columns) for f in files]
    return pd.concat(dfs, ignore_index=True)
