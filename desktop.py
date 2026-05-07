"""
desktop.py – تطبيق سطح المكتب لنظام الحضور والغياب
يشغّل Flask في خيط خلفي ويعرض التطبيق داخل نافذة PyQt5 WebEngine
يعمل بلا إنترنت على: Linux / Windows / macOS
"""

import os
import sys
import time
import socket
import logging
import threading

# ── مسار التطبيق (يعمل مع PyInstaller أيضاً) ────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS          # عند التجميع PyInstaller يضع الملفات هنا
    # DATA_DIR = مجلد قابل للكتابة (لا نكتب داخل Program Files)
    if sys.platform == "win32":
        DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Shahab")
    else:
        DATA_DIR = os.path.join(os.path.expanduser("~"), ".config", "shahab")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = BASE_DIR

os.makedirs(DATA_DIR, exist_ok=True)
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

# ── تهيئة ملف الأخطاء ───────────────────────────────────────────────────
_log_file = os.path.join(DATA_DIR, "error.log")
logging.basicConfig(
    filename=_log_file,
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)

# ── إخفاء console على Windows ────────────────────────────────────────────
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

# ── إعداد بيئة Qt قبل أي استيراد ─────────────────────────────────────────
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
if sys.platform == "linux":
    # دعم Wayland وX11
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        os.environ["DISPLAY"] = ":0"
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS",
                          "--disable-gpu --no-sandbox --disable-dev-shm-usage")
elif sys.platform == "win32":
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS",
                          "--disable-gpu")

from PySide6.QtCore    import Qt, QUrl, QTimer, QThread, Signal, QSize
from PySide6.QtGui     import QFont, QIcon, QAction, QPixmap
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                               QHBoxLayout, QWidget, QToolBar, QStatusBar,
                               QMessageBox, QSizePolicy, QFrame,
                               QDialog, QPushButton)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore    import QWebEngineSettings, QWebEngineProfile, QWebEnginePage
from PySide6.QtNetwork          import QNetworkProxy

# تعطيل proxy النظام لمنع مشاكل الاتصال بـ localhost
QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))

APP_NAME = "شهاب"
PRIMARY  = "#1976D2"


def _icon_path() -> str:
    """مسار الأيقونة — يعمل في وضع التطوير والتثبيت وPyInstaller"""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    # Windows يحتاج .ico للتعرف على الأيقونة بشكل صحيح
    if sys.platform == "win32":
        ico = os.path.join(base, "static", "img", "icon.ico")
        if os.path.exists(ico):
            return ico
    return os.path.join(base, "static", "img", "icon.png")


def _app_icon() -> QIcon:
    return QIcon(_icon_path())


# ══════════════════════════════════════════════════════════════════════════
# أداة: إيجاد منفذ حر تلقائياً
# ══════════════════════════════════════════════════════════════════════════
def find_free_port(start: int = 5555) -> int:
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("لا يوجد منفذ متاح!")


# ══════════════════════════════════════════════════════════════════════════
# 1. خيط تشغيل Flask
# ══════════════════════════════════════════════════════════════════════════
class FlaskThread(QThread):
    ready = Signal(str)      # يُرسل URL عند الجاهزية
    error = Signal(str)

    def __init__(self, port: int):
        super().__init__()
        self.port = port
        self.host = "127.0.0.1"
        self.url  = f"http://{self.host}:{self.port}"

    def run(self):
        try:
            import database as db
            from app import app
            db.init_db()

            # انتظار جاهزية المنفذ في خيط منفصل
            threading.Thread(target=self._wait_ready, daemon=True).start()

            from werkzeug.serving import make_server
            self._server = make_server(self.host, self.port, app)
            self._server.serve_forever()
        except Exception as e:
            logging.exception("فشل تشغيل Flask")
            self.error.emit(str(e))

    def stop(self):
        if hasattr(self, '_server'):
            self._server.shutdown()

    def _wait_ready(self):
        for _ in range(60):
            try:
                s = socket.create_connection((self.host, self.port), timeout=1)
                s.close()
                self.ready.emit(self.url)
                return
            except OSError:
                time.sleep(0.2)
        self.error.emit("انتهت مهلة الانتظار — لم يبدأ الخادم")


