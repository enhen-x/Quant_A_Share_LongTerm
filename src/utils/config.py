"""
配置加载模块

支持 YAML 配置文件加载、默认值处理和环境变量支持
"""

import os
import yaml
from typing import Any, Dict, Optional, Union
from pathlib import Path


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，默认为 config/main.yaml
        """
        if config_path is None:
            self.config_path = Path(__file__).parent.parent.parent / "config" / "main.yaml"
        else:
            self.config_path = Path(config_path)

        self._config = self._load_config()
        self._defaults = self._get_defaults()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(str(self.config_path), "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 替换环境变量
        config = self._replace_env_vars(config)

        return config

    def _replace_env_vars(self, obj: Any) -> Any:
        """递归替换环境变量"""
        if isinstance(obj, str):
            if obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                default_value = None
                if ":" in env_var:
                    env_var, default_value = env_var.split(":", 1)
                return os.getenv(env_var, default_value)
            return obj
        elif isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        return obj

    def _get_defaults(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "tushare": {
                "token": "",
                "timeout": 30,
                "retry": 3,
            },
            "deviation": {
                "window": {
                    "type": "simple",
                    "size": 252,
                },
                "normalization": {
                    "method": "zscore",
                },
                "percentile_window": 1260,
            },
            "distribution": {
                "stats_window": 252,
                "histogram": {
                    "n_bins": 50,
                    "density": True,
                },
                "thresholds": {
                    "skewness": 0.5,
                    "kurtosis": 3.5,
                    "jb_pvalue": 0.05,
                },
            },
            "grid": {
                "n_zones": 10,
                "type_selection": "adaptive",
                "range": {
                    "multiplier": 3.0,
                    "min_range": 0.05,
                },
                "smoothing": {
                    "enabled": True,
                    "factor": 0.5,
                },
                "update_frequency": "monthly",
            },
            "position": {
                "max_position": 1.0,
                "min_position": 0.0,
                "max_daily_change": 0.2,
                "default_mappings": {
                    "normal": {
                        "low_zone": [1, 2, 3],
                        "high_zone": [8, 9, 10],
                    },
                    "skewed_right": {
                        "low_zone": [1, 2, 3, 4],
                        "high_zone": [9, 10],
                    },
                    "skewed_left": {
                        "low_zone": [1, 2],
                        "high_zone": [7, 8, 9, 10],
                    },
                },
            },
            "risk": {
                "drawdown": {
                    "max_drawdown": 0.15,
                    "stop_loss": 0.20,
                    "recovery_mode": False,
                },
                "concentration": {
                    "max_single_stock": 0.15,
                    "max_industry": 0.30,
                },
                "liquidity": {
                    "min_turnover": 1000000,
                    "max_position_ratio": 0.10,
                },
            },
            "rebalancing": {
                "trigger": {
                    "deviation_threshold": 0.02,
                    "position_threshold": 0.05,
                    "time_based": True,
                    "frequency": "weekly",
                },
                "method": "smooth",
                "smooth_period": 5,
            },
            "report": {
                "frequency": "weekly",
                "sections": [
                    "distribution_analysis",
                    "grid_visualization",
                    "position_allocation",
                    "risk_metrics",
                    "performance_summary",
                ],
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'deviation.window.size'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_or_default(self, key: str) -> Any:
        """
        获取配置值或默认值

        Args:
            key: 配置键

        Returns:
            配置值，如果不存在则返回默认值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return self._get_nested_default(keys)

        return value

    def _get_nested_default(self, keys: list) -> Any:
        """从默认配置中获取嵌套值"""
        value = self._defaults
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value

    def save(self, path: Optional[Union[str, Path]] = None):
        """
        保存配置到文件

        Args:
            path: 保存路径，默认为原配置文件路径
        """
        if path is None:
            save_path = str(self.config_path)
        else:
            save_path = str(Path(path))

        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)


_config_instance: Optional[Config] = None


def get_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    获取配置实例（单例模式）

    Args:
        config_path: 配置文件路径

    Returns:
        Config 实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
