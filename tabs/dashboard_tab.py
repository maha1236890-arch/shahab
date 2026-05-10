"""
لوحة التحكم الذكية - Smart Dashboard Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QColor
from datetime import datetime, date

DAYS_AR = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']

# Tab indices (dashboard=0, so all tabs shift by 1)
TAB_EMPLOYEES   = 1
TAB_ATTENDANCE  = 2
TAB_PRESENT     = 3
TAB_SEARCH      = 4
TAB_NUTRITION   = 5
TAB_VISITS      = 6
TAB_QAT         = 7
TAB_DEPARTMENTS = 8
TAB_REPORTS     = 9


def _rgba(hex_color: str, alpha: int) -> str:
    """Convert #RRGGBB + alpha 0-255 to rgba() string for QSS"""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


class AnimatedStatCard(QFrame):
    """بطاقة إحصاء تفاعلية مع تأثيرات hover"""
    clicked = pyqtSignal()

    def __init__(self, icon, title, value=0, color='#1f6feb', subtitle=''):
        super().__init__()
        self.color = color
        self._hovered = False
        self.setObjectName('anim_stat_card')
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(120)
        self.setMinimumWidth(170)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Glow shadow
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(color + '66'))
        self.shadow.setOffset(0, 3)
        self.setGraphicsEffect(self.shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        # Top: icon + title
        top = QHBoxLayout()
        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setStyleSheet(
            f'font-size: 22px; background: transparent; color: {color};'
        )
        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            'font-size: 12px; color: #8b949e; background: transparent; font-weight: 500;'
        )
        top.addWidget(self._icon_lbl)
        top.addWidget(self._title_lbl, 1)
        layout.addLayout(top)

        # Value (large)
        self.value_lbl = QLabel(str(value))
        self.value_lbl.setAlignment(Qt.AlignCenter)
        self.value_lbl.setStyleSheet(
            f'font-size: 40px; font-weight: bold; color: {color}; background: transparent;'
        )
        layout.addWidget(self.value_lbl)

        # Subtitle
        if subtitle:
            sub = QLabel(subtitle)
            sub.setAlignment(Qt.AlignCenter)
            sub.setStyleSheet('font-size: 10px; color: #484f58; background: transparent;')
            layout.addWidget(sub)

        self._apply_style(False)

    def _apply_style(self, hovered):
        border_rgba = _rgba(self.color, 200 if hovered else 68)
        bg = '#1a1f2e' if hovered else '#161b22'
        self.setStyleSheet(f'''
            QFrame#anim_stat_card {{
                background: {bg};
                border: 1px solid {border_rgba};
                border-radius: 12px;
            }}
        ''')
        if hovered:
            self.shadow.setBlurRadius(25)
            self.shadow.setColor(QColor(self.color))
            self.shadow.color().setAlpha(153)
        else:
            self.shadow.setBlurRadius(15)
            self.shadow.setColor(QColor(self.color))
            self.shadow.color().setAlpha(68)

    def update_value(self, value):
        self.value_lbl.setText(str(value))

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class AlertItem(QFrame):
    """عنصر تنبيه ملون"""
    def __init__(self, text, alert_type='warning'):
        super().__init__()
        STYLES = {
            'warning': ('#e3b341', '#1f1800', '⚠️'),
            'error':   ('#f85149', '#1f0000', '🔴'),
            'info':    ('#58a6ff', '#001a2a', 'ℹ️'),
            'success': ('#3fb950', '#001a00', '✅'),
        }
        color, bg, icon = STYLES.get(alert_type, STYLES['warning'])
        border_light = _rgba(color, 51)
        self.setStyleSheet(f'''
            QFrame {{
                background: {bg};
                border: 1px solid {border_light};
                border-right: 3px solid {color};
                border-radius: 6px;
            }}
        ''')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet('background: transparent; font-size: 15px;')
        icon_lbl.setFixedWidth(22)

        text_lbl = QLabel(text)
        text_lbl.setStyleSheet(f'background: transparent; color: {color}; font-size: 12px;')
        text_lbl.setWordWrap(True)

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl, 1)


class QuickActionBtn(QPushButton):
    """زر إجراء سريع بتصميم بطاقة"""
    def __init__(self, icon, title, description, color):
        super().__init__()
        self.color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(78)
        self.setMinimumWidth(160)

        inner = QVBoxLayout(self)
        inner.setContentsMargins(10, 8, 10, 8)
        inner.setSpacing(2)

        top_lbl = QLabel(f'{icon}  {title}')
        top_lbl.setStyleSheet(
            f'color: {color}; font-size: 13px; font-weight: bold; background: transparent;'
        )
        top_lbl.setAlignment(Qt.AlignCenter)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet('color: #6e7681; font-size: 10px; background: transparent;')
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)

        inner.addWidget(top_lbl)
        inner.addWidget(desc_lbl)

        self._apply_style(False)

    def _apply_style(self, hovered):
        if hovered:
            bg_rgba     = _rgba(self.color, 30)
            border_rgba = _rgba(self.color, 170)
            self.setStyleSheet(f'''
                QPushButton {{
                    background: {bg_rgba};
                    border: 1px solid {border_rgba};
                    border-radius: 10px;
                }}
            ''')
        else:
            border_rgba = _rgba(self.color, 51)
            self.setStyleSheet(f'''
                QPushButton {{
                    background: #161b22;
                    border: 1px solid {border_rgba};
                    border-radius: 10px;
                }}
            ''')

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)


