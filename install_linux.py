#!/usr/bin/env python3
"""
سكريبت تثبيت نظام إدارة الموظفين على Linux
يقوم بـ:
1. نسخ الملف التنفيذي إلى مجلد التطبيقات
2. إنشاء أيقونة سطح المكتب
3. تسجيل التطبيق في قائمة التطبيقات
"""

import os
import sys
import shutil
import subprocess
import stat

APP_NAME_AR = 'نظام إدارة الموظفين'
APP_NAME_EN = 'employee_system'
BINARY_NAME = 'نظام_إدارة_الموظفين'

def get_binary_path():
    """ابحث عن الملف التنفيذي بجانب السكريبت"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for name in [BINARY_NAME, f'{BINARY_NAME}.bin', 'نظام_ادارة_الموظفين']:
        p = os.path.join(script_dir, name)
        if os.path.isfile(p):
            return p
    return None

def main():
    sep = '=' * 50
    print(sep)
    print(f'  تثبيت {APP_NAME_AR}')
    print(sep)

    home = os.path.expanduser('~')
    install_dir = os.path.join(home, '.local', 'share', APP_NAME_EN)
    icon_dir    = os.path.join(home, '.local', 'share', 'icons')
    apps_dir    = os.path.join(home, '.local', 'share', 'applications')
    desktop_dir = os.path.join(home, 'Desktop')
    if not os.path.isdir(desktop_dir):
        desktop_dir = os.path.join(home, 'سطح المكتب')

    # Find binary
    binary_src = get_binary_path()
    if not binary_src:
        print(f'❌ لم يُعثر على الملف التنفيذي "{BINARY_NAME}" بجانب السكريبت.')
        sys.exit(1)

    # Find icon
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_src = os.path.join(script_dir, 'app_icon.png')

    # Create dirs
    for d in [install_dir, icon_dir, apps_dir]:
        os.makedirs(d, exist_ok=True)

    # Copy binary
    binary_dst = os.path.join(install_dir, BINARY_NAME)
    print(f'📦 نسخ التطبيق إلى {binary_dst}...')
    shutil.copy2(binary_src, binary_dst)
    os.chmod(binary_dst, os.stat(binary_dst).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # Copy icon
    icon_dst = os.path.join(icon_dir, f'{APP_NAME_EN}.png')
    if os.path.isfile(icon_src):
        shutil.copy2(icon_src, icon_dst)
        print(f'🖼️  نسخ الأيقونة إلى {icon_dst}...')
    else:
        icon_dst = APP_NAME_EN  # fallback to name

    # Create .desktop file content
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={APP_NAME_AR}
Name[ar]={APP_NAME_AR}
Name[en]=Employee Management System
Comment=نظام إدارة الموظفين والحضور والزيارات
Comment[en]=Employee Management System
Exec={binary_dst}
Icon={icon_dst}
Terminal=false
Categories=Office;Database;
StartupNotify=true
StartupWMClass={APP_NAME_EN}
"""

    # Install to applications menu
    apps_desktop = os.path.join(apps_dir, f'{APP_NAME_EN}.desktop')
    with open(apps_desktop, 'w', encoding='utf-8') as f:
        f.write(desktop_content)
    os.chmod(apps_desktop, 0o755)
    print(f'📋 تسجيل في قائمة التطبيقات: {apps_desktop}')

    # Install to Desktop
    if os.path.isdir(desktop_dir):
        desktop_file = os.path.join(desktop_dir, f'{APP_NAME_EN}.desktop')
        with open(desktop_file, 'w', encoding='utf-8') as f:
            f.write(desktop_content)
        os.chmod(desktop_file, 0o755)
        # Mark as trusted (for GNOME)
        try:
            subprocess.run(['gio', 'set', desktop_file,
                            'metadata::trusted', 'true'], check=False, capture_output=True)
        except Exception:
            pass
        print(f'🖥️  أيقونة سطح المكتب: {desktop_file}')

    # Update desktop database
    try:
        subprocess.run(['update-desktop-database', apps_dir], check=False, capture_output=True)
    except Exception:
        pass

    print()
    print('✅ تم التثبيت بنجاح!')
    print(f'   يمكنك تشغيل التطبيق من سطح المكتب أو من قائمة التطبيقات.')
    print(f'   أو مباشرة: {binary_dst}')


if __name__ == '__main__':
    main()
