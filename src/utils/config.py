# src/utils/config.py
"""配置文件加载工具"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


_config_cache: Optional[Dict[str, Any]] = None


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载 YAML 配置文件
    
    Args:
        config_path: 配置文件路径，默认为 config/main.yaml
        
    Returns:
        配置字典
    """
    global _config_cache
    
    if _config_cache is not None and config_path is None:
        return _config_cache
    
    if config_path is None:
        # 自动查找项目根目录的配置文件
        current = Path(__file__).resolve()
        project_root = current.parent.parent.parent  # src/utils/config.py -> project_root
        config_path = project_root / "config" / "main.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 处理相对路径
    project_root = config_path.parent.parent
    config['_project_root'] = str(project_root)
    
    if config_path is None:
        _config_cache = config
    
    return config


def get_config(key: str = None, default: Any = None) -> Any:
    """
    获取配置项
    
    Args:
        key: 配置键，支持点分格式如 'tushare.token'
        default: 默认值
        
    Returns:
        配置值
    """
    config = load_config()
    
    if key is None:
        return config
    
    keys = key.split('.')
    value = config
    
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default


def get_project_root() -> Path:
    """获取项目根目录"""
    config = load_config()
    return Path(config['_project_root'])


def get_data_path(data_type: str = 'raw') -> Path:
    """
    获取数据目录路径
    
    Args:
        data_type: 'raw', 'processed', 'meta'
        
    Returns:
        数据目录路径
    """
    config = load_config()
    root = Path(config['_project_root'])
    
    path_key = f'data_{data_type}'
    rel_path = config['paths'].get(path_key, f'data/{data_type}')
    
    return root / rel_path
