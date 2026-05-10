"""
تبويب التقارير - Reports Tab
نسخة محدّثة: طباعة + PDF + Excel + أرشفة، التقرير اليومي مجمَّع حسب الأقسام
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFrame, QTabWidget, QScrollArea, QGridLayout,
    QMessageBox, QListWidget, QListWidgetItem, QSplitter, QTextBrowser,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument
from datetime import datetime, date
import printing_utils
import export_utils


MONTHS_AR = [
    '', 'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
    'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
]

DEPT_COLORS_SUMMARY = [
    '#1f6feb', '#238636', '#9e6a03', '#8250df',
    '#da3633', '#0ca4a5', '#e3b341', '#f78166',
]

REPORT_TYPE_LABELS = {
    'daily_attendance':   '📅 تقرير حضور يومي',
    'monthly_attendance': '📆 تقرير حضور شهري',
}


# ── Helpers ──────────────────────────────────────────────────────────────────

class SummaryCard(QFrame):
    def __init__(self, title, value, subtitle='', color='#58a6ff', icon=''):
        super().__init__()
        self.setObjectName('stat_card')
        self.setMinimumWidth(160)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 12, 12, 12)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet('font-size: 26px; background: transparent;')

        val_lbl = QLabel(str(value))
        val_lbl.setAlignment(Qt.AlignCenter)
        val_lbl.setStyleSheet(
            f'font-size: 28px; font-weight: bold; color: {color}; background: transparent;'
        )

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet('font-size: 12px; color: #8b949e; background: transparent;')

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setAlignment(Qt.AlignCenter)
            sub_lbl.setStyleSheet('font-size: 11px; color: #484f58; background: transparent;')
            layout.addWidget(sub_lbl)

        self.value_label = val_lbl
        layout.addWidget(icon_lbl)
        layout.addWidget(val_lbl)
        layout.addWidget(title_lbl)


def _make_print_bar(print_fn, pdf_fn, excel_fn, archive_fn=None):
    """شريط أزرار: طباعة + PDF + Excel (+ أرشفة اختيارياً)"""
    bar = QFrame()
    bar.setObjectName('card')
    bar.setFixedHeight(52)
    h = QHBoxLayout(bar)
    h.setContentsMargins(10, 6, 10, 6)
    h.setSpacing(8)

    lbl = QLabel('📤 تصدير:')
    lbl.setStyleSheet('color:#8b949e; font-size:13px;')
    h.addWidget(lbl)

    print_btn = QPushButton('🖨️  طباعة مباشرة')
    print_btn.setObjectName('print_btn')
    print_btn.setFixedHeight(36)
    print_btn.clicked.connect(print_fn)
    h.addWidget(print_btn)

    pdf_btn = QPushButton('📄  حفظ PDF')
    pdf_btn.setObjectName('info')
    pdf_btn.setFixedHeight(36)
    pdf_btn.clicked.connect(pdf_fn)
    h.addWidget(pdf_btn)

    excel_btn = QPushButton('📊  تصدير Excel')
    excel_btn.setFixedHeight(36)
    excel_btn.setStyleSheet(
        'QPushButton { background: #1a7f37; color: #fff; border-radius: 7px;'
        ' font-weight: bold; padding: 0 14px; }'
        'QPushButton:hover { background: #2ea043; }'
    )
    excel_btn.clicked.connect(excel_fn)
    h.addWidget(excel_btn)

    if archive_fn:
        arch_btn = QPushButton('🗄️  أرشفة')
        arch_btn.setObjectName('secondary')
        arch_btn.setFixedHeight(36)
        arch_btn.clicked.connect(archive_fn)
        h.addWidget(arch_btn)

    h.addStretch()
    return bar


# ── Main Tab ──────────────────────────────────────────────────────────────────

class ReportsTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._current_daily_html   = ''
        self._current_monthly_html = ''
        self._setup_ui()
        self.load_daily_report()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel('📊 التقارير والإحصائيات')
        title.setObjectName('page_title')
        layout.addWidget(title)

        self.report_tabs = QTabWidget()
        layout.addWidget(self.report_tabs)

        self.report_tabs.addTab(self._build_daily_tab(),   '📅 التقرير اليومي')
        self.report_tabs.addTab(self._build_monthly_tab(), '📆 التقرير الشهري')
        self.report_tabs.addTab(self._build_summary_tab(), '📈 الإحصائيات العامة')
        self.report_tabs.addTab(self._build_archive_tab(), '🗄️ الأرشيف')

    # ═══════════════════════════════════════════════════════════════════════════
    # ■ التقرير اليومي
    # ═══════════════════════════════════════════════════════════════════════════

    def _build_daily_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        # Controls
        ctrl = QHBoxLayout()
        self.daily_date = QDateEdit()
        self.daily_date.setDate(QDate.currentDate())
        self.daily_date.setCalendarPopup(True)
        self.daily_date.setFixedWidth(150)

        today_btn = QPushButton('اليوم')
        today_btn.setObjectName('info')
        today_btn.setFixedWidth(70)
        today_btn.clicked.connect(lambda: self.daily_date.setDate(QDate.currentDate()))

        load_btn = QPushButton('🔍 عرض التقرير')
        load_btn.clicked.connect(self.load_daily_report)

        ctrl.addWidget(QLabel('التاريخ:'))
        ctrl.addWidget(self.daily_date)
        ctrl.addWidget(today_btn)
        ctrl.addWidget(load_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        layout.addWidget(_make_print_bar(
            print_fn   = self._print_daily,
            pdf_fn     = self._pdf_daily,
            excel_fn   = self._excel_daily,
            archive_fn = self._archive_daily,
        ))

        # Stats cards
        stats_frame = QFrame()
        stats_frame.setObjectName('card')
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(10)

        self.daily_present_card = SummaryCard('الحاضرون',  0, color='#3fb950', icon='✅')
        self.daily_absent_card  = SummaryCard('الغائبون',  0, color='#f85149', icon='❌')
        self.daily_visits_card  = SummaryCard('الزيارات',  0, color='#58a6ff', icon='🚪')
        self.daily_food_card    = SummaryCard('الوجبات',   0, color='#e3b341', icon='🍽')

        for card in (self.daily_present_card, self.daily_absent_card,
                     self.daily_visits_card, self.daily_food_card):
            stats_layout.addWidget(card)
        layout.addWidget(stats_frame)

        # Table
        self.daily_table = QTableWidget()
        self.daily_table.setColumnCount(7)
        self.daily_table.setHorizontalHeaderLabels([
            'الرقم', 'الكود', 'الاسم الحقيقي', 'الاسم الوظيفي',
            'القسم', 'الحالة', 'وقت الحضور'
        ])
        self.daily_table.setAlternatingRowColors(True)
        self.daily_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.daily_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.daily_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.daily_table.setShowGrid(False)
        self.daily_table.verticalHeader().setDefaultSectionSize(34)
        layout.addWidget(self.daily_table)
        return widget

    def load_daily_report(self):
        date_str = self.daily_date.date().toString('yyyy-MM-dd')
        summary  = self.db.get_daily_summary(date_str)

        self.daily_present_card.value_label.setText(str(summary.get('present', 0)))
        self.daily_absent_card.value_label.setText(str(summary.get('absent', 0)))
        self.daily_visits_card.value_label.setText(str(summary.get('visits', 0)))
        self.daily_food_card.value_label.setText(str(summary.get('food', 0)))

        all_emps = self.db.get_all_employees()
        att_map  = {r['employee_id']: r for r in self.db.get_attendance_by_date(date_str)}

        self.daily_table.setRowCount(len(all_emps))
        for row, emp in enumerate(all_emps):
            att     = att_map.get(emp['id'])
            status  = att['status']  if att else 'غير مسجل'
            time_in = att['time_in'] if att else ''

            values = [str(emp['id']), emp['code'], emp['real_name'],
                      emp['job_name'], emp['department'] or '', status, time_in or '']
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 0:
                    item.setData(Qt.UserRole, emp['id'])
                self.daily_table.setItem(row, col, item)

            status_item = self.daily_table.item(row, 5)
            if status == 'حاضر':
                status_item.setForeground(QColor('#3fb950'))
                self._set_row_bg(self.daily_table, row, '#0d2a0d', 7)
            elif status == 'غائب':
                status_item.setForeground(QColor('#f85149'))
                self._set_row_bg(self.daily_table, row, '#2a0d0d', 7)
            else:
                status_item.setForeground(QColor('#d29922'))

        # Build + cache HTML
        dept_data = self.db.get_attendance_by_dept(date_str)
        self._current_daily_html = printing_utils.build_daily_attendance_html(
            date_str, dept_data, summary
        )

    def _set_row_bg(self, table, row, color, col_count):
        for col in range(col_count):
            item = table.item(row, col)
            if item:
                item.setBackground(QColor(color))

    def _get_daily_dept_data(self):
        date_str  = self.daily_date.date().toString('yyyy-MM-dd')
        dept_data = self.db.get_attendance_by_dept(date_str)
        summary   = self.db.get_daily_summary(date_str)
        return date_str, dept_data, summary

    def _print_daily(self):
        date_str, dept_data, summary = self._get_daily_dept_data()
        printing_utils.print_daily_by_dept(self, date_str, dept_data, summary)

    def _pdf_daily(self):
        if not self._current_daily_html:
            self.load_daily_report()
        date_str = self.daily_date.date().toString('yyyy-MM-dd')
        export_utils.save_as_pdf(self, self._current_daily_html,
                                 f'تقرير_حضور_{date_str}.pdf')

    def _excel_daily(self):
        date_str, dept_data, _ = self._get_daily_dept_data()
        export_utils.save_grouped_excel(self, dept_data, date_str,
                                        f'تقرير_حضور_{date_str}.xlsx')

    def _archive_daily(self):
        if not self._current_daily_html:
            self.load_daily_report()
        date_str = self.daily_date.date().toString('yyyy-MM-dd')
        self.db.save_report(
            report_type  = 'daily_attendance',
            report_date  = date_str,
            title        = f'تقرير الحضور اليومي — {date_str}',
            html_content = self._current_daily_html,
        )
        self._show_toast('تم أرشفة التقرير بنجاح ✅', 'success')
        self._reload_archive()

    # ═══════════════════════════════════════════════════════════════════════════
    # ■ التقرير الشهري
    # ═══════════════════════════════════════════════════════════════════════════

    def _build_monthly_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        ctrl = QHBoxLayout()
        self.month_combo = QComboBox()
        self.month_combo.setFixedWidth(120)
        for i, m in enumerate(MONTHS_AR[1:], 1):
            self.month_combo.addItem(m, i)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)

        self.year_spin = QComboBox()
        self.year_spin.setFixedWidth(90)
        cy = datetime.now().year
        for y in range(cy - 3, cy + 2):
            self.year_spin.addItem(str(y), y)
        self.year_spin.setCurrentText(str(cy))

        load_btn = QPushButton('🔍 عرض التقرير')
        load_btn.clicked.connect(self.load_monthly_report)

        ctrl.addWidget(QLabel('الشهر:'))
        ctrl.addWidget(self.month_combo)
        ctrl.addWidget(QLabel('السنة:'))
        ctrl.addWidget(self.year_spin)
        ctrl.addWidget(load_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        layout.addWidget(_make_print_bar(
            print_fn   = self._print_monthly,
            pdf_fn     = self._pdf_monthly,
            excel_fn   = self._excel_monthly,
            archive_fn = self._archive_monthly,
        ))

        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(7)
        self.monthly_table.setHorizontalHeaderLabels([
            'الرقم', 'الكود', 'الاسم الحقيقي', 'الاسم الوظيفي',
            'القسم', 'أيام الحضور', 'أيام الغياب'
        ])
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.monthly_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.monthly_table.setShowGrid(False)
        self.monthly_table.verticalHeader().setDefaultSectionSize(34)
        layout.addWidget(self.monthly_table)
        return widget

    def load_monthly_report(self):
        month = self.month_combo.currentData()
        year  = int(self.year_spin.currentText())
        data  = self.db.get_monthly_attendance_report(year, month)

        self.monthly_table.setRowCount(len(data))
        rows_for_html = []
        for row, emp in enumerate(data):
            present = emp['present_days'] or 0
            absent  = emp['absent_days']  or 0
            values  = [str(emp['id']), emp['code'], emp['real_name'],
                       emp['job_name'], emp['department'] or '', str(present), str(absent)]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.monthly_table.setItem(row, col, item)
            self.monthly_table.item(row, 5).setForeground(QColor('#3fb950'))
            self.monthly_table.item(row, 6).setForeground(QColor('#f85149'))
            rows_for_html.append(values)

        months_ar  = MONTHS_AR
        month_name = months_ar[month] if 1 <= month <= 12 else str(month)
        rows_html  = ''.join(
            f'<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td>'
            f'<td>{r[3]}</td><td>{r[4]}</td>'
            f'<td style="color:#1a7f37;font-weight:bold;">{r[5]}</td>'
            f'<td style="color:#cf222e;font-weight:bold;">{r[6]}</td></tr>'
            for r in rows_for_html
        )
        self._current_monthly_html = (
            '<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><style>'
            'body{font-family:Arial,Tahoma;font-size:11pt;margin:15px;}'
            '.header{text-align:center;border-bottom:4px solid #8250df;'
            'padding-bottom:10px;margin-bottom:14px;}'
            '.header h1{color:#8250df;font-size:18pt;margin:0;}'
            'table{width:100%;border-collapse:collapse;}'
            'th{background:#8250df;color:#fff;padding:7px;text-align:right;}'
            'td{padding:6px 8px;border:1px solid #ddd;text-align:right;}'
            'tr:nth-child(even){background:#f5f5f5;}'
            '</style></head><body>'
            f'<div class="header"><h1>&#128202; التقرير الشهري للحضور</h1>'
            f'<p>شهر {month_name} {year}</p></div>'
            '<table><tr><th>#</th><th>الكود</th><th>الاسم</th><th>الوظيفة</th>'
            '<th>القسم</th><th>أيام الحضور</th><th>أيام الغياب</th></tr>'
            f'{rows_html}</table>'
            f'<div style="text-align:center;color:#888;font-size:9pt;margin-top:16px;">'
            f'نظام إدارة الموظفين — طُبع في {datetime.now().strftime("%Y/%m/%d  %H:%M")}'
            '</div></body></html>'
        )

    def _print_monthly(self):
        month = self.month_combo.currentData()
        year  = int(self.year_spin.currentText())
        data  = self.db.get_monthly_attendance_report(year, month)
        printing_utils.print_monthly_report(self, year, month, [dict(r) for r in data])

    def _pdf_monthly(self):
        if not self._current_monthly_html:
            self.load_monthly_report()
        month = self.month_combo.currentData()
        year  = int(self.year_spin.currentText())
        export_utils.save_as_pdf(self, self._current_monthly_html,
                                 f'تقرير_شهري_{year}_{month:02d}.pdf')

    def _excel_monthly(self):
        month = self.month_combo.currentData()
        year  = int(self.year_spin.currentText())
        data  = self.db.get_monthly_attendance_report(year, month)
        headers = ['الرقم', 'الكود', 'الاسم الحقيقي', 'الاسم الوظيفي',
                   'القسم', 'أيام الحضور', 'أيام الغياب']
        rows = [[str(r['id']), r['code'], r['real_name'], r['job_name'],
                 r['department'] or '', r['present_days'] or 0, r['absent_days'] or 0]
                for r in data]
        export_utils.save_as_excel(self, headers, rows,
                                   f'تقرير_شهري_{year}_{month:02d}.xlsx',
                                   sheet_title=f'شهر {MONTHS_AR[month]} {year}')

    def _archive_monthly(self):
        if not self._current_monthly_html:
            self.load_monthly_report()
        month = self.month_combo.currentData()
        year  = int(self.year_spin.currentText())
        self.db.save_report(
            report_type  = 'monthly_attendance',
            report_date  = f'{year}-{month:02d}',
            title        = f'تقرير الحضور الشهري — {MONTHS_AR[month]} {year}',
            html_content = self._current_monthly_html,
        )
        self._show_toast('تم أرشفة التقرير بنجاح ✅', 'success')
        self._reload_archive()

    # ═══════════════════════════════════════════════════════════════════════════
    # ■ الإحصائيات العامة
    # ═══════════════════════════════════════════════════════════════════════════

    def _build_summary_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet('background: transparent;')
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        dept_title = QLabel('📂 إحصائيات الأقسام')
        dept_title.setStyleSheet(
            'font-size:15px;font-weight:bold;color:#58a6ff;'
            'padding:6px 10px;background-color:#21262d;border-radius:6px;'
        )
        content_layout.addWidget(dept_title)

        dept_stats = self.db.get_department_stats()
        dept_grid  = QFrame()
        dept_grid.setObjectName('card')
        dept_grid_layout = QGridLayout(dept_grid)
        dept_grid_layout.setSpacing(10)

        for i, row in enumerate(dept_stats):
            card = SummaryCard(
                row['department'], row['count'], '👥 موظف',
                DEPT_COLORS_SUMMARY[i % len(DEPT_COLORS_SUMMARY)], '🏢'
            )
            dept_grid_layout.addWidget(card, i // 4, i % 4)
        content_layout.addWidget(dept_grid)

        today        = date.today().strftime('%Y-%m-%d')
        today_summary= self.db.get_daily_summary(today)

        today_title = QLabel(f'📅 ملخص اليوم — {today}')
        today_title.setStyleSheet(
            'font-size:15px;font-weight:bold;color:#3fb950;'
            'padding:6px 10px;background-color:#1a3a1a;border-radius:6px;'
        )
        content_layout.addWidget(today_title)

        today_frame  = QFrame()
        today_frame.setObjectName('card')
        today_layout = QHBoxLayout(today_frame)
        today_layout.setSpacing(10)

        for lbl, key, color, icon in [
            ('الحاضرون',       'present',         '#3fb950', '✅'),
            ('الغائبون',       'absent',          '#f85149', '❌'),
            ('إجمالي الموظفين','total_employees', '#58a6ff', '👥'),
            ('الزيارات',       'visits',          '#8250df', '🚪'),
            ('الوجبات',        'food',            '#e3b341', '🍽'),
        ]:
            today_layout.addWidget(
                SummaryCard(lbl, today_summary.get(key, 0), color=color, icon=icon)
            )
        content_layout.addWidget(today_frame)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return widget

    # ═══════════════════════════════════════════════════════════════════════════
    # ■ الأرشيف
    # ═══════════════════════════════════════════════════════════════════════════

    def _build_archive_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        # Filter bar
        fbar = QHBoxLayout()
        self.arch_type_combo = QComboBox()
        self.arch_type_combo.addItem('الكل', None)
        for k, v in REPORT_TYPE_LABELS.items():
            self.arch_type_combo.addItem(v, k)
        self.arch_type_combo.setFixedWidth(220)
        self.arch_type_combo.currentIndexChanged.connect(self._reload_archive)

        refresh_btn = QPushButton('🔄 تحديث')
        refresh_btn.setObjectName('info')
        refresh_btn.setFixedWidth(90)
        refresh_btn.clicked.connect(self._reload_archive)

        fbar.addWidget(QLabel('نوع التقرير:'))
        fbar.addWidget(self.arch_type_combo)
        fbar.addWidget(refresh_btn)
        fbar.addStretch()
        layout.addLayout(fbar)

        # Splitter: list + preview
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        list_panel  = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)
        list_layout.addWidget(QLabel('التقارير المحفوظة:'))

        self.arch_list = QListWidget()
        self.arch_list.setAlternatingRowColors(True)
        self.arch_list.itemSelectionChanged.connect(self._on_archive_select)
        list_layout.addWidget(self.arch_list)

        arch_btns = QHBoxLayout()
        reprint_btn = QPushButton('🖨️ طباعة')
        reprint_btn.setObjectName('print_btn')
        reprint_btn.clicked.connect(self._reprint_archived)

        repdf_btn = QPushButton('📄 PDF')
        repdf_btn.setObjectName('info')
        repdf_btn.clicked.connect(self._repdf_archived)

        del_btn = QPushButton('🗑️ حذف')
        del_btn.setObjectName('danger')
        del_btn.clicked.connect(self._delete_archived)

        arch_btns.addWidget(reprint_btn)
        arch_btns.addWidget(repdf_btn)
        arch_btns.addWidget(del_btn)
        list_layout.addLayout(arch_btns)

        preview_panel  = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.addWidget(QLabel('معاينة:'))
        self.arch_preview = QTextBrowser()
        self.arch_preview.setOpenExternalLinks(False)
        preview_layout.addWidget(self.arch_preview)

        splitter.addWidget(list_panel)
        splitter.addWidget(preview_panel)
        splitter.setSizes([280, 600])
        layout.addWidget(splitter, 1)

        self._reload_archive()
        return widget

    def _reload_archive(self):
        if not hasattr(self, 'arch_list'):
            return
        report_type = self.arch_type_combo.currentData()
        records     = self.db.get_archived_reports(report_type)
        self.arch_list.clear()
        for rec in records:
            lbl  = REPORT_TYPE_LABELS.get(rec['report_type'], rec['report_type'])
            item = QListWidgetItem(
                f"{lbl}  |  {rec['report_date']}  |  {rec['created_at'][:16]}"
            )
            item.setData(Qt.UserRole, rec['id'])
            self.arch_list.addItem(item)

    def _selected_archive_id(self):
        items = self.arch_list.selectedItems()
        return items[0].data(Qt.UserRole) if items else None

    def _on_archive_select(self):
        rid = self._selected_archive_id()
        if rid is None:
            self.arch_preview.setHtml('')
            return
        html = self.db.get_report_html(rid)
        if html:
            self.arch_preview.setHtml(html)

    def _reprint_archived(self):
        rid = self._selected_archive_id()
        if rid is None:
            return
        html = self.db.get_report_html(rid)
        if html:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            dlg = QPrintDialog(printer, self)
            if dlg.exec_() == QPrintDialog.Accepted:
                doc = QTextDocument()
                doc.setHtml(html)
                doc.print_(printer)

    def _repdf_archived(self):
        rid = self._selected_archive_id()
        if rid is None:
            return
        html = self.db.get_report_html(rid)
        if html:
            export_utils.save_as_pdf(self, html, 'تقرير_مؤرشف.pdf')

    def _delete_archived(self):
        rid = self._selected_archive_id()
        if rid is None:
            return
        reply = QMessageBox.question(self, 'تأكيد الحذف',
                                     'هل تريد حذف هذا التقرير من الأرشيف؟',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_report(rid)
            self.arch_preview.setHtml('')
            self._reload_archive()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _show_toast(self, message, toast_type='info'):
        mw = self.window()
        if hasattr(mw, 'show_toast'):
            mw.show_toast(message, toast_type)

    def refresh(self):
        self.load_daily_report()
