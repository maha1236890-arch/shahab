# -*- mode: python ; coding: utf-8 -*-
# attendance_windows.spec  —  PyInstaller spec لنسخة Windows
# يُشغَّل من مجلد المشروع على جهاز Windows

import os
BASE = os.path.abspath('.')

a = Analysis(
    ['desktop.py'],
    pathex=[BASE],
    binaries=[],
    datas=[
        ('templates',           'templates'),
        ('static',              'static'),
        ('database.py',         '.'),
        ('export_utils.py',     '.'),
        ('app.py',              '.'),
        ('license.py',          '.'),
        ('admin_panel.py',      '.'),
        ('static/img/icon.ico', 'static/img'),
    ],
    hiddenimports=[
        'flask', 'jinja2', 'werkzeug', 'click',
        'openpyxl', 'reportlab',
        'arabic_reshaper', 'bidi',
        'sqlite3', 'license',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtNetwork',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'wx'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='attendance',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='static\\img\\icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='attendance',
)
