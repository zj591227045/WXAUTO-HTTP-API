"""
配置管理模块
用于处理配置文件的读写
"""

import os
import json
import logging
from pathlib import Path

# 配置目录
DATA_DIR = Path("data")
API_DIR = DATA_DIR / "api"
CONFIG_DIR = API_DIR / "config"
LOGS_DIR = API_DIR / "logs"
TEMP_DIR = API_DIR / "temp"  # 临时文件目录，用于保存图片、文件等

# 确保目录存在
def ensure_dirs():
    """确保所有必要的目录都存在"""
    for directory in [DATA_DIR, API_DIR, CONFIG_DIR, LOGS_DIR, TEMP_DIR]:
        directory.mkdir(exist_ok=True, parents=True)

# 日志过滤器配置文件
LOG_FILTER_CONFIG = CONFIG_DIR / "log_filter.json"

# 默认配置
DEFAULT_LOG_FILTER = {
    "hide_status_check": False,
    "hide_debug": False,
    "custom_filter": ""
}

def load_log_filter_config():
    """
    加载日志过滤器配置

    Returns:
        dict: 日志过滤器配置
    """
    ensure_dirs()

    if not LOG_FILTER_CONFIG.exists():
        # 如果配置文件不存在，创建默认配置
        save_log_filter_config(DEFAULT_LOG_FILTER)
        return DEFAULT_LOG_FILTER

    try:
        with open(LOG_FILTER_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 确保所有必要的键都存在
        for key in DEFAULT_LOG_FILTER:
            if key not in config:
                config[key] = DEFAULT_LOG_FILTER[key]

        return config
    except Exception as e:
        logging.error(f"加载日志过滤器配置失败: {str(e)}")
        return DEFAULT_LOG_FILTER

def save_log_filter_config(config):
    """
    保存日志过滤器配置

    Args:
        config (dict): 日志过滤器配置
    """
    ensure_dirs()

    try:
        with open(LOG_FILTER_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logging.debug("日志过滤器配置已保存")
    except Exception as e:
        logging.error(f"保存日志过滤器配置失败: {str(e)}")

def get_log_file_path(filename=None):
    """
    获取日志文件路径

    Args:
        filename (str, optional): 日志文件名。如果为None，则使用默认文件名。

    Returns:
        Path: 日志文件路径
    """
    ensure_dirs()

    if filename is None:
        filename = "api.log"

    return LOGS_DIR / filename
