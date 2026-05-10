# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Employee Management System
# نظام إدارة الموظفين

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Include tabs package
        ('tabs/*.py', 'tabs'),
        # Application icon
        ('app_icon.png', '.'),
        # Install script and icon for desktop shortcut
        ('install_linux.py', '.'),
    ],
    hiddenimports=[
        # PyQt5 essentials
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtPrintSupport',
        # openpyxl
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.styles.fills',
        'openpyxl.styles.fonts',
        'openpyxl.styles.alignment',
        'openpyxl.styles.borders',
        # App modules
        'database',
        'styles',
        'export_utils',
        'printing_utils',
        'tabs.dashboard_tab',
        'tabs.employees_tab',
        'tabs.attendance_tab',
        'tabs.present_tab',
        'tabs.search_tab',
        'tabs.nutrition_tab',
        'tabs.visits_tab',
        'tabs.qat_tab',
        'tabs.distribution_tab',
        'tabs.departments_tab',
        'tabs.reports_tab',
        'tabs.users_tab',
        'login_dialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='نظام_إدارة_الموظفين',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico',
)
