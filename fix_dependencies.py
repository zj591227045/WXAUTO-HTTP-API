"""
修复依赖项
检查并修复项目依赖项
"""

import os
import sys
import subprocess
import pkg_resources

def check_and_install_dependencies():
    """检查并安装依赖项"""
    print("正在检查依赖项...")
    
    # 定义所需的依赖项及其版本
    required_packages = {
        'flask': '2.0.1',
        'flask-limiter': '1.4',
        'werkzeug': '2.0.1',
        'python-dotenv': '0.19.0',
        'requests': '2.26.0',
        'psutil': '5.8.0'
    }
    
    # 检查并安装依赖项
    for package, version in required_packages.items():
        try:
            # 检查是否已安装
            pkg_resources.get_distribution(package)
            print(f"✓ {package} 已安装")
        except pkg_resources.DistributionNotFound:
            print(f"✗ {package} 未安装，正在安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", f"{package}=={version}"])
            print(f"✓ {package} 安装成功")
        except Exception as e:
            print(f"! {package} 检查失败: {str(e)}")
    
    # 特别检查werkzeug版本
    try:
        werkzeug_version = pkg_resources.get_distribution('werkzeug').version
        print(f"当前werkzeug版本: {werkzeug_version}")
        
        # 如果版本不是2.0.1，重新安装
        if werkzeug_version != '2.0.1':
            print("werkzeug版本不匹配，正在重新安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "werkzeug==2.0.1"])
            print("werkzeug重新安装成功")
    except Exception as e:
        print(f"检查werkzeug版本失败: {str(e)}")
    
    print("依赖项检查完成")

if __name__ == "__main__":
    check_and_install_dependencies()
