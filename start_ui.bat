@echo off
echo 正在检查依赖项...
python fix_dependencies.py

echo 正在启动wxauto_http_api管理界面...
python start_ui.py
pause
