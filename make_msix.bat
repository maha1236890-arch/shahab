@echo off
REM ==========================================================================
REM  make_msix.bat — يحوّل dist\attendance إلى حزمة MSIX لـ Microsoft Store
REM  يُشغَّل على Windows بعد build_windows.bat
REM  متطلبات: MakeAppx.exe (مثبّتة مع Windows SDK)
REM ==========================================================================

setlocal EnableDelayedExpansion

set APP_NAME=Shahab
set PUBLISHER=CN=MGGSoftware
set VERSION=2.0.0.0
set DIST=dist\attendance
set MSIX_DIR=msix_pkg
set OUT=shahab_%VERSION%.msix

echo ==========================================
echo  %APP_NAME% — MSIX Packaging Tool
echo ==========================================
echo.

REM ── 1. التحقق من dist\attendance ─────────────────────────────────────────
if not exist "%DIST%\attendance.exe" (
    echo ERROR: attendance.exe not found. Run build_windows.bat first.
    pause & exit /b 1
)

REM ── 2. إنشاء هيكل MSIX ───────────────────────────────────────────────────
echo [1/4] Preparing MSIX folder structure...
if exist "%MSIX_DIR%" rmdir /s /q "%MSIX_DIR%"
mkdir "%MSIX_DIR%"
xcopy /e /i /q "%DIST%" "%MSIX_DIR%\app"

REM ── 3. نسخ الأيقونات ─────────────────────────────────────────────────────
echo [2/4] Copying store assets...
mkdir "%MSIX_DIR%\Assets"
copy /y "static\img\store_assets\Square44x44Logo.scale-100.png"   "%MSIX_DIR%\Assets\"
copy /y "static\img\store_assets\Square150x150Logo.scale-100.png" "%MSIX_DIR%\Assets\"
copy /y "static\img\store_assets\Square310x310Logo.scale-100.png" "%MSIX_DIR%\Assets\"
copy /y "static\img\store_assets\Wide310x150Logo.scale-100.png"   "%MSIX_DIR%\Assets\"
copy /y "static\img\store_assets\StoreLogo.scale-100.png"         "%MSIX_DIR%\Assets\"
copy /y "static\img\store_assets\SplashScreen.scale-100.png"      "%MSIX_DIR%\Assets\"

REM ── 4. إنشاء AppxManifest.xml ────────────────────────────────────────────
echo [3/4] Creating AppxManifest.xml...
(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<Package
echo   xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
echo   xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
echo   xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
echo   IgnorableNamespaces="uap rescap"^>
echo.
echo   ^<Identity
echo     Name="MGGSoftware.Shahab"
echo     Publisher="%PUBLISHER%"
echo     Version="%VERSION%"
echo     ProcessorArchitecture="x64" /^>
echo.
echo   ^<Properties^>
echo     ^<DisplayName^>شهاب^</DisplayName^>
echo     ^<PublisherDisplayName^>MGG Software^</PublisherDisplayName^>
echo     ^<Logo^>Assets\StoreLogo.scale-100.png^</Logo^>
echo   ^</Properties^>
echo.
echo   ^<Dependencies^>
echo     ^<TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22621.0" /^>
echo   ^</Dependencies^>
echo.
echo   ^<Resources^>
echo     ^<Resource Language="ar" /^>
echo     ^<Resource Language="en" /^>
echo   ^</Resources^>
echo.
echo   ^<Applications^>
echo     ^<Application Id="App" Executable="app\attendance.exe" EntryPoint="Windows.FullTrustApplication"^>
echo       ^<uap:VisualElements
echo         DisplayName="شهاب"
echo         Description="نظام متكامل لإدارة حضور وغياب الموظفين"
echo         BackgroundColor="transparent"
echo         Square150x150Logo="Assets\Square150x150Logo.scale-100.png"
echo         Square44x44Logo="Assets\Square44x44Logo.scale-100.png"^>
echo         ^<uap:SplashScreen Image="Assets\SplashScreen.scale-100.png" /^>
echo         ^<uap:DefaultTile Wide310x150Logo="Assets\Wide310x150Logo.scale-100.png"
echo                           Square310x310Logo="Assets\Square310x310Logo.scale-100.png" /^>
echo       ^</uap:VisualElements^>
echo       ^<Extensions^>
echo         ^<rescap:Extension Category="windows.fullTrustProcess" Executable="app\attendance.exe" /^>
echo       ^</Extensions^>
echo     ^</Application^>
echo   ^</Applications^>
echo.
echo   ^<Capabilities^>
echo     ^<rescap:Capability Name="runFullTrust" /^>
echo   ^</Capabilities^>
echo.
echo ^</Package^>
) > "%MSIX_DIR%\AppxManifest.xml"

REM ── 5. بناء MSIX ──────────────────────────────────────────────────────────
echo [4/4] Building MSIX package...

REM ابحث عن MakeAppx.exe في Windows SDK
set MAKEAPPX=""
for /d %%d in ("C:\Program Files (x86)\Windows Kits\10\bin\*") do (
    if exist "%%d\x64\makeappx.exe" set MAKEAPPX="%%d\x64\makeappx.exe"
)

if %MAKEAPPX%=="" (
    echo.
    echo WARNING: MakeAppx.exe not found.
    echo Install Windows SDK from:
    echo   https://developer.microsoft.com/windows/downloads/windows-sdk/
    echo.
    echo Then run manually:
    echo   makeappx pack /d "%MSIX_DIR%" /p "%OUT%"
    pause & exit /b 1
)

%MAKEAPPX% pack /d "%MSIX_DIR%" /p "%OUT%" /overwrite
if errorlevel 1 (
    echo ERROR: MSIX packaging failed.
    pause & exit /b 1
)

echo.
echo ==========================================
echo  SUCCESS!
echo  Output: %OUT%
echo ==========================================
echo.
echo Next steps:
echo  1. Sign the MSIX: signtool sign /fd SHA256 /a "%OUT%"
echo  2. Upload to: https://partner.microsoft.com/dashboard
echo.
pause
