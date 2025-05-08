#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
清理项目中的所有 __pycache__ 目录和 .pyc 文件
"""

import os
import shutil
import sys

def clean_pycache(root_dir='.'):
    """
    递归删除指定目录下的所有 __pycache__ 目录和 .pyc 文件

    Args:
        root_dir (str): 要清理的根目录
    """
    print(f"开始清理 {os.path.abspath(root_dir)} 目录下的 __pycache__ 和 .pyc 文件...")

    pycache_dirs = []
    pyc_files = []

    # 遍历目录
    for root, dirs, files in os.walk(root_dir):
        # 查找 __pycache__ 目录
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            pycache_dirs.append(pycache_path)

        # 查找 .pyc 文件
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                pyc_files.append(pyc_path)

    # 先删除 .pyc 文件
    for pyc_file in pyc_files:
        try:
            print(f"删除文件: {pyc_file}")
            os.remove(pyc_file)
        except Exception as e:
            print(f"删除 {pyc_file} 失败: {str(e)}")

    # 再删除 __pycache__ 目录
    for pycache_dir in pycache_dirs:
        try:
            print(f"删除目录: {pycache_dir}")
            shutil.rmtree(pycache_dir)
        except Exception as e:
            print(f"删除 {pycache_dir} 失败: {str(e)}")

    print(f"清理完成! 共删除 {len(pycache_dirs)} 个 __pycache__ 目录和 {len(pyc_files)} 个 .pyc 文件")

if __name__ == "__main__":
    # 如果提供了命令行参数，使用第一个参数作为根目录
    if len(sys.argv) > 1:
        clean_pycache(sys.argv[1])
    else:
        # 否则使用当前目录
        clean_pycache()
