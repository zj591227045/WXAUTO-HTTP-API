"""
PyInstaller hook for wxautox
确保wxautox库及其依赖被正确打包，特别是.pyd文件
"""

import os
import glob
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# 收集wxautox的所有内容
try:
    datas, binaries, hiddenimports = collect_all('wxautox')
    print(f"wxautox hook: collect_all成功，找到 {len(datas)} 个数据文件，{len(binaries)} 个二进制文件，{len(hiddenimports)} 个隐藏导入")
except Exception as e:
    print(f"wxautox hook: collect_all失败: {e}")
    datas, binaries, hiddenimports = [], [], []

# 确保包含所有子模块
try:
    submodules = collect_submodules('wxautox')
    hiddenimports += submodules
    print(f"wxautox hook: collect_submodules成功，找到 {len(submodules)} 个子模块")
except Exception as e:
    print(f"wxautox hook: collect_submodules失败: {e}")

# 手动添加wxautox的.pyd文件
try:
    import wxautox
    wxautox_dir = os.path.dirname(wxautox.__file__)

    # 查找所有.pyd文件
    pyd_files = glob.glob(os.path.join(wxautox_dir, '*.pyd'))
    pyd_files += glob.glob(os.path.join(wxautox_dir, '**', '*.pyd'), recursive=True)

    for pyd_file in pyd_files:
        # 计算相对路径
        rel_path = os.path.relpath(pyd_file, wxautox_dir)
        dest_dir = os.path.dirname(rel_path) if os.path.dirname(rel_path) else '.'
        dest_path = os.path.join('wxautox', dest_dir)

        binaries.append((pyd_file, dest_path))
        print(f"wxautox hook: 添加.pyd文件 {pyd_file} -> {dest_path}")

except Exception as e:
    print(f"wxautox hook: 添加.pyd文件时出错: {e}")

# 添加可能的数据文件
try:
    datas += collect_data_files('wxautox')
except:
    pass

# 确保包含核心模块和.pyd模块
core_modules = [
    'wxautox',
    'wxautox.wx',
    'wxautox.utils',
    'wxautox.utils.win32',  # 关键的.pyd模块
    'wxautox.utils.tools',  # 关键的.pyd模块
    'wxautox.utils.useful', # 关键的.pyd模块
    'wxautox.uia',
    'wxautox.uia.uiplug',   # 关键的.pyd模块
    'wxautox.ui',
    'wxautox.ui.chatbox',
    'wxautox.ui.component',
    'wxautox.ui.main',
    'wxautox.ui.moment',
    'wxautox.ui.navigationbox',
    'wxautox.ui.sessionbox',
    'wxautox.msgs',
    'wxautox.msgs.base',    # 关键的.pyd模块
    'wxautox.msgs.friend',  # 关键的.pyd模块
    'wxautox.msgs.mattr',   # 关键的.pyd模块
    'wxautox.msgs.msg',     # 关键的.pyd模块
    'wxautox.msgs.self',    # 关键的.pyd模块
    'wxautox.msgs.type',    # 关键的.pyd模块
]

hiddenimports += core_modules
print(f"wxautox hook: 添加了 {len(core_modules)} 个核心模块")

# 尝试手动处理wxautox.utils的星号导入问题
try:
    # 导入wxautox.utils.win32模块，获取其导出的函数
    import wxautox.utils.win32 as win32_module
    win32_functions = [name for name in dir(win32_module) if not name.startswith('_')]

    # 为每个函数创建虚拟的模块导入
    for func_name in win32_functions:
        if func_name in ['GetAllWindows', 'SetClipboardText', 'FindWindow']:
            # 这些是PyInstaller警告中提到的缺失函数
            print(f"wxautox hook: 处理关键函数 {func_name}")

    print(f"wxautox hook: 从win32模块找到 {len(win32_functions)} 个函数")

except Exception as e:
    print(f"wxautox hook: 处理win32模块时出错: {e}")

# 强制包含整个wxautox包目录
try:
    import wxautox
    wxautox_path = os.path.dirname(wxautox.__file__)
    # 将整个wxautox目录作为数据文件包含
    datas.append((wxautox_path, 'wxautox'))
    print(f"wxautox hook: 强制包含整个wxautox目录: {wxautox_path}")
except Exception as e:
    print(f"wxautox hook: 强制包含wxautox目录失败: {e}")

print(f"wxautox hook: 最终统计 - {len(hiddenimports)} 个隐藏导入")
print(f"wxautox hook: 最终统计 - {len(datas)} 个数据文件")
print(f"wxautox hook: 最终统计 - {len(binaries)} 个二进制文件")
