#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
wxautox激活管理模块
负责管理wxautox的激活码存储、激活状态检测等功能
"""

import os
import sys
import subprocess
import logging
import json
from datetime import datetime
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 激活码配置文件路径
ACTIVATION_CONFIG_FILE = "wxautox_activation.json"


def get_activation_config_path():
    """获取激活码配置文件的完整路径"""
    return os.path.join(os.getcwd(), ACTIVATION_CONFIG_FILE)


def load_activation_config():
    """
    加载激活码配置
    
    Returns:
        dict: 激活码配置信息
    """
    config_path = get_activation_config_path()
    
    if not os.path.exists(config_path):
        return {
            "activation_code": "",
            "last_activation_time": "",
            "activation_status": False
        }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        logger.error(f"加载激活码配置失败: {str(e)}")
        return {
            "activation_code": "",
            "last_activation_time": "",
            "activation_status": False
        }


def save_activation_config(config):
    """
    保存激活码配置
    
    Args:
        config (dict): 激活码配置信息
        
    Returns:
        bool: 保存是否成功
    """
    config_path = get_activation_config_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info("激活码配置保存成功")
        return True
    except Exception as e:
        logger.error(f"保存激活码配置失败: {str(e)}")
        return False


def save_activation_code(activation_code):
    """
    保存激活码
    
    Args:
        activation_code (str): 激活码
        
    Returns:
        bool: 保存是否成功
    """
    config = load_activation_config()
    config["activation_code"] = activation_code
    
    return save_activation_config(config)


def get_activation_code():
    """
    获取保存的激活码
    
    Returns:
        str: 激活码，如果没有则返回空字符串
    """
    config = load_activation_config()
    return config.get("activation_code", "")


def activate_wxautox(activation_code=None):
    """
    激活wxautox
    
    Args:
        activation_code (str, optional): 激活码，如果不提供则使用保存的激活码
        
    Returns:
        tuple: (成功状态, 消息, 输出信息)
    """
    if not activation_code:
        activation_code = get_activation_code()
    
    if not activation_code:
        return False, "未提供激活码", ""
    
    try:
        # 执行wxautox激活命令
        result = subprocess.run(
            [sys.executable, "-m", "wxautox", "-a", activation_code],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',  # 忽略编码错误
            timeout=30  # 30秒超时
        )

        # 安全地处理输出，防止None值
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        output = stdout + stderr
        logger.info(f"wxautox激活命令输出: {output}")
        
        # 检查是否激活成功 - 支持多种成功标识
        success_indicators = [">>>激活成功！<<<", "激活成功", "activation successful"]
        failure_indicators = [">>>激活失败：forbidden<<<", "激活失败", "forbidden", "expired"]

        is_success = any(indicator in output for indicator in success_indicators)
        is_failure = any(indicator in output for indicator in failure_indicators)

        if is_success:
            # 更新激活状态
            config = load_activation_config()
            config["activation_code"] = activation_code
            config["activation_status"] = True
            config["last_activation_time"] = str(datetime.now())
            save_activation_config(config)

            logger.info("wxautox激活成功")
            return True, "wxautox激活成功", output
        elif is_failure:
            # 激活失败，更新状态
            config = load_activation_config()
            config["activation_status"] = False
            save_activation_config(config)

            if "forbidden" in output:
                error_msg = "激活码可能已过期或有使用限制"
            else:
                error_msg = "激活失败"

            logger.warning(f"wxautox激活失败: {error_msg}")
            return False, error_msg, output
        else:
            logger.warning(f"wxautox激活结果未知: {output}")
            return False, f"激活结果未知: {output}", output
            
    except subprocess.TimeoutExpired:
        logger.error("wxautox激活命令超时")
        return False, "wxautox激活命令超时", ""
    except FileNotFoundError:
        logger.error("找不到wxautox命令，请确保wxautox已正确安装")
        return False, "找不到wxautox命令，请确保wxautox已正确安装", ""
    except Exception as e:
        logger.error(f"wxautox激活过程出错: {str(e)}")
        return False, f"wxautox激活过程出错: {str(e)}", ""


def check_wxautox_activation_status():
    """
    检查wxautox激活状态

    Returns:
        bool: 是否已激活
    """
    # 首先检查配置文件中的状态
    config = load_activation_config()
    config_status = config.get("activation_status", False)

    # 如果配置显示已激活，再通过实际导入验证
    if config_status:
        try:
            # 使用subprocess验证wxautox是否真的可用
            result = subprocess.run(
                [sys.executable, "-c", "import wxautox; print('wxautox_working')"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )

            if result.returncode == 0 and "wxautox_working" in result.stdout:
                return True
            else:
                # 如果实际导入失败，更新配置状态
                logger.warning("wxautox配置显示已激活，但实际导入失败，更新状态")
                config["activation_status"] = False
                save_activation_config(config)
                return False
        except Exception as e:
            logger.warning(f"验证wxautox状态时出错: {str(e)}")
            return False

    return False


def startup_activate_wxautox():
    """
    启动时自动激活wxautox
    
    Returns:
        tuple: (成功状态, 消息)
    """
    activation_code = get_activation_code()
    
    if not activation_code:
        logger.info("未配置wxautox激活码，跳过自动激活")
        return True, "未配置激活码，跳过自动激活"
    
    logger.info("开始自动激活wxautox...")
    success, message, output = activate_wxautox(activation_code)
    
    if success:
        logger.info("wxautox自动激活成功")
        return True, "wxautox自动激活成功"
    else:
        logger.warning(f"wxautox自动激活失败: {message}")
        return False, f"wxautox自动激活失败: {message}"
