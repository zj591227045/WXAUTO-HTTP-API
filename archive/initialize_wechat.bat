@echo off
echo 正在初始化微信...
curl -X POST -H "X-API-Key: test-key-2" http://localhost:5000/api/wechat/initialize
echo.
echo 初始化完成！
pause
