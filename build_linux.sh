#!/bin/bash
# سكريبت البناء المحلي لـ Linux
# يُشغَّل على الجهاز مباشرةً

set -e

echo "=================================================="
echo "   بناء نظام إدارة الموظفين - Linux"
echo "=================================================="

cd "$(dirname "$0")"

# التحقق من Python
if ! command -v python3 &>/dev/null; then
    echo "[خطأ] Python3 غير مثبت"
    exit 1
fi

echo "[1/4] تثبيت المكتبات..."
pip3 install --quiet PyQt5 openpyxl pyinstaller

echo "[2/4] تنظيف ملفات البناء السابقة..."
rm -rf dist/ build/

echo "[3/4] بناء الملف التنفيذي..."
pyinstaller employee_system.spec --clean --noconfirm

echo "[4/4] نسخ قاعدة البيانات..."
if [ -f employee_system.db ]; then
    cp employee_system.db dist/employee_system.db
    echo "تم نسخ قاعدة البيانات."
else
    echo "ملاحظة: ستُنشأ قاعدة البيانات تلقائياً عند أول تشغيل."
fi

chmod +x "dist/نظام_إدارة_الموظفين"

echo ""
echo "=================================================="
echo "   تم البناء بنجاح!"
echo "   الملف في: dist/نظام_إدارة_الموظفين"
echo "=================================================="
echo ""
echo "للتشغيل:"
echo "  ./dist/نظام_إدارة_الموظفين"
