#!/usr/bin/env bash
# build_deb.sh – يبني حزمة .deb لتوزيع نظام الحضور والغياب على Ubuntu/Debian
# الاستخدام: bash build_deb.sh
# ─────────────────────────────────────────────────────────────────────────

set -e

APP="attendance-system"
VERSION="2.0.0"
ARCH="amd64"
MAINTAINER="مجموعة الأنظمة المتكاملة <support@example.com>"
DESCRIPTION="شهاب — نظام متكامل لإدارة حضور الموظفين"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist/attendance"
PKG_DIR="$SCRIPT_DIR/pkg_build/${APP}_${VERSION}_${ARCH}"
DEB_FILE="$SCRIPT_DIR/${APP}_${VERSION}_${ARCH}.deb"

echo "══════════════════════════════════════════════════════"
echo "  📦  بناء حزمة .deb — نظام الحضور والغياب v$VERSION"
echo "══════════════════════════════════════════════════════"
echo ""

# ── التحقق من dist/attendance ─────────────────────────────────────────────
if [[ ! -f "$DIST_DIR/attendance" ]]; then
    echo "❌  لم يُبنَ التطبيق. شغّل PyInstaller أولاً:"
    echo "    python3 -m PyInstaller attendance.spec --noconfirm"
    exit 1
fi

# ── هيكل الحزمة ──────────────────────────────────────────────────────────
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/attendance_system"
mkdir -p "$PKG_DIR/usr/local/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/512x512/apps"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$PKG_DIR/var/lib/attendance_system"

# ── نسخ الملفات ──────────────────────────────────────────────────────────
echo "📂  نسخ ملفات التطبيق..."
cp -r "$DIST_DIR/." "$PKG_DIR/opt/attendance_system/"
chmod +x "$PKG_DIR/opt/attendance_system/attendance"

# تثبيت الأيقونة في مجلدات النظام الصحيحة
ICON_SRC="$SCRIPT_DIR/static/img/icon.png"
if command -v convert &>/dev/null; then
    convert "$ICON_SRC" -resize 512x512 "$PKG_DIR/usr/share/icons/hicolor/512x512/apps/shahab.png" 2>/dev/null
    convert "$ICON_SRC" -resize 256x256 "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/shahab.png" 2>/dev/null
    convert "$ICON_SRC" -resize 128x128 "$PKG_DIR/usr/share/icons/hicolor/128x128/apps/shahab.png" 2>/dev/null
else
    cp "$ICON_SRC" "$PKG_DIR/usr/share/icons/hicolor/512x512/apps/shahab.png"
    cp "$ICON_SRC" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/shahab.png"
    cp "$ICON_SRC" "$PKG_DIR/usr/share/icons/hicolor/128x128/apps/shahab.png"
fi

# رابط تشغيل
ln -sf /opt/attendance_system/attendance \
    "$PKG_DIR/usr/local/bin/attendance"

# ── ملف .desktop ─────────────────────────────────────────────────────────
cat > "$PKG_DIR/usr/share/applications/shahab.desktop" << EOF
[Desktop Entry]
Version=2.0
Type=Application
Name=شهاب
Name[ar]=شهاب
GenericName=نظام الحضور والغياب
Comment=نظام إدارة الحضور والغياب للموظفين
Exec=/opt/attendance_system/attendance
Icon=shahab
Terminal=false
Categories=Office;Education;
Keywords=attendance;حضور;غياب;موظفين;شهاب;
StartupNotify=true
StartupWMClass=shahab
EOF

# ── DEBIAN/control ───────────────────────────────────────────────────────
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: $APP
Version: $VERSION
Architecture: $ARCH
Maintainer: $MAINTAINER
Description: $DESCRIPTION
 نظام كامل لإدارة حضور وغياب الموظفين
 يعمل بدون إنترنت على Linux (Ubuntu/Debian)
 .
 المميزات:
  - واجهة ويب عربية (RTL)
  - تقارير Excel/PDF
  - نسخ احتياطي تلقائي
  - نظام ترخيص محمي
Depends: libglib2.0-0, libxcb1, libdbus-1-3
Installed-Size: $(du -s "$PKG_DIR/opt" | cut -f1)
EOF

# ── DEBIAN/postinst ───────────────────────────────────────────────────────
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
chmod 777 /var/lib/attendance_system 2>/dev/null || true
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
echo "✅  تم تثبيت شهاب بنجاح!"
echo "   ▶  شغل التطبيق: attendance"
echo "   ▶  أو ابحث عن (شهاب) في قائمة التطبيقات"
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# ── DEBIAN/prerm ──────────────────────────────────────────────────────────
cat > "$PKG_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
echo "🗑️   جارٍ إزالة شهاب..."
rm -f /usr/share/icons/hicolor/512x512/apps/shahab.png
rm -f /usr/share/icons/hicolor/256x256/apps/shahab.png
rm -f /usr/share/icons/hicolor/128x128/apps/shahab.png
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
EOF
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# ── بناء الحزمة ──────────────────────────────────────────────────────────
echo "🔨  بناء الحزمة..."
dpkg-deb --build "$PKG_DIR" "$DEB_FILE"

echo ""
echo "══════════════════════════════════════════════════════"
echo "  ✅  تم إنشاء الحزمة بنجاح!"
echo "══════════════════════════════════════════════════════"
echo ""
echo "  الملف: $DEB_FILE"
echo "  الحجم: $(du -sh "$DEB_FILE" | cut -f1)"
echo ""
echo "  لتثبيتها:"
echo "    sudo dpkg -i $DEB_FILE"
echo "    sudo apt-get install -f  # لإصلاح التبعيات إن لزم"
echo ""

# تنظيف
rm -rf "$SCRIPT_DIR/pkg_build"
