# -*- mode: python ; coding: utf-8 -*-
# attendance_windows.spec  —  PyInstaller spec لنسخة Windows
# يُشغَّل من مجلد المشروع على جهاز Windows

import os
from PyInstaller.utils.hooks import collect_all

BASE = os.path.abspath('.')

# تضمين كامل لمكتبات Excel وPDF
openpyxl_datas,   openpyxl_bins,   openpyxl_hidden   = collect_all('openpyxl')
reportlab_datas,  reportlab_bins,  reportlab_hidden  = collect_all('reportlab')

a = Analysis(
    ['desktop.py'],
    pathex=[BASE],
    binaries=[] + openpyxl_bins + reportlab_bins,
    datas=[
        ('templates',           'templates'),
        ('static',              'static'),
        ('database.py',         '.'),
        ('export_utils.py',     '.'),
        ('app.py',              '.'),
        ('license.py',          '.'),
        ('admin_panel.py',      '.'),
        ('static/img/icon.ico', 'static/img'),
    ] + openpyxl_datas + reportlab_datas,
    hiddenimports=[
        'flask', 'jinja2', 'werkzeug', 'click',
        'arabic_reshaper', 'bidi',
        'sqlite3', 'license',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtNetwork',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ] + openpyxl_hidden + reportlab_hidden,
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
