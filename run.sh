#!/bin/bash
# تشغيل نظام إدارة الموظفين
# Run Employee Management System

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if PyQt5 is installed
if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "جارٍ تثبيت المتطلبات..."
    pip3 install PyQt5 --quiet
fi

echo "جارٍ تشغيل النظام..."
python3 main.py
