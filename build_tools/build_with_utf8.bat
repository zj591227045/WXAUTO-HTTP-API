@echo off
echo 设置环境变量 PYTHONIOENCODING=utf-8
set PYTHONIOENCODING=utf-8
echo 设置环境变量 PYTHONLEGACYWINDOWSSTDIO=0
set PYTHONLEGACYWINDOWSSTDIO=0

echo 开始打包应用程序...
cd ..
python -m build_tools.build_app %*

echo 打包完成！
pause
