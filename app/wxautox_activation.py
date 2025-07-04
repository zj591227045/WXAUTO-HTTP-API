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

# 使用统一日志管理器
from app.unified_logger import logger

def safe_log(level, message):
    """安全的日志记录函数，避免 I/O operation on closed file 错误"""
    try:
        if level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        elif level == "debug":
            logger.debug(message)
    except (ValueError, OSError, AttributeError):
        # I/O operation on closed file 或其他 I/O 错误
        # 静默忽略，避免在应用关闭时产生错误
        pass
    except Exception:
        # 其他未知错误，也静默忽略
        pass

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
        safe_log("error", f"加载激活码配置失败: {str(e)}")
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
        safe_log("error", f"保存激活码配置失败: {str(e)}")
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
        # 检查是否在打包环境中
        is_frozen = getattr(sys, 'frozen', False)

        if is_frozen:
            # 在打包环境中，直接调用wxautox的激活API
            safe_log("info", "打包环境中尝试直接调用wxautox激活API")
            try:
                # 直接导入并调用wxautox的激活功能
                from wxautox.utils.useful import authenticate
                safe_log("info", f"开始激活wxautox，激活码: {activation_code[:8]}...")

                # 直接调用激活函数
                authenticate(activation_code)

                # 更新激活状态
                config = load_activation_config()
                config["activation_code"] = activation_code
                config["activation_status"] = True
                config["last_activation_time"] = str(datetime.now())
                save_activation_config(config)

                safe_log("info", "wxautox激活成功（打包环境）")
                return True, "wxautox激活成功", "打包环境中直接调用激活API成功"

            except ImportError:
                safe_log("error", "wxautox库未安装")
                return False, "wxautox库未安装", ""
            except Exception as e:
                error_msg = str(e)
                safe_log("error", f"打包环境中激活wxautox失败: {error_msg}")

                # 检查常见的错误类型
                if "forbidden" in error_msg.lower() or "过期" in error_msg:
                    return False, "激活码可能已过期或有使用限制", error_msg
                elif "网络" in error_msg or "network" in error_msg.lower():
                    return False, "网络连接失败，请检查网络连接", error_msg
                else:
                    return False, f"激活失败: {error_msg}", error_msg
        else:
            # 在开发环境中，使用命令行激活
            safe_log("info", "开发环境中使用命令行激活wxautox")
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
            safe_log("info", f"wxautox激活命令输出: {output}")

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

                safe_log("info", "wxautox激活成功")
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

                safe_log("warning", f"wxautox激活失败: {error_msg}")
                return False, error_msg, output
            else:
                safe_log("warning", f"wxautox激活结果未知: {output}")
                return False, f"激活结果未知: {output}", output

    except subprocess.TimeoutExpired:
        safe_log("error", "wxautox激活命令超时")
        return False, "wxautox激活命令超时", ""
    except FileNotFoundError:
        safe_log("error", "找不到wxautox命令，请确保wxautox已正确安装")
        return False, "找不到wxautox命令，请确保wxautox已正确安装", ""
    except Exception as e:
        safe_log("error", f"wxautox激活过程出错: {str(e)}")
        return False, f"wxautox激活过程出错: {str(e)}", ""


def simple_check_wxautox_activation():
    """
    简单检查wxautox激活状态
    在打包环境中使用更安全的检测策略，避免闪退

    Returns:
        str: "已激活" | "未激活" | "未知"
    """
    try:
        # 检查是否在打包环境中
        import sys
        is_frozen = getattr(sys, 'frozen', False)

        if is_frozen:
            # 在打包环境中，使用更保守的检测策略
            safe_log("info", "打包环境中检测wxautox激活状态")

            try:
                # 只尝试导入，不创建实例
                import wxautox
                safe_log("info", "wxautox库导入成功")

                # 检查关键类是否存在
                if hasattr(wxautox, 'WeChat'):
                    safe_log("info", "wxautox.WeChat类存在，认为激活成功")
                    return "已激活"
                else:
                    safe_log("warning", "wxautox.WeChat类不存在，可能未激活")
                    return "未激活"

            except ImportError as e:
                safe_log("info", f"wxautox库导入失败: {str(e)}")
                return "未激活"
            except Exception as e:
                safe_log("warning", f"打包环境中检查wxautox时出错: {str(e)}")
                return "未知"
        else:
            # 在开发环境中，使用原有的检测策略
            safe_log("info", "开发环境中检测wxautox激活状态")

            # 尝试导入wxautox库
            import wxautox
            safe_log("info", "wxautox库导入成功")

            # 尝试创建WeChat实例并初始化（更准确的激活检测）
            try:
                # 尝试实际初始化微信实例
                wechat = wxautox.WeChat()
                safe_log("info", "wxautox.WeChat实例创建并初始化成功，认为激活成功")
                return "已激活"
            except Exception as e:
                error_msg = str(e)
                # 如果是因为微信未运行等原因导致的错误，仍然认为激活成功
                if any(keyword in error_msg.lower() for keyword in ["微信", "wechat", "not found", "无法找到"]):
                    safe_log("info", f"wxautox库可用但微信未运行: {error_msg}，仍认为激活成功")
                    return "已激活"
                else:
                    safe_log("warning", f"wxautox初始化失败，可能未激活: {error_msg}")
                    return "未激活"

    except ImportError as e:
        safe_log("info", f"wxautox库导入失败: {str(e)}")
        return "未激活"
    except Exception as e:
        safe_log("warning", f"检查wxautox激活状态时出错: {str(e)}")
        return "未知"

def check_wxautox_activation_status():
    """
    简单检查wxautox激活状态

    Returns:
        str: "已激活" | "未激活" | "未知"
    """
    return simple_check_wxautox_activation()




def startup_activate_wxautox():
    """
    启动时自动激活wxautox
    
    Returns:
        tuple: (成功状态, 消息)
    """
    activation_code = get_activation_code()
    
    if not activation_code:
        safe_log("info", "未配置wxautox激活码，跳过自动激活")
        return True, "未配置激活码，跳过自动激活"

    safe_log("info", "开始自动激活wxautox...")
    success, message, output = activate_wxautox(activation_code)

    if success:
        safe_log("info", "wxautox自动激活成功")
        return True, "wxautox自动激活成功"
    else:
        safe_log("warning", f"wxautox自动激活失败: {message}")
        return False, f"wxautox自动激活失败: {message}"
