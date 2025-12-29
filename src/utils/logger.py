# src/utils/logger.py
"""日志配置工具"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from .config import load_config, get_project_root


_loggers = {}


def setup_logger(
    name: str = 'quant_longterm',
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    设置日志器
    
    Args:
        name: 日志器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径 (None 则使用默认路径)
        
    Returns:
        logging.Logger 实例
    """
    if name in _loggers:
        return _loggers[name]
    
    config = load_config()
    log_config = config.get('logging', {})
    
    # 日志级别
    if level is None:
        level = log_config.get('level', 'INFO')
    level = getattr(logging, level.upper(), logging.INFO)
    
    # 日志格式
    log_format = log_config.get(
        'format', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    formatter = logging.Formatter(log_format)
    
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # 清除已有处理器
    
    # 控制台输出
    if log_config.get('console_enabled', True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件输出
    if log_config.get('file_enabled', True):
        if log_file is None:
            log_dir = get_project_root() / config['paths'].get('logs', 'logs')
            log_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = log_dir / f'{name}_{today}.log'
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger


def get_logger(name: str = 'quant_longterm') -> logging.Logger:
    """
    获取日志器 (如不存在则创建)
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger 实例
    """
    if name not in _loggers:
        return setup_logger(name)
    return _loggers[name]
