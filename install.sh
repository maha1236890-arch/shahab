#!/usr/bin/env bash
# install.sh – مثبّت نظام الحضور والغياب على Linux
# الاستخدام: sudo bash install.sh
# ─────────────────────────────────────────────────────────────────────────

set -e

APP_NAME="attendance"
DISPLAY_NAME="نظام الحضور والغياب"
INSTALL_DIR="/opt/attendance_system"
BIN_LINK="/usr/local/bin/attendance"
DESKTOP_FILE="/usr/share/applications/attendance.desktop"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── التحقق من صلاحيات root ───────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo "❌  يجب تشغيل هذا المثبّت بصلاحيات root:"
    echo "    sudo bash install.sh"
    exit 1
fi

echo "══════════════════════════════════════════════════════"
echo "  🚀  تثبيت نظام الحضور والغياب"
echo "══════════════════════════════════════════════════════"
echo ""

# ── التحقق من وجود dist/attendance ───────────────────────────────────────
DIST_DIR="$SCRIPT_DIR/dist/attendance"
if [[ ! -f "$DIST_DIR/attendance" ]]; then
    echo "⚙️   لم يُبنَ التطبيق بعد — جارٍ البناء بـ PyInstaller..."
    echo ""

    # التحقق من وجود Python
    if ! command -v python3 &>/dev/null; then
        echo "❌  Python3 غير مثبّت. ثبّته أولاً:"
        echo "    sudo apt install python3 python3-pip"
        exit 1
    fi

    # تثبيت المتطلبات
    cd "$SCRIPT_DIR"
    echo "📦  تثبيت المتطلبات..."
    python3 -m pip install --quiet -r requirements.txt 2>/dev/null || \
        python3 -m pip install --quiet flask pyside6 pyinstaller openpyxl 2>/dev/null

    # البناء
    echo "🔨  جارٍ البناء (قد يستغرق بضع دقائق)..."
    python3 -m PyInstaller attendance.spec --noconfirm 2>&1 | tail -5

    if [[ ! -f "$DIST_DIR/attendance" ]]; then
        echo "❌  فشل البناء. راجع الأخطاء أعلاه."
        exit 1
    fi
    echo "✅  تم البناء بنجاح"
fi

# ── نسخ الملفات ──────────────────────────────────────────────────────────
echo "📂  نسخ التطبيق إلى $INSTALL_DIR ..."
rm -rf "$INSTALL_DIR"
cp -r "$DIST_DIR" "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/attendance"

# ── رابط تشغيل ──────────────────────────────────────────────────────────
echo "🔗  إنشاء رابط تشغيل في $BIN_LINK ..."
ln -sf "$INSTALL_DIR/attendance" "$BIN_LINK"

# ── ملف .desktop ─────────────────────────────────────────────────────────
echo "🖥️   إنشاء اختصار سطح المكتب..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=2.0
Type=Application
Name=نظام الحضور والغياب
Comment=نظام إدارة الحضور والغياب للموظفين
Exec=$INSTALL_DIR/attendance
Icon=$INSTALL_DIR/icon.png
Terminal=false
Categories=Office;Education;
Keywords=attendance;حضور;غياب;
StartupNotify=true
EOF

# محاولة نسخ الأيقونة إن وُجدت
if [[ -f "$SCRIPT_DIR/icon.png" ]]; then
    cp "$SCRIPT_DIR/icon.png" "$INSTALL_DIR/icon.png"
fi

chmod 644 "$DESKTOP_FILE"
update-desktop-database 2>/dev/null || true

# ── إنشاء مجلد البيانات ──────────────────────────────────────────────────
DATA_DIR="/var/lib/attendance_system"
mkdir -p "$DATA_DIR"
chmod 777 "$DATA_DIR"

echo ""
echo "══════════════════════════════════════════════════════"
echo "  ✅  اكتمل التثبيت بنجاح!"
echo "══════════════════════════════════════════════════════"
echo ""
echo "  ▶  لتشغيل البرنامج:"
echo "     $BIN_LINK"
echo "     أو ابحث عن 'نظام الحضور' في قائمة التطبيقات"
echo ""
echo "  📁  مسار التثبيت: $INSTALL_DIR"
echo "  🗄️   ملف البيانات: $DATA_DIR/attendance.db"
echo ""
