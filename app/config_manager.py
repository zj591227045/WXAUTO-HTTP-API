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

# 配置文件路径
LOG_FILTER_CONFIG = CONFIG_DIR / "log_filter.json"
APP_CONFIG_FILE = CONFIG_DIR / "app_config.json"

# 确保目录存在
def ensure_dirs():
    """确保所有必要的目录都存在"""
    for directory in [DATA_DIR, API_DIR, CONFIG_DIR, LOGS_DIR, TEMP_DIR]:
        directory.mkdir(exist_ok=True, parents=True)

# 默认配置
DEFAULT_LOG_FILTER = {
    "hide_status_check": True,  # 默认隐藏微信状态检查日志
    "hide_debug": True,         # 默认隐藏DEBUG级别日志
    "custom_filter": ""
}

# 默认应用配置
DEFAULT_APP_CONFIG = {
    "api_keys": ["test-key-2"],
    "port": 5000,
    "wechat_lib": "wxauto",
    "auto_start_enabled": False,
    "auto_start_countdown": 5
}

def load_log_filter_config(force_defaults=False):
    """
    加载日志过滤器配置

    Args:
        force_defaults (bool): 是否强制使用默认值覆盖现有配置

    Returns:
        dict: 日志过滤器配置
    """
    ensure_dirs()

    if not LOG_FILTER_CONFIG.exists() or force_defaults:
        # 如果配置文件不存在或强制使用默认值，创建默认配置
        save_log_filter_config(DEFAULT_LOG_FILTER)
        return DEFAULT_LOG_FILTER

    try:
        with open(LOG_FILTER_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 确保所有必要的键都存在，并使用默认值
        config_updated = False
        for key in DEFAULT_LOG_FILTER:
            if key not in config:
                config[key] = DEFAULT_LOG_FILTER[key]
                config_updated = True
            # 对于特定的键，强制使用默认值
            elif key in ['hide_status_check', 'hide_debug'] and not config[key]:
                config[key] = DEFAULT_LOG_FILTER[key]
                config_updated = True

        # 如果配置被更新，保存回文件
        if config_updated:
            save_log_filter_config(config)
            logging.info("日志过滤器配置已更新为默认值")

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

def load_app_config():
    """
    加载应用配置，如果配置文件不存在，则使用默认配置并创建配置文件

    Returns:
        dict: 应用配置
    """
    ensure_dirs()

    # 如果配置文件不存在，使用默认配置
    if not APP_CONFIG_FILE.exists():
        # 使用默认配置
        config = DEFAULT_APP_CONFIG.copy()

        # 保存配置
        save_app_config(config)
        return config

    # 如果配置文件存在，直接读取
    try:
        with open(APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 确保所有必要的键都存在
        for key, value in DEFAULT_APP_CONFIG.items():
            if key not in config:
                config[key] = value

        return config
    except Exception as e:
        logging.error(f"加载应用配置失败: {str(e)}")
        return DEFAULT_APP_CONFIG.copy()

def save_app_config(config):
    """
    保存应用配置

    Args:
        config (dict): 应用配置
    """
    ensure_dirs()

    try:
        with open(APP_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logging.debug("应用配置已保存")
    except Exception as e:
        logging.error(f"保存应用配置失败: {str(e)}")

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
