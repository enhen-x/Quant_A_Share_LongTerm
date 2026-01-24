"""
日志系统

提供统一的日志记录功能，支持文件日志和终端日志
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


class Logger:
    """日志管理类"""

    _loggers: dict = {}

    @classmethod
    def get_logger(
        cls,
        name: str = "quant",
        log_file: Optional[str] = None,
        level: str = "INFO",
        fmt: Optional[str] = None
    ) -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 日志名称
            log_file: 日志文件路径，默认为 logs/{name}.log
            level: 日志级别
            fmt: 日志格式

        Returns:
            Logger 实例
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))

        if not logger.handlers:
            if fmt is None:
                fmt = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"

            formatter = logging.Formatter(fmt)

            console_handler = logging.StreamHandler(sys.stdout)
            console_level = logging.ERROR if name == "tushare" else logging.INFO
            console_handler.setLevel(console_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            if log_file is None:
                log_dir = Path(__file__).parent.parent.parent / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = str(log_dir / f"{name}.log")
            else:
                log_file = str(log_file)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8"
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        cls._loggers[name] = logger
        return logger


def get_logger(name: str = "quant", log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """
    获取日志记录器的便捷函数

    Args:
        name: 日志名称
        log_file: 日志文件路径
        level: 日志级别

    Returns:
        Logger 实例
    """
    return Logger.get_logger(name, log_file, level)
