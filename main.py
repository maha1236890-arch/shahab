"""
نظام إدارة الموظفين - النافذة الرئيسية
Employee Management System - Main Window
"""

import sys
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QFrame, QStatusBar, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from styles import get_stylesheet
from tabs.dashboard_tab import DashboardTab
from tabs.employees_tab import EmployeesTab
from tabs.attendance_tab import AttendanceTab
from tabs.present_tab import PresentTab
from tabs.search_tab import SearchTab
from tabs.nutrition_tab import NutritionTab
from tabs.visits_tab import VisitsTab
from tabs.qat_tab import QatTab
from tabs.departments_tab import DepartmentsTab
from tabs.reports_tab import ReportsTab
from tabs.users_tab import UsersTab
from login_dialog import LoginDialog


DAYS_AR = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']

TOAST_ICONS = {
    'success': '✅',
    'error':   '❌',
    'warning': '⚠️',
    'info':    'ℹ️',
}
TOAST_COLORS = {
    'success': '#3fb950',
    'error':   '#f85149',
    'warning': '#e3b341',
    'info':    '#58a6ff',
}


class ToastNotification(QFrame):
    """إشعار منبثق يختفي تلقائياً"""

    def __init__(self, parent, message, toast_type='success'):
        super().__init__(parent)
        self.setObjectName(f'toast_{toast_type}')
        self.setFixedWidth(360)
        self.setFixedHeight(62)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        color = TOAST_COLORS.get(toast_type, '#58a6ff')
        icon  = TOAST_ICONS.get(toast_type, 'ℹ️')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet('font-size: 22px; background: transparent;')
        icon_lbl.setFixedWidth(28)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            f'font-size: 13px; color: {color}; background: transparent; font-weight: bold;'
        )
        msg_lbl.setWordWrap(True)

        layout.addWidget(icon_lbl)
        layout.addWidget(msg_lbl, 1)

        # Opacity animation for fade-out
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

        self._fade = QPropertyAnimation(self._opacity, b'opacity')
        self._fade.setDuration(600)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.setEasingCurve(QEasingCurve.OutQuad)
        self._fade.finished.connect(self.deleteLater)

        # Auto-dismiss after 2.8 seconds
        QTimer.singleShot(2800, self._fade.start)


