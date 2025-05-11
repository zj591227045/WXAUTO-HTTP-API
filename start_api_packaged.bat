@echo off
echo 正在启动wxauto_http_api API服务...
"%~dp0wxauto_http_api.exe" --service api --debug
pause