# ══════════════════════════════════════════════════════════════════════════
# 2. شاشة البداية
# ══════════════════════════════════════════════════════════════════════════
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 280)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 20px;
                border: 1px solid #e0e0e0;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(12)
        lay.setContentsMargins(36, 32, 36, 32)

        ico = QLabel()
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("border:none;")
        _px = QPixmap(_icon_path())
        if not _px.isNull():
            ico.setPixmap(_px.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        else:
            ico.setText("📋")
            ico.setStyleSheet("font-size:48px; border:none;")

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size:22px; font-weight:bold; color:{PRIMARY}; border:none;")

        self.status_lbl = QLabel("جارٍ تحميل التطبيق...")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("font-size:13px; color:#777; border:none;")

        # شريط تحميل متحرك
        from PySide6.QtWidgets import QProgressBar
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.setFixedHeight(6)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background:#eee; border-radius:3px; border:none; }}
            QProgressBar::chunk {{ background:{PRIMARY}; border-radius:3px; }}
        """)

        lay.addWidget(ico)
        lay.addWidget(title)
        lay.addWidget(self.status_lbl)
        lay.addSpacing(4)
        lay.addWidget(self.bar)
        outer.addWidget(card)

        self._center()

    def _center(self):
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.center().x() - self.width()//2,
                  geo.center().y() - self.height()//2)


    def set_status(self, text: str):
        self.status_lbl.setText(text)


# ══════════════════════════════════════════════════════════════════════════
# 3. صفحة ويب مخصصة — تعترض روابط التصدير وتنزّلها عبر Python
# ══════════════════════════════════════════════════════════════════════════
class _AttendancePage(QWebEnginePage):
    """تعترض روابط /reports/export/* و /backup/download/* وتنزّلها مباشرة"""

    _EXPORT_PATTERNS = (
        "/reports/export/excel",
        "/reports/export/pdf",
        "/backup/download/",
    )

    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self._cookies = {}
        store = profile.cookieStore()
        store.cookieAdded.connect(self._store_cookie)
        store.cookieRemoved.connect(self._remove_cookie)

    def _store_cookie(self, cookie):
        name  = bytes(cookie.name()).decode('utf-8', errors='replace')
        value = bytes(cookie.value()).decode('utf-8', errors='replace')
        self._cookies[name] = value

    def _remove_cookie(self, cookie):
        name = bytes(cookie.name()).decode('utf-8', errors='replace')
        self._cookies.pop(name, None)

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        path = url.path()
        if any(path.startswith(p) for p in self._EXPORT_PATTERNS):
            url_str = url.toString()
            QTimer.singleShot(0, lambda: self._download(url_str))
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def _show_error(self, title, msg):
        """يعرض الخطأ داخل صفحة الويب كـ alert مضمون الظهور"""
        safe = msg.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
        self.runJavaScript(f"alert('{title}\\n{safe}')")

    def _download(self, url_str):
        import urllib.request
        import urllib.error
        from PySide6.QtWidgets import QFileDialog

        cookie_header = "; ".join(f"{k}={v}" for k, v in self._cookies.items())

        try:
            req = urllib.request.Request(url_str)
            if cookie_header:
                req.add_header("Cookie", cookie_header)

            try:
                response = urllib.request.urlopen(req, timeout=30)
            except urllib.error.HTTPError as e:
                # خطأ من الخادم — اقرأ الرسالة وأظهرها
                body = e.read().decode('utf-8', errors='replace')
                import re
                text = re.sub(r'<[^>]+>', ' ', body).strip()[:300]
                self._show_error(f"خطأ {e.code} من الخادم", text)
                logging.error("HTTP %s for %s: %s", e.code, url_str, text)
                return
            except urllib.error.URLError as e:
                self._show_error("خطأ في الاتصال", str(e.reason))
                return

            with response as resp:
                if 'login' in (resp.url or ''):
                    self._show_error("انتهت الجلسة", "يرجى تسجيل الدخول من جديد")
                    return

                data = resp.read()

                # إذا رجع HTML بدل ملف — خطأ في الخادم
                ct = resp.headers.get("Content-Type", "")
                if "text/html" in ct:
                    import re
                    text = re.sub(r'<[^>]+>', ' ', data.decode('utf-8', 'replace')).strip()[:300]
                    self._show_error("خطأ في الخادم", text)
                    logging.error("HTML response for %s: %s", url_str, text)
                    return

                cd = resp.headers.get("Content-Disposition", "")
                suggested = ""
                if "filename=" in cd:
                    suggested = cd.split("filename=")[-1].strip().strip('"')
                if not suggested:
                    suggested = url_str.split("/")[-1].split("?")[0] or "file"

                ext = os.path.splitext(suggested)[1].lower()
                if ext == ".xlsx":
                    file_filter = "Excel Files (*.xlsx);;All Files (*)"
                elif ext == ".pdf":
                    file_filter = "PDF Files (*.pdf);;All Files (*)"
                elif ext == ".db":
                    file_filter = "Database Files (*.db);;All Files (*)"
                else:
                    file_filter = "All Files (*)"

                default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(default_dir, exist_ok=True)

                save_path, _ = QFileDialog.getSaveFileName(
                    None, "حفظ الملف",
                    os.path.join(default_dir, suggested),
                    file_filter
                )
                if save_path:
                    with open(save_path, "wb") as f:
                        f.write(data)

        except Exception as e:
            logging.error("_download error: %s", e, exc_info=True)
            self._show_error("خطأ غير متوقع", str(e))


# ══════════════════════════════════════════════════════════════════════════
# 4. النافذة الرئيسية
# ══════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self, app_url: str):
        super().__init__()
        self.app_url = app_url
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(_app_icon())
        self.resize(1280, 820)
        self._center()
        self._build_toolbar()
        self._build_webview()
        self._build_statusbar()

    def _center(self):
        geo = QApplication.primaryScreen().availableGeometry()
        fg  = self.frameGeometry()
        fg.moveCenter(geo.center())
        self.move(fg.topLeft())

    # ── شريط الأدوات ──────────────────────────────────────────────────
    def _build_toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))  # type: ignore
        tb.setStyleSheet(f"""
            QToolBar {{
                background: {PRIMARY};
                spacing: 4px;
                padding: 3px 10px;
                border: none;
            }}
            QToolButton {{
                color: white; border: none;
                padding: 5px 14px; border-radius: 6px;
                font-size: 13px;
            }}
            QToolButton:hover   {{ background: rgba(255,255,255,.18); }}
            QToolButton:pressed {{ background: rgba(255,255,255,.30); }}
        """)

        lbl = QLabel(f"  📋  {APP_NAME}  ")
        lbl.setStyleSheet("color:white; font-size:16px; font-weight:bold;")
        tb.addWidget(lbl)

        sp = QWidget()
        sp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(sp)

        nav = [
            ("🏠 الرئيسية",   "/dashboard"),
            ("👥 الموظفون",    "/employees"),
            ("📋 الحضور",     "/attendance"),
            ("📊 التقارير",    "/reports"),
            ("👤 المستخدمون", "/users"),
        ]
        for label, path in nav:
            a = QAction(label, self)
            a.triggered.connect(lambda _, p=path: self._nav(p))
            tb.addAction(a)

        tb.addSeparator()
        for label, slot in [("◀", self._back), ("▶", self._fwd), ("↺", self._reload)]:
            a = QAction(label, self)
            a.triggered.connect(slot)
            tb.addAction(a)

        self.addToolBar(tb)

    # ── WebView ────────────────────────────────────────────────────────
    def _build_webview(self):
        # مسح الكاش لضمان تحميل أحدث نسخة
        profile = QWebEngineProfile.defaultProfile()
        profile.clearHttpCache()
        profile.clearAllVisitedLinks()

        self.web = QWebEngineView()
        # استخدام صفحة مخصصة تعترض روابط التصدير
        page = _AttendancePage(profile, self.web)
        self.web.setPage(page)

        s = self.web.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)

        # معالج احتياطي للتنزيلات التي لا يعترضها _AttendancePage
        profile.downloadRequested.connect(self._on_download)

        self.web.setUrl(QUrl(self.app_url))
        self.web.loadStarted.connect(lambda: self.sb.showMessage("⌛ جارٍ التحميل..."))
        self.web.loadFinished.connect(
            lambda ok: self.sb.showMessage("✔ جاهز" if ok else "✗ خطأ في التحميل"))
        self.web.titleChanged.connect(
            lambda t: self.setWindowTitle(f"{t}  —  {APP_NAME}" if t else APP_NAME))

        self.setCentralWidget(self.web)

    # ── تنزيل الملفات ──────────────────────────────────────────────────
    def _on_download(self, item):
        from PySide6.QtWidgets import QFileDialog
        suggested = item.suggestedFileName() or "file"
        ext = os.path.splitext(suggested)[1].lower()

        if ext == ".db":
            file_filter = "Database Files (*.db);;All Files (*)"
        elif ext == ".xlsx":
            file_filter = "Excel Files (*.xlsx);;All Files (*)"
        elif ext == ".pdf":
            file_filter = "PDF Files (*.pdf);;All Files (*)"
        else:
            file_filter = "All Files (*)"

        if sys.platform == "win32":
            default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(default_dir, exist_ok=True)

        save_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ الملف",
            os.path.join(default_dir, suggested),
            file_filter
        )
        if save_path:
            item.setDownloadDirectory(os.path.dirname(save_path))
            item.setDownloadFileName(os.path.basename(save_path))
            item.accept()
            self.sb.showMessage(f"✔ جارٍ التنزيل: {os.path.basename(save_path)}")
        else:
            item.cancel()


    def _build_statusbar(self):
        self.sb = QStatusBar()
        self.sb.setStyleSheet("font-size:12px; color:#555;")
        self.setStatusBar(self.sb)
        self.sb.showMessage("✔ التطبيق جاهز — يعمل بدون إنترنت")

    # ── تنقل ──────────────────────────────────────────────────────────
    def _nav(self, path):  self.web.setUrl(QUrl(self.app_url + path))
    def _back(self):       self.web.back()
    def _fwd(self):        self.web.forward()
    def _reload(self):     self.web.reload()

    # ── إغلاق آمن ─────────────────────────────────────────────────────
    def closeEvent(self, ev):
        dlg = QDialog(self)
        dlg.setWindowTitle("إغلاق التطبيق")
        dlg.setFixedSize(360, 180)
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setStyleSheet("""
            QDialog {
                background: #ffffff;
                border-radius: 12px;
            }
            QLabel#title {
                font-size: 15px;
                font-weight: bold;
                color: #212121;
            }
            QLabel#sub {
                font-size: 12px;
                color: #757575;
            }
            QPushButton#yes {
                background: #e53935;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 24px;
            }
            QPushButton#yes:hover { background: #c62828; }
            QPushButton#no {
                background: #f5f5f5;
                color: #424242;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                padding: 8px 24px;
            }
            QPushButton#no:hover { background: #e0e0e0; }
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("هل تريد إغلاق التطبيق؟")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("سيتم إيقاف النظام وإغلاق جميع النوافذ")
        sub.setObjectName("sub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_no  = QPushButton("إلغاء")
        btn_no.setObjectName("no")
        btn_yes = QPushButton("إغلاق")
        btn_yes.setObjectName("yes")

        btn_row.addWidget(btn_no)
        btn_row.addWidget(btn_yes)

        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addSpacing(8)
        layout.addLayout(btn_row)

        btn_yes.clicked.connect(dlg.accept)
        btn_no.clicked.connect(dlg.reject)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            ev.accept()
            if hasattr(self, '_flask_thread') and self._flask_thread:
                self._flask_thread.stop()
                self._flask_thread.wait(3000)
            os._exit(0)
        else:
            ev.ignore()


# ══════════════════════════════════════════════════════════════════════════
# 4. نافذة الترخيص
# ══════════════════════════════════════════════════════════════════════════
class LicenseDialog(QWidget):
    """نافذة إدخال مفتاح الترخيص تظهر عند عدم وجود ترخيص صالح"""
    activated = Signal()
    rejected  = Signal()

    def __init__(self, status: dict, parent=None):
        super().__init__(parent)
        self.status = status
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(500, 340)
        self.setWindowTitle("تفعيل الترخيص")
        self._build_ui()
        self._center()

    def _center(self):
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.center().x() - self.width()//2,
                  geo.center().y() - self.height()//2)

    def _build_ui(self):
        from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLineEdit,
                                        QPushButton, QTextEdit)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 25, 30, 25)
        lay.setSpacing(14)

        icon = QLabel("🔑")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size:42px;")

        title = QLabel("تفعيل شهاب")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size:18px; font-weight:bold; color:{PRIMARY};")

        reason = self.status.get("reason", "")
        if reason:
            reason_lbl = QLabel(f"⚠️  {reason}")
            reason_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            reason_lbl.setStyleSheet("color:#c0392b; font-size:13px;")
        else:
            reason_lbl = QLabel("")

        from PySide6.QtWidgets import QLineEdit
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("أدخل مفتاح الترخيص  XXXXXX-XXXXXX-...")
        self.key_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_input.setStyleSheet("""
            QLineEdit {
                font-size:13px; padding:10px;
                border:2px solid #ccc; border-radius:8px;
            }
            QLineEdit:focus { border-color:#1976D2; }
        """)
        self.key_input.setMinimumHeight(44)

        self.msg_lbl = QLabel("")
        self.msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_lbl.setStyleSheet("font-size:13px;")

        btn_activate = QPushButton("تفعيل")
        btn_activate.setMinimumHeight(42)
        btn_activate.setStyleSheet(f"""
            QPushButton {{
                background:{PRIMARY}; color:white;
                font-size:14px; font-weight:bold;
                border-radius:8px; border:none;
            }}
            QPushButton:hover {{ background:#1565C0; }}
        """)
        btn_activate.clicked.connect(self._activate)

        btn_exit = QPushButton("إنهاء البرنامج")
        btn_exit.setMinimumHeight(42)
        btn_exit.setStyleSheet("""
            QPushButton {
                background:#e0e0e0; color:#333;
                font-size:13px; border-radius:8px; border:none;
            }
            QPushButton:hover { background:#bdbdbd; }
        """)
        btn_exit.clicked.connect(self._exit_app)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_activate)
        btn_row.addWidget(btn_exit)

        lay.addWidget(icon)
        lay.addWidget(title)
        lay.addWidget(reason_lbl)
        lay.addWidget(self.key_input)
        lay.addWidget(self.msg_lbl)
        lay.addLayout(btn_row)

    def _activate(self):
        key = self.key_input.text().strip()
        if not key:
            self.msg_lbl.setText("⚠️  يرجى إدخال مفتاح الترخيص")
            self.msg_lbl.setStyleSheet("color:#c0392b; font-size:13px;")
            return
        import license as lic
        result = lic.save_license(key)
        if result["valid"]:
            self.msg_lbl.setText(f"✅  تم التفعيل — {result.get('customer','')}")
            self.msg_lbl.setStyleSheet("color:#27ae60; font-size:13px;")
            QTimer.singleShot(1200, self._on_activated)
        else:
            self.msg_lbl.setText(f"❌  {result.get('reason','مفتاح غير صالح')}")
            self.msg_lbl.setStyleSheet("color:#c0392b; font-size:13px;")

    def _on_activated(self):
        self.close()
        self.activated.emit()

    def _exit_app(self):
        self.rejected.emit()
        QApplication.quit()


# ══════════════════════════════════════════════════════════════════════════
# 5. نقطة الدخول
# ══════════════════════════════════════════════════════════════════════════
def main():
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("shahab")

    # ── تعيين مسار قاعدة البيانات في مجلد قابل للكتابة ─────────────────
    # (Program Files ممنوع الكتابة على ويندوز)
    if "DB_PATH" not in os.environ:
        os.environ["DB_PATH"] = os.path.join(DATA_DIR, "attendance.db")
    qapp.setApplicationDisplayName(APP_NAME)
    qapp.setOrganizationName("MGG Software")
    if sys.platform == "linux":
        qapp.setDesktopFileName("shahab")
    qapp.setWindowIcon(_app_icon())
    qapp.setStyle("Fusion")

    # خط التطبيق — Cairo على Linux/macOS، Segoe UI على Windows
    if sys.platform == "win32":
        font = QFont("Segoe UI", 10)
    else:
        font = QFont("Cairo", 10)
    qapp.setFont(font)

    # ── فحص الترخيص ───────────────────────────────────────────────────
    # يجب تهيئة قاعدة البيانات أولاً حتى نتمكن من قراءة الترخيص
    try:
        import database as _db_pre
        _db_pre.init_db()
    except Exception:
        logging.exception("فشل تهيئة قاعدة البيانات")

    import license as _lic
    lic_status = _lic.get_license_status()

    # إذا لم يكن الترخيص صالحاً: اعرض نافذة التفعيل
    if not lic_status.get("valid", False):
        lic_dialog = LicenseDialog(lic_status)
        _continue = [False]

        def on_activated():
            _continue[0] = True
            lic_dialog.close()

        lic_dialog.activated.connect(on_activated)
        lic_dialog.show()
        qapp.exec()

        if not _continue[0]:
            return  # المستخدم أغلق البرنامج

        # إعادة تشغيل qapp بعد إغلاق نافذة الترخيص
        qapp = QApplication.instance() or QApplication(sys.argv)
        qapp.setStyle("Fusion")
        qapp.setFont(QFont("Cairo", 10))

    # تحذير قرب الانتهاء (أقل من 14 يوم)
    days_left = lic_status.get("days_left", 99999)
    if lic_status.get("valid") and days_left < 14:
        QMessageBox.warning(None, "تنبيه الترخيص",
            f"⚠️  ينتهي الترخيص خلال {days_left} يوم.\n"
            "يرجى التواصل مع المورّد لتجديد الترخيص.")

    # ── شاشة البداية ──
    splash = SplashScreen()
    splash.show()
    qapp.processEvents()

    # ── إيجاد منفذ حر ──
    port = find_free_port(5555)
    splash.set_status(f"جارٍ تشغيل الخادم على المنفذ {port}...")
    qapp.processEvents()

    # ── تشغيل Flask ──
    flask_t = FlaskThread(port)
    win = [None]

    def on_ready(url):
        splash.set_status("✔ جاهز — جارٍ فتح النافذة")
        qapp.processEvents()
        def show():
            splash.close()
            win[0] = MainWindow(url)
            win[0]._flask_thread = flask_t
            win[0].show()
        QTimer.singleShot(200, show)

    def on_error(msg):
        logging.error(f"فشل تشغيل Flask: {msg}")
        splash.close()
        QMessageBox.critical(None, "خطأ", f"فشل تشغيل التطبيق:\n{msg}")
        qapp.quit()

    flask_t.ready.connect(on_ready)
    flask_t.error.connect(on_error)
    flask_t.start()

    sys.exit(qapp.exec())


if __name__ == "__main__":
    main()