class MainWindow(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.db = Database()
        self.current_user = current_user
        self.setWindowTitle('نظام إدارة الموظفين')
        self.setMinimumSize(1280, 800)
        self.setLayoutDirection(Qt.RightToLeft)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)

        # Header
        main_layout.addWidget(self._build_header())

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        main_layout.addWidget(self.tab_widget)

        # Build and add tabs
        self._build_tabs()

        # Status bar
        self._build_statusbar()

        # Clock timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_clock)
        self.timer.start(1000)

        # Tab badge update timer (every 60 s)
        self._badge_timer = QTimer()
        self._badge_timer.timeout.connect(self._update_badges)
        self._badge_timer.start(60000)
        self._update_badges()

        # Tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    # ─────────────────────────────────────────────
    def _build_header(self):
        frame = QFrame()
        frame.setObjectName('header_frame')
        frame.setFixedHeight(68)
        frame.setStyleSheet('''
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #161b22, stop:0.5 #1a2332, stop:1 #161b22);
                border-bottom: 2px solid #1f6feb;
                border-radius: 0;
            }
        ''')

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Logo
        logo = QLabel('🏢')
        logo.setStyleSheet('font-size: 36px; background: transparent;')

        # System name
        sys_name = QLabel('نظام إدارة الموظفين')
        sys_name.setStyleSheet(
            'font-size: 22px; font-weight: bold; color: #58a6ff;'
            'background: transparent; letter-spacing: 1px;'
        )
        sys_name.setAlignment(Qt.AlignCenter)

        # Version
        version = QLabel('v3.0')
        version.setStyleSheet('font-size: 11px; color: #484f58; background: transparent;')

        # Clock
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(
            'font-size: 14px; color: #3fb950; font-weight: bold; background: transparent;'
        )
        self.clock_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._update_clock()

        layout.addWidget(logo)
        layout.addWidget(sys_name, 1)
        layout.addWidget(version)
        layout.addWidget(QLabel('|'))
        layout.addWidget(self.clock_label)
        layout.addWidget(QLabel('|'))

        # Role badge
        role_labels = {
            'admin': ('مدير النظام', '#f0883e'),
            'attendance': ('مسؤول الحضور', '#58a6ff'),
            'data_entry': ('إدخال بيانات', '#3fb950'),
            'viewer': ('مشاهد', '#8b949e'),
        }
        role_text, role_color = role_labels.get(
            self.current_user.get('role', ''), ('مستخدم', '#8b949e')
        )
        role_lbl = QLabel(role_text)
        role_lbl.setStyleSheet(
            f'font-size: 11px; color: {role_color}; background: transparent; font-weight: bold;'
        )

        user_lbl = QLabel(f'👤 {self.current_user.get("full_name", self.current_user.get("username",""))}')
        user_lbl.setStyleSheet('font-size: 13px; color: #c9d1d9; background: transparent;')

        from PyQt5.QtWidgets import QPushButton
        logout_btn = QPushButton('🚪 خروج')
        logout_btn.setFixedHeight(32)
        logout_btn.setStyleSheet('''
            QPushButton {
                background: #21262d; color: #f85149; border: 1px solid #f85149;
                border-radius: 6px; padding: 2px 12px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #2d0f0f; }
        ''')
        logout_btn.clicked.connect(self._logout)

        layout.addWidget(role_lbl)
        layout.addWidget(user_lbl)
        layout.addWidget(logout_btn)

        return frame

    def _logout(self):
        self.db.log_action(self.current_user['id'], self.current_user['username'],
                           'تسجيل خروج', '')
        QApplication.instance().setProperty('logout_requested', True)
        self.close()

    def _update_clock(self):
        now = datetime.now()
        day = DAYS_AR[now.weekday()]
        self.clock_label.setText(
            f'  {day}  {now.strftime("%Y/%m/%d")}  {now.strftime("%H:%M:%S")}  '
        )

    def _build_tabs(self):
        role = self.current_user.get('role', 'data_entry')

        self.dashboard_tab  = DashboardTab(self.db)
        self.employees_tab  = EmployeesTab(self.db)
        self.attendance_tab = AttendanceTab(self.db)
        self.present_tab    = PresentTab(self.db)
        self.search_tab     = SearchTab(self.db)
        self.nutrition_tab  = NutritionTab(self.db)
        self.visits_tab     = VisitsTab(self.db)
        self.qat_tab        = QatTab(self.db)
        self.departments_tab = DepartmentsTab(self.db)
        self.reports_tab    = ReportsTab(self.db)
        self.users_tab      = UsersTab(self.db, self.current_user)

        # Connect dashboard "quick action" click → switch tab
        self.dashboard_tab.switch_to_tab.connect(self.tab_widget.setCurrentIndex)

        # Tabs visible per role:
        # admin:       all tabs
        # attendance:  dashboard, attendance, present, search, reports
        # data_entry:  dashboard, employees, attendance, search, nutrition, visits, qat
        # viewer:      dashboard, search, reports
        all_tabs = [
            (self.dashboard_tab,   '🏠  الرئيسية',  ['admin', 'attendance', 'data_entry', 'viewer']),
            (self.employees_tab,   '👥  الموظفون',   ['admin', 'data_entry']),
            (self.attendance_tab,  '📋  الحضور',     ['admin', 'attendance', 'data_entry']),
            (self.present_tab,     '✅  الحاضرون',   ['admin', 'attendance']),
            (self.search_tab,      '🔍  البحث',      ['admin', 'attendance', 'data_entry', 'viewer']),
            (self.nutrition_tab,   '🍽  التغذية',    ['admin', 'data_entry']),
            (self.visits_tab,      '🚪  الزيارات',   ['admin', 'data_entry']),
            (self.qat_tab,         '🌿  القات',      ['admin', 'data_entry']),
            (self.departments_tab, '🏢  الأقسام',    ['admin']),
            (self.reports_tab,     '📊  التقارير',   ['admin', 'attendance', 'viewer']),
            (self.users_tab,       '⚙️  المستخدمون', ['admin']),
        ]

        self._tabs = []
        for widget, label, allowed_roles in all_tabs:
            if role in allowed_roles:
                self.tab_widget.addTab(widget, label)
                self._tabs.append((widget, label))

        # Store tab index mapping for badge updates
        self._tab_index = {}
        for i, (widget, _) in enumerate(self._tabs):
            self._tab_index[type(widget).__name__] = i

    def _build_statusbar(self):
        status = self.statusBar()
        status.showMessage(
            '  ✅ النظام جاهز  |  نظام إدارة الموظفين v3.0  |  '
            f'قاعدة البيانات: {Database.get_instance().db_path}  '
        )

    def _on_tab_changed(self, index):
        widget = self.tab_widget.widget(index)
        if hasattr(widget, 'refresh'):
            widget.refresh()
        # Update badges when switching to attendance or visits
        att_idx = self._tab_index.get('AttendanceTab', -1)
        vis_idx = self._tab_index.get('VisitsTab', -1)
        if index in (att_idx, vis_idx):
            self._update_badges()

    def _update_badges(self):
        """تحديث شارات التبويبات بأعداد المهام المعلقة"""
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        try:
            all_emps = self.db.get_all_employees()
            total = len(all_emps)
            from database import Database as _DB
            summary = self.db.get_daily_summary(today)
            present = summary.get('present', 0)
            absent  = summary.get('absent', 0)
            unrecorded = max(0, total - present - absent)
            open_visits = self.db.get_open_visits(today)
            n_open = len(open_visits)

            # Attendance tab badge
            att_idx = self._tab_index.get('AttendanceTab', -1)
            if att_idx >= 0:
                att_label = f'📋  الحضور ({unrecorded})' if unrecorded > 0 else '📋  الحضور'
                self.tab_widget.setTabText(att_idx, att_label)

            # Visits tab badge
            vis_idx = self._tab_index.get('VisitsTab', -1)
            if vis_idx >= 0:
                vis_label = f'🚪  الزيارات ({n_open})' if n_open > 0 else '🚪  الزيارات'
                self.tab_widget.setTabText(vis_idx, vis_label)
        except Exception:
            pass

    # ─── Public API: show toast from anywhere ────
    def show_toast(self, message, toast_type='success'):
        """أظهر إشعار منبثق لثلاث ثوانٍ"""
        toast = ToastNotification(self, message, toast_type)
        # Position at bottom-right corner
        margin = 16
        x = self.width()  - toast.width()  - margin
        y = self.height() - toast.height() - margin - 30
        toast.move(x, y)
        toast.show()
        toast.raise_()


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyleSheet(get_stylesheet())

    # Set Arabic-compatible font
    font = QFont()
    font.setFamilies(['Tahoma', 'Arial', 'sans-serif'])
    font.setPointSize(11)
    app.setFont(font)

    db = Database.get_instance()

    while True:
        app.setProperty('logout_requested', False)
        login = LoginDialog(db)
        login.exec_()
        if login.current_user is None:
            # User closed login dialog without logging in
            break
        window = MainWindow(login.current_user)
        window.showMaximized()
        window.show()
        app.exec_()
        if not app.property('logout_requested'):
            break


if __name__ == '__main__':
    main()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
