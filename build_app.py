"""
build_app.py – سكريبت بناء التطبيق كملف تنفيذي مستقل
يعمل على Linux / Windows / macOS

الاستخدام:
    python3 build_app.py

المخرجات:
    dist/attendance/            ← مجلد يحتوي التطبيق وكل ملفاته
    dist/attendance/attendance  ← ملف التشغيل (Linux/macOS)
    dist/attendance/attendance.exe  ← ملف التشغيل (Windows)
"""

import os
import sys
import shutil
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 55)
    print("  بناء تطبيق الحضور والغياب")
    print("=" * 55)

    # ── التحقق من PyInstaller ──────────────────────────────────────
    try:
        import PyInstaller
        print(f"✔ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("تثبيت PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # ── تنظيف بناء سابق ──────────────────────────────────────────
    for d in ["build", "dist"]:
        p = os.path.join(BASE, d)
        if os.path.exists(p):
            shutil.rmtree(p)
            print(f"  حُذف: {d}/")

    spec_file = os.path.join(BASE, "attendance.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # ── تجميع قائمة ملفات البيانات ───────────────────────────────
    sep = ";" if sys.platform == "win32" else ":"

    datas = [
        f"templates{sep}templates",
        f"static{sep}static",
        f"database.py{sep}.",
        f"export_utils.py{sep}.",
        f"app.py{sep}.",
    ]

    # ── وسيطات PyInstaller ────────────────────────────────────────
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "attendance",
        "--onedir",                      # مجلد واحد (أسرع من onefile)
        "--windowed",                    # بدون console
        "--noconfirm",
        "--clean",
    ]

    for d in datas:
        pyinstaller_args += ["--add-data", d]

    # مكتبات مخفية ضرورية
    hidden = [
        "flask", "jinja2", "werkzeug", "click",
        "openpyxl", "reportlab", "arabic_reshaper", "bidi",
        "sqlite3",
        "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineCore",
        "PySide6.QtNetwork", "PySide6.QtCore", "PySide6.QtGui",
        "PySide6.QtWidgets",
    ]
    for h in hidden:
        pyinstaller_args += ["--hidden-import", h]

    # استبعاد Qt الأخرى لمنع التعارض
    excluded = ["PyQt5", "PyQt6", "PySide2", "wx"]
    for ex in excluded:
        pyinstaller_args += ["--exclude-module", ex]

    pyinstaller_args.append(os.path.join(BASE, "desktop.py"))

    print("\n⚙  جارٍ البناء (قد يستغرق دقيقتين)...\n")
    result = subprocess.run(pyinstaller_args, cwd=BASE)

    if result.returncode != 0:
        print("\n✗ فشل البناء!")
        sys.exit(1)

    # ── نسخ قاعدة البيانات (إن وُجدت) إلى dist ─────────────────
    dist_dir = os.path.join(BASE, "dist", "attendance")
    db_src = os.path.join(BASE, "attendance.db")
    if os.path.exists(db_src):
        shutil.copy2(db_src, dist_dir)
        print("  ✔ نُسخت قاعدة البيانات")

    # ── نسخ الأيقونة ──────────────────────────────────────────────
    icon_src = os.path.join(BASE, "static", "img", "icon.png")
    if os.path.exists(icon_src):
        shutil.copy2(icon_src, dist_dir)
        print("  ✔ نُسخت الأيقونة")

    # ── اسم ملف التنفيذ ──────────────────────────────────────────
    exe_name = "attendance.exe" if sys.platform == "win32" else "attendance"
    exe_path = os.path.join(dist_dir, exe_name)

    print("\n" + "=" * 55)
    print("  ✔ تم البناء بنجاح!")
    print(f"  المجلد : dist/attendance/")
    print(f"  التشغيل: {exe_path}")
    print("=" * 55)
    print("\n  انسخ مجلد dist/attendance/ إلى أي جهاز وشغّله مباشرة.")


if __name__ == "__main__":
    main()
