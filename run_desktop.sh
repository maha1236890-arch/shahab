#!/usr/bin/env bash
# تشغيل تطبيق الحضور بواجهة رسومية سطح المكتب
cd "$(dirname "$0")"

# التحقق من وجود display (بيئة رسومية)
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "خطأ: لا توجد بيئة رسومية. استخدم python3 app.py للتشغيل عبر المتصفح."
    exit 1
fi

exec python3 desktop.py "$@"
