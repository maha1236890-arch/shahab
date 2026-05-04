@echo off
REM تشغيل نظام الحضور والغياب عبر Docker
REM يعمل على: Windows
REM المتطلب الوحيد: تثبيت Docker Desktop

echo ================================================
echo   نظام الحضور والغياب - Docker
echo ================================================

if not exist data mkdir data

docker compose up --build -d

echo.
echo التطبيق يعمل الان!
echo افتح المتصفح على: http://localhost:5000
echo بيانات الدخول: admin / admin123
echo.
echo لايقاف التطبيق: docker compose down
pause
