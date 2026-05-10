@echo off
chcp 65001 > nul
title بناء نظام إدارة الموظفين

echo =====================================================
echo    بناء نظام إدارة الموظفين للويندوز
echo =====================================================
echo.

REM التحقق من وجود Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [خطأ] Python غير مثبت. حمّله من https://python.org
    pause
    exit /b 1
)

echo [1/4] تثبيت المكتبات المطلوبة...
pip install PyQt5 openpyxl pyinstaller
if errorlevel 1 (
    echo [خطأ] فشل تثبيت المكتبات
    pause
    exit /b 1
)

echo.
echo [2/4] تنظيف ملفات البناء السابقة...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo.
echo [3/4] بناء الملف التنفيذي...
pyinstaller employee_system.spec --clean --noconfirm
if errorlevel 1 (
    echo [خطأ] فشل البناء، راجع الأخطاء أعلاه
    pause
    exit /b 1
)

echo.
echo [4/4] نسخ قاعدة البيانات إلى مجلد الناتج...
if exist employee_system.db (
    copy employee_system.db dist\employee_system.db
    echo تم نسخ قاعدة البيانات.
) else (
    echo ملاحظة: لا توجد قاعدة بيانات، ستُنشأ تلقائياً عند أول تشغيل.
)

echo.
echo =====================================================
echo    تم البناء بنجاح!
echo    الملف التنفيذي في: dist\نظام_إدارة_الموظفين.exe
echo =====================================================
echo.
pause
