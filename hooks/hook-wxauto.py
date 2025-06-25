"""
PyInstaller hook for wxauto
确保wxauto库及其依赖被正确打包
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# 收集wxauto的所有内容
datas, binaries, hiddenimports = collect_all('wxauto')

# 确保包含所有子模块
hiddenimports += collect_submodules('wxauto')

# 添加可能的数据文件
try:
    datas += collect_data_files('wxauto')
except:
    pass

# 确保包含核心模块
hiddenimports += [
    'wxauto',
    'wxauto.wxauto',
]

print(f"wxauto hook: 找到 {len(hiddenimports)} 个隐藏导入")
print(f"wxauto hook: 找到 {len(datas)} 个数据文件")
print(f"wxauto hook: 找到 {len(binaries)} 个二进制文件")
