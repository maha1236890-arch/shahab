@echo off
REM ============================================================
REM  build_windows.bat  —  بناء نسخة Windows من نظام الحضور
REM  يُشغَّل من داخل مجلد المشروع على جهاز Windows
REM  متطلبات: Python 3.10+ مثبّت + pip
REM ============================================================

setlocal EnableDelayedExpansion
set PROJECT=attendance_system
set DIST=dist\attendance
set ICON=static\img\icon.ico

echo ============================================
echo  %PROJECT% - Windows Build Script
echo ============================================
echo.

REM 1. تثبيت المتطلبات
echo [1/5] Installing Python dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
pip install pyinstaller ^
    PySide6 ^
    flask ^
    openpyxl ^
    reportlab ^
    arabic-reshaper ^
    python-bidi ^
    pyinstaller-hooks-contrib >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip install failed
    pause & exit /b 1
)
echo    Done.

REM 2. تنظيف البناء السابق
echo [2/5] Cleaning previous build...
if exist build     rmdir /s /q build
if exist %DIST%    rmdir /s /q %DIST%

REM 3. بناء التطبيق
echo [3/5] Running PyInstaller...
pyinstaller attendance_windows.spec
if errorlevel 1 (
    echo ERROR: PyInstaller failed
    pause & exit /b 1
)
echo    Build successful.

REM 4. نسخ الأصول
echo [4/5] Copying assets...
xcopy /e /i /q static            %DIST%\static
xcopy /e /i /q templates         %DIST%\templates
if exist favicon.ico copy /y favicon.ico %DIST%\

REM 5. إنشاء مثبّت بـ Inno Setup (اختياري — إن كان مثبّتاً)
echo [5/5] Checking Inno Setup...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
    echo    Building installer with Inno Setup...
    %ISCC% attendance_setup.iss
    if errorlevel 1 ( echo    WARNING: Inno Setup failed ) else ( echo    Installer created in Output\ )
) else (
    echo    Inno Setup not found — skipping installer.
    echo    You can distribute the folder: %DIST%\
)

echo.
echo ============================================
echo  Build complete!
echo  Output: %DIST%\attendance.exe
echo ============================================
pause
