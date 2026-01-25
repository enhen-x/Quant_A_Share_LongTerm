"""
日志工具模块
提供统一的日志配置和管理
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    设置并返回一个配置好的logger
    
    Args:
        name: logger名称
        log_file: 日志文件路径，如果为None则不写入文件
        level: 日志级别
        console_output: 是否输出到控制台
        
    Returns:
        配置好的logger对象
    """
    # 创建logger
    logger = logging.getLogger(name)
    
    # 如果logger已经有handlers，说明已经配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 创建formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 添加控制台handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 添加文件handler
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 防止日志传播到root logger
    logger.propagate = False
    
    return logger


def get_default_log_file(name: str, log_dir: str = "logs") -> str:
    """
    获取默认的日志文件路径
    
    Args:
        name: logger名称
        log_dir: 日志目录
        
    Returns:
        日志文件路径
    """
    today = datetime.now().strftime("%Y%m%d")
    log_file = Path(log_dir) / f"{name}_{today}.log"
    return str(log_file)


class LoggerManager:
    """日志管理器，用于管理多个logger"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        log_file: Optional[str] = None,
        level: int = logging.INFO,
        console_output: bool = True
    ) -> logging.Logger:
        """
        获取或创建logger
        
        Args:
            name: logger名称
            log_file: 日志文件路径
            level: 日志级别
            console_output: 是否输出到控制台
            
        Returns:
            logger对象
        """
        if name not in cls._loggers:
            cls._loggers[name] = setup_logger(
                name=name,
                log_file=log_file,
                level=level,
                console_output=console_output
            )
        return cls._loggers[name]
    
    @classmethod
    def set_level(cls, name: str, level: int):
        """设置指定logger的日志级别"""
        if name in cls._loggers:
            cls._loggers[name].setLevel(level)
            for handler in cls._loggers[name].handlers:
                handler.setLevel(level)
    
    @classmethod
    def close_all(cls):
        """关闭所有logger的handlers"""
        for logger in cls._loggers.values():
            for handler in logger.handlers:
                handler.close()
        cls._loggers.clear()
