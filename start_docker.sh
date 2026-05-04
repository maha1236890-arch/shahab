#!/bin/bash
# تشغيل نظام الحضور والغياب عبر Docker
# يعمل على: Linux / macOS
# المتطلب الوحيد: تثبيت Docker

set -e

echo "================================================"
echo "  نظام الحضور والغياب – Docker"
echo "================================================"

# إنشاء مجلد البيانات إذا لم يكن موجوداً
mkdir -p data

# بناء وتشغيل الحاوية
docker compose up --build -d

echo ""
echo "✔ التطبيق يعمل الآن!"
echo "► افتح المتصفح على: http://localhost:5000"
echo "► بيانات الدخول الافتراضية: admin / admin123"
echo ""
echo "لإيقاف التطبيق: docker compose down"
