"""
تبويب الحضور والغياب - Attendance Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFrame, QDateEdit, QHeaderView, QAbstractItemView,
    QMessageBox, QTabWidget
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from datetime import datetime
import printing_utils
import export_utils


class StatCard(QFrame):
    def __init__(self, title, value='0', color='#58a6ff', icon=''):
        super().__init__()
        self.setObjectName('stat_card')
        self.setMinimumWidth(140)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('font-size: 24px; background: transparent;')

        self.value_label = QLabel(value)
        self.value_label.setObjectName('stat_value')
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(
            f'font-size: 30px; font-weight: bold; color: {color}; background: transparent;'
        )

        self.title_label = QLabel(title)
        self.title_label.setObjectName('stat_title')
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet('font-size: 12px; color: #8b949e; background: transparent;')

        layout.addWidget(icon_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class AttendanceTab(QWidget):
    data_changed = pyqtSignal()   # يُطلق بعد كل تغيير في الحضور

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        self.load_attendance()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # ── Toolbar ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        title = QLabel('📋 تسجيل الحضور والغياب')
        title.setObjectName('page_title')

        date_label = QLabel('التاريخ:')
        date_label.setStyleSheet('font-weight: bold;')

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedWidth(140)
        self.date_edit.dateChanged.connect(self.load_attendance)

        today_btn = QPushButton('📅 اليوم')
        today_btn.setObjectName('info')
        today_btn.setFixedWidth(90)
        today_btn.clicked.connect(self._go_today)

        mark_all_btn = QPushButton('✅ تحضير الجميع')
        mark_all_btn.clicked.connect(self._mark_all_present)

        absent_all_btn = QPushButton('❌ تغيب الجميع')
        absent_all_btn.setObjectName('danger')
        absent_all_btn.clicked.connect(self._mark_all_absent)

        print_btn = QPushButton('🖨️ طباعة')
        print_btn.setObjectName('print_btn')
        print_btn.clicked.connect(self._print_report)

        pdf_btn = QPushButton('📄 PDF')
        pdf_btn.setObjectName('info')
        pdf_btn.clicked.connect(self._pdf_report)

        excel_btn = QPushButton('📊 Excel')
        excel_btn.setFixedHeight(32)
        excel_btn.setStyleSheet(
            'QPushButton { background: #1a7f37; color: #fff; border-radius: 7px;'
            ' font-weight: bold; padding: 0 10px; }'
            'QPushButton:hover { background: #2ea043; }'
        )
        excel_btn.clicked.connect(self._excel_report)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(date_label)
        toolbar.addWidget(self.date_edit)
        toolbar.addWidget(today_btn)
        toolbar.addWidget(mark_all_btn)
        toolbar.addWidget(absent_all_btn)
        toolbar.addWidget(print_btn)
        toolbar.addWidget(pdf_btn)
        toolbar.addWidget(excel_btn)
        layout.addLayout(toolbar)

        # ── Stats Cards ──
        stats_frame = QFrame()
        stats_frame.setObjectName('card')
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(10)

        self.card_present    = StatCard('الحاضرون',        '0', '#3fb950', '✅')
        self.card_absent     = StatCard('الغائبون',        '0', '#f85149', '❌')
        self.card_total      = StatCard('إجمالي الموظفين', '0', '#58a6ff', '👥')
        self.card_unrecorded = StatCard('غير مسجل',        '0', '#d29922', '⏳')

        stats_layout.addWidget(self.card_present)
        stats_layout.addWidget(self.card_absent)
        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_unrecorded)
        layout.addWidget(stats_frame)

        # ── Department Tabs ──
        self.dept_tabs = QTabWidget()
        self.dept_tabs.setStyleSheet('''
            QTabWidget::pane { border: 1px solid #30363d; border-radius: 6px;
                               background: #0d1117; }
            QTabBar::tab { background: #21262d; color: #8b949e; padding: 8px 18px;
                           border-radius: 4px; margin-right: 3px; font-size: 13px; }
            QTabBar::tab:selected { background: #1f6feb; color: #ffffff; font-weight: bold; }
            QTabBar::tab:hover:!selected { background: #30363d; color: #e6edf3; }
        ''')
        layout.addWidget(self.dept_tabs)

    def _get_date(self):
        return self.date_edit.date().toString('yyyy-MM-dd')

    def _go_today(self):
        self.date_edit.setDate(QDate.currentDate())

    def load_attendance(self):
        date_str = self._get_date()

        # Global stats
        present, absent, total = self.db.get_attendance_stats(date_str)
        self.card_present.set_value(present)
        self.card_absent.set_value(absent)
        self.card_total.set_value(total)
        self.card_unrecorded.set_value(total - present - absent)

        # All employees grouped by department (LEFT JOIN to attendance)
        dept_data = self.db.get_attendance_by_dept(date_str)

        # Preserve active tab
        current_idx = self.dept_tabs.currentIndex()
        self.dept_tabs.blockSignals(True)
        self.dept_tabs.clear()

        for dept, employees in dept_data.items():
            widget = self._build_dept_widget(employees)
            present_in_dept = sum(1 for e in employees if e['status'] == 'حاضر')
            tab_label = f'🏢 {dept}  ({present_in_dept}/{len(employees)})'
            self.dept_tabs.addTab(widget, tab_label)

        self.dept_tabs.blockSignals(False)

        if 0 <= current_idx < self.dept_tabs.count():
            self.dept_tabs.setCurrentIndex(current_idx)

    def _build_dept_widget(self, employees):
        """بناء widget لعرض موظفي قسم واحد"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # Dept mini-stats + per-dept action buttons
        present_count    = sum(1 for e in employees if e['status'] == 'حاضر')
        absent_count     = sum(1 for e in employees if e['status'] == 'غائب')
        unrecorded_count = len(employees) - present_count - absent_count

        top_row = QHBoxLayout()
        stats_lbl = QLabel(
            f'✅ حاضر: <b style="color:#3fb950">{present_count}</b>'
            f'   ❌ غائب: <b style="color:#f85149">{absent_count}</b>'
            f'   ⏳ غير مسجل: <b style="color:#d29922">{unrecorded_count}</b>'
            f'   👥 الإجمالي: <b style="color:#58a6ff">{len(employees)}</b>'
        )
        stats_lbl.setTextFormat(Qt.RichText)
        stats_lbl.setStyleSheet('font-size: 13px; padding: 4px;')

        mark_dept_btn = QPushButton('✅ تحضير القسم')
        mark_dept_btn.setFixedHeight(32)
        mark_dept_btn.setStyleSheet(
            'background-color:#238636; color:white; border-radius:5px;'
            ' font-weight:bold; padding:0 12px;'
        )
        mark_dept_btn.clicked.connect(
            lambda _, emps=employees: self._mark_dept_all(emps, 'حاضر')
        )

        absent_dept_btn = QPushButton('❌ تغيب القسم')
        absent_dept_btn.setFixedHeight(32)
        absent_dept_btn.setStyleSheet(
            'background-color:#da3633; color:white; border-radius:5px;'
            ' font-weight:bold; padding:0 12px;'
        )
        absent_dept_btn.clicked.connect(
            lambda _, emps=employees: self._mark_dept_all(emps, 'غائب')
        )

        top_row.addWidget(stats_lbl)
        top_row.addStretch()
        top_row.addWidget(mark_dept_btn)
        top_row.addWidget(absent_dept_btn)
        layout.addLayout(top_row)

        # Table for this department (no القسم column - we're already inside the dept tab)
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['#', 'الكود', 'الاسم الوظيفي', 'الحالة', 'الإجراءات'])
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)
        table.setColumnWidth(4, 160)
        table.setShowGrid(False)
        table.verticalHeader().setDefaultSectionSize(40)

        table.setRowCount(len(employees))
        for row, emp in enumerate(employees):
            emp_id = emp['emp_id']
            status = emp['status']

            for col, val in enumerate([str(row + 1), emp['code'], emp['job_name']]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 0:
                    item.setData(Qt.UserRole, emp_id)
                table.setItem(row, col, item)

            # Status cell
            if status == 'حاضر':
                status_item = QTableWidgetItem('✓ حاضر')
                status_item.setForeground(QColor('#3fb950'))
                status_item.setFont(QFont('Arial', 12, QFont.Bold))
                for col in range(4):
                    it = table.item(row, col)
                    if it:
                        it.setBackground(QColor('#0d2a0d'))
            elif status == 'غائب':
                status_item = QTableWidgetItem('✗ غائب')
                status_item.setForeground(QColor('#f85149'))
                status_item.setFont(QFont('Arial', 12, QFont.Bold))
                for col in range(4):
                    it = table.item(row, col)
                    if it:
                        it.setBackground(QColor('#2a0d0d'))
            else:
                status_item = QTableWidgetItem('⏳ غير مسجل')
                status_item.setForeground(QColor('#d29922'))
            status_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 3, status_item)

            # Action buttons
            btn_w = QWidget()
            btn_w.setStyleSheet('background: transparent;')
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(3, 3, 3, 3)
            btn_l.setSpacing(4)

            p_btn = QPushButton('حاضر ✓')
            p_btn.setFixedHeight(28)
            p_btn.setStyleSheet(
                'background-color:#238636; color:white; border-radius:4px;'
                ' font-size:11px; font-weight:bold; padding:0 6px;'
            )
            p_btn.clicked.connect(lambda _, eid=emp_id: self._mark(eid, 'حاضر'))

            a_btn = QPushButton('غائب ✗')
            a_btn.setFixedHeight(28)
            a_btn.setStyleSheet(
                'background-color:#da3633; color:white; border-radius:4px;'
                ' font-size:11px; font-weight:bold; padding:0 6px;'
            )
            a_btn.clicked.connect(lambda _, eid=emp_id: self._mark(eid, 'غائب'))

            btn_l.addWidget(p_btn)
            btn_l.addWidget(a_btn)
            table.setCellWidget(row, 4, btn_w)

        layout.addWidget(table)
        return widget

    def _mark(self, employee_id, status):
        date_str = self._get_date()
        time_in = datetime.now().strftime('%H:%M') if status == 'حاضر' else None
        self.db.mark_attendance(employee_id, date_str, status, time_in)
        current_idx = self.dept_tabs.currentIndex()
        self.load_attendance()
        if 0 <= current_idx < self.dept_tabs.count():
            self.dept_tabs.setCurrentIndex(current_idx)
        self.data_changed.emit()
        try:
            main_win = self.window()
            emp = self.db.get_employee_by_id(employee_id)
            name = emp['job_name'] if emp else str(employee_id)
            if hasattr(main_win, 'show_toast'):
                t = 'success' if status == 'حاضر' else 'warning'
                main_win.show_toast(f'{status}: {name}', t)
                main_win._update_badges()
            if hasattr(main_win, 'current_user') and main_win.current_user:
                u = main_win.current_user
                self.db.log_action(u['id'], u['username'], f'تسجيل {status}',
                                   f'{name} - {date_str}')
        except Exception:
            pass

    def _mark_dept_all(self, employees, status):
        date_str = self._get_date()
        time_in = datetime.now().strftime('%H:%M') if status == 'حاضر' else None
        for emp in employees:
            self.db.mark_attendance(emp['emp_id'], date_str, status, time_in)
        current_idx = self.dept_tabs.currentIndex()
        self.load_attendance()
        if 0 <= current_idx < self.dept_tabs.count():
            self.dept_tabs.setCurrentIndex(current_idx)
        self.data_changed.emit()
        try:
            main_win = self.window()
            if hasattr(main_win, 'show_toast'):
                label = 'حضور' if status == 'حاضر' else 'غياب'
                main_win.show_toast(
                    f'تم تسجيل {label} القسم', 'success' if status == 'حاضر' else 'warning'
                )
                main_win._update_badges()
        except Exception:
            pass

    def _mark_all_present(self):
        date_str = self._get_date()
        time_in = datetime.now().strftime('%H:%M')
        for emp in self.db.get_all_employees():
            self.db.mark_attendance(emp['id'], date_str, 'حاضر', time_in)
        self.load_attendance()
        self.data_changed.emit()
        try:
            main_win = self.window()
            if hasattr(main_win, 'show_toast'):
                main_win.show_toast('تم تسجيل حضور جميع الموظفين', 'success')
                main_win._update_badges()
            if hasattr(main_win, 'current_user') and main_win.current_user:
                u = main_win.current_user
                self.db.log_action(u['id'], u['username'], 'تسجيل حضور الكل', date_str)
        except Exception:
            pass

    def _mark_all_absent(self):
        reply = QMessageBox.question(
            self, 'تأكيد', 'هل تريد تسجيل غياب جميع الموظفين؟',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            date_str = self._get_date()
            for emp in self.db.get_all_employees():
                self.db.mark_attendance(emp['id'], date_str, 'غائب', None)
            self.load_attendance()
            self.data_changed.emit()
            try:
                main_win = self.window()
                if hasattr(main_win, 'show_toast'):
                    main_win.show_toast('تم تسجيل غياب جميع الموظفين', 'warning')
                    main_win._update_badges()
                if hasattr(main_win, 'current_user') and main_win.current_user:
                    u = main_win.current_user
                    self.db.log_action(u['id'], u['username'], 'تسجيل غياب الكل', date_str)
            except Exception:
                pass

    def _print_report(self):
        date_str = self._get_date()
        att_list = self.db.get_attendance_by_date(date_str)
        all_emps = self.db.get_all_employees()
        att_map = {row['employee_id']: row for row in att_list}

        data = []
        for emp in all_emps:
            att = att_map.get(emp['id'])
            row = dict(emp)
            row['status']  = att['status']  if att else 'غير مسجل'
            row['time_in'] = att['time_in'] if att else ''
            data.append(row)
        printing_utils.print_attendance_report(self, date_str, data)

    def _build_report_data(self):
        date_str = self._get_date()
        att_map = {r['employee_id']: r for r in self.db.get_attendance_by_date(date_str)}
        data = []
        for emp in self.db.get_all_employees():
            att = att_map.get(emp['id'])
            row = dict(emp)
            row['status']  = att['status']  if att else 'غير مسجل'
            row['time_in'] = att['time_in'] if att else ''
            data.append(row)
        return date_str, data

    def _pdf_report(self):
        date_str, data = self._build_report_data()
        dept_data = self.db.get_attendance_by_dept(date_str)
        summary   = self.db.get_daily_summary(date_str)
        html = printing_utils.build_daily_attendance_html(date_str, dept_data, summary)
        export_utils.save_as_pdf(self, html, f'حضور_{date_str}.pdf')

    def _excel_report(self):
        date_str, data = self._build_report_data()
        headers = ['الرقم', 'الكود', 'الاسم الوظيفي', 'القسم', 'الحالة', 'وقت الحضور']
        rows = [[str(r['id']), r['code'], r['job_name'],
                 r['department'] or '', r['status'], r['time_in'] or '']
                for r in data]
        export_utils.save_as_excel(self, headers, rows, f'حضور_{date_str}.xlsx',
                                   sheet_title=f'حضور {date_str}')

    def refresh(self):
        self.load_attendance()