class DashboardTab(QWidget):
    """لوحة التحكم الذكية الرئيسية"""
    switch_to_tab = pyqtSignal(int)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()

        # Clock: updates every second
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)

        # Auto-refresh every 30 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh_stats)
        self._refresh_timer.start(30000)

        self.refresh_stats()

    # ─────────────────────────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        root.addWidget(self._build_header())
        root.addLayout(self._build_stat_cards())

        body = QHBoxLayout()
        body.setSpacing(10)
        body.addWidget(self._build_alerts_panel(), 4)
        body.addWidget(self._build_quick_actions(), 6)
        root.addLayout(body, 1)

    # ─── Header ──────────────────────────────────
    def _build_header(self):
        frame = QFrame()
        frame.setFixedHeight(72)
        frame.setStyleSheet('''
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0d1117, stop:0.35 #162032, stop:0.65 #162032, stop:1 #0d1117);
                border: 1px solid rgba(31,111,235,68);
                border-radius: 12px;
            }
        ''')
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 8, 20, 8)

        # Left: welcome + date
        left = QVBoxLayout()
        welcome = QLabel('🏢  نظام إدارة الموظفين')
        welcome.setStyleSheet(
            'font-size: 19px; font-weight: bold; color: #e6edf3; background: transparent;'
        )
        today_obj = date.today()
        day_name = DAYS_AR[today_obj.weekday()]
        date_str = today_obj.strftime('%Y/%m/%d')
        self._date_lbl = QLabel(f'📅  {day_name}، {date_str}')
        self._date_lbl.setStyleSheet(
            'font-size: 12px; color: #8b949e; background: transparent;'
        )
        left.addWidget(welcome)
        left.addWidget(self._date_lbl)
        layout.addLayout(left, 1)

        # Right: live clock
        self._clock_lbl = QLabel()
        self._clock_lbl.setStyleSheet(
            'font-size: 30px; font-weight: bold; color: #1f6feb;'
            'background: transparent; letter-spacing: 2px; font-family: monospace;'
        )
        self._clock_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._tick_clock()
        layout.addWidget(self._clock_lbl)

        return frame

    # ─── Stat Cards Row ──────────────────────────
    def _build_stat_cards(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        self._card_present    = AnimatedStatCard('✅', 'الحاضرون اليوم',    0, '#3fb950')
        self._card_absent     = AnimatedStatCard('❌', 'الغائبون اليوم',    0, '#f85149')
        self._card_total      = AnimatedStatCard('👥', 'إجمالي الموظفين',  0, '#58a6ff')
        self._card_visits     = AnimatedStatCard('🚪', 'الزيارات اليوم',   0, '#8250df')
        self._card_unrecorded = AnimatedStatCard('⏳', 'غير مسجلين',        0, '#e3b341', 'يحتاجون تسجيل')

        self._card_present.clicked.connect(lambda: self.switch_to_tab.emit(TAB_PRESENT))
        self._card_absent.clicked.connect(lambda: self.switch_to_tab.emit(TAB_ATTENDANCE))
        self._card_unrecorded.clicked.connect(lambda: self.switch_to_tab.emit(TAB_ATTENDANCE))
        self._card_visits.clicked.connect(lambda: self.switch_to_tab.emit(TAB_VISITS))
        self._card_total.clicked.connect(lambda: self.switch_to_tab.emit(TAB_EMPLOYEES))

        for card in [self._card_present, self._card_absent, self._card_total,
                     self._card_visits, self._card_unrecorded]:
            row.addWidget(card)

        return row

    # ─── Alerts Panel ────────────────────────────
    def _build_alerts_panel(self):
        frame = QFrame()
        frame.setObjectName('card')
        frame.setStyleSheet('''
            QFrame#card {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
            }
        ''')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        hdr = QHBoxLayout()
        title = QLabel('🔔  التنبيهات')
        title.setStyleSheet(
            'font-size: 14px; font-weight: bold; color: #e3b341; background: transparent;'
        )
        refresh_btn = QPushButton('🔄')
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setObjectName('secondary')
        refresh_btn.setToolTip('تحديث الآن')
        refresh_btn.clicked.connect(self.refresh_stats)

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(refresh_btn)
        layout.addLayout(hdr)

        # Scroll area for alerts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet('background: transparent;')

        self._alerts_content = QWidget()
        self._alerts_content.setStyleSheet('background: transparent;')
        self._alerts_layout = QVBoxLayout(self._alerts_content)
        self._alerts_layout.setSpacing(6)
        self._alerts_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self._alerts_content)
        layout.addWidget(scroll, 1)

        return frame

    # ─── Quick Actions ────────────────────────────
    def _build_quick_actions(self):
        frame = QFrame()
        frame.setObjectName('card')
        frame.setStyleSheet('''
            QFrame#card {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
            }
        ''')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(8)

        title = QLabel('⚡  الإجراءات السريعة')
        title.setStyleSheet(
            'font-size: 14px; font-weight: bold; color: #58a6ff; background: transparent;'
        )
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(8)

        ACTIONS = [
            ('📋', 'تسجيل الحضور',   'تسجيل الحضور والغياب',       '#3fb950', TAB_ATTENDANCE),
            ('✅', 'الحاضرون الآن',   'عرض الحاضرين بالأقسام',      '#58a6ff', TAB_PRESENT),
            ('🚪', 'دخول / خروج',     'إصدار تصريح الزيارة',         '#8250df', TAB_VISITS),
            ('🔍', 'بحث موظف',         'البحث بالكود',                '#e3b341', TAB_SEARCH),
            ('🌿', 'توزيع القات',      'تسجيل توزيع القات اليومي',   '#3fb950', TAB_QAT),
            ('🍽', 'التغذية',          'بيانات وجبات اليوم',          '#f78166', TAB_NUTRITION),
            ('🏢', 'الأقسام',          'إدارة وعرض الأقسام',          '#58a6ff', TAB_DEPARTMENTS),
            ('📊', 'التقارير',         'تقارير يومية وشهرية',          '#da3633', TAB_REPORTS),
        ]

        for i, (icon, label, desc, color, tab) in enumerate(ACTIONS):
            btn = QuickActionBtn(icon, label, desc, color)
            btn.clicked.connect(lambda _, t=tab: self.switch_to_tab.emit(t))
            grid.addWidget(btn, i // 4, i % 4)

        layout.addLayout(grid)

        self._last_refresh_lbl = QLabel()
        self._last_refresh_lbl.setStyleSheet(
            'font-size: 10px; color: #484f58; background: transparent;'
        )
        self._last_refresh_lbl.setAlignment(Qt.AlignLeft)
        layout.addWidget(self._last_refresh_lbl)

        return frame

    # ─── Logic ───────────────────────────────────
    def _tick_clock(self):
        self._clock_lbl.setText(datetime.now().strftime('%H:%M:%S'))

    def refresh_stats(self):
        today = date.today().strftime('%Y-%m-%d')
        try:
            summary = self.db.get_daily_summary(today)
            total   = len(self.db.get_all_employees())
            present = summary.get('present', 0)
            absent  = summary.get('absent', 0)
            visits  = summary.get('visits', 0)
            unrecorded = max(0, total - present - absent)

            self._card_present.update_value(present)
            self._card_absent.update_value(absent)
            self._card_total.update_value(total)
            self._card_visits.update_value(visits)
            self._card_unrecorded.update_value(unrecorded)

            self._refresh_alerts(today, unrecorded, summary)

            self._last_refresh_lbl.setText(
                f'آخر تحديث: {datetime.now().strftime("%H:%M:%S")}'
            )
        except Exception:
            pass

    def _refresh_alerts(self, today, unrecorded, summary):
        # Clear old alerts
        while self._alerts_layout.count():
            item = self._alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        alerts = []
        open_visits = []

        if unrecorded > 0:
            alerts.append((
                f'{unrecorded} موظف لم يُسجَّل حضورهم أو غيابهم اليوم',
                'warning'
            ))
        try:
            open_visits = self.db.get_open_visits(today)
            if open_visits:
                alerts.append((
                    f'{len(open_visits)} زيارة مفتوحة — دخلوا ولم يخرجوا بعد',
                    'error'
                ))
        except Exception:
            pass

        p = summary.get('present', 0)
        a = summary.get('absent', 0)
        total_att = p + a
        if total_att > 0:
            pct = int(p / total_att * 100)
            color = 'success' if pct >= 80 else ('warning' if pct >= 60 else 'error')
            alerts.append((f'نسبة الحضور اليوم: {p}/{total_att} ({pct}%)', color))

        if not alerts or (unrecorded == 0 and not open_visits):
            if unrecorded == 0 and not open_visits:
                alerts.insert(0, ('جميع بيانات اليوم مكتملة ✓', 'success'))

        for text, atype in alerts:
            self._alerts_layout.addWidget(AlertItem(text, atype))

        if not alerts:
            no = QLabel('لا توجد تنبيهات حالياً')
            no.setStyleSheet('color: #484f58; font-size: 12px; padding: 10px;')
            no.setAlignment(Qt.AlignCenter)
            self._alerts_layout.addWidget(no)

    def refresh(self):
        self.refresh_stats()
