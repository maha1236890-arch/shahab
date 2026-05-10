"""
تبويب الحضور والغياب - Attendance Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFrame, QDateEdit, QHeaderView, QAbstractItemView,
    QMessageBox
)
from PyQt5.QtCore import Qt, QDate
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

        # Toolbar
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

        # Stats cards
        stats_frame = QFrame()
        stats_frame.setObjectName('card')
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(10)

        self.card_present = StatCard('الحاضرون', '0', '#3fb950', '✅')
        self.card_absent = StatCard('الغائبون', '0', '#f85149', '❌')
        self.card_total = StatCard('إجمالي الموظفين', '0', '#58a6ff', '👥')
        self.card_unrecorded = StatCard('غير مسجل', '0', '#d29922', '⏳')

        stats_layout.addWidget(self.card_present)
        stats_layout.addWidget(self.card_absent)
        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_unrecorded)
        layout.addWidget(stats_frame)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'الرقم', 'الكود', 'الاسم الوظيفي', 'القسم', 'الحالة', 'الإجراءات'
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 160)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.table)

    def _get_date(self):
        return self.date_edit.date().toString('yyyy-MM-dd')

    def _go_today(self):
        self.date_edit.setDate(QDate.currentDate())

    def load_attendance(self):
        date_str = self._get_date()
        employees = self.db.get_all_employees()
        att_map = {row['employee_id']: row for row in self.db.get_attendance_by_date(date_str)}

        present, absent, total = self.db.get_attendance_stats(date_str)
        self.card_present.set_value(present)
        self.card_absent.set_value(absent)
        self.card_total.set_value(total)
        self.card_unrecorded.set_value(total - present - absent)

        self.table.setRowCount(len(employees))
        for row, emp in enumerate(employees):
            emp_id = emp['id']
            att = att_map.get(emp_id)

            for col, val in enumerate([
                str(emp['id']), emp['code'],
                emp['job_name'], emp['department'] or ''
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 0:
                    item.setData(Qt.UserRole, emp_id)
                self.table.setItem(row, col, item)

            # Status
            if att:
                status = att['status']
                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignCenter)
                if status == 'حاضر':
                    status_item.setForeground(QColor('#3fb950'))
                    status_item.setFont(QFont('Arial', 12, QFont.Bold))
                    self._set_row_bg(row, '#0d2a0d')
                else:
                    status_item.setForeground(QColor('#f85149'))
                    status_item.setFont(QFont('Arial', 12, QFont.Bold))
                    self._set_row_bg(row, '#2a0d0d')
            else:
                status_item = QTableWidgetItem('غير مسجل')
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(QColor('#d29922'))
            self.table.setItem(row, 5, status_item)

            # Action buttons
            btn_widget = QWidget()
            btn_widget.setStyleSheet('background: transparent;')
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(3, 3, 3, 3)
            btn_layout.setSpacing(4)

            p_btn = QPushButton('حاضر ✓')
            p_btn.setFixedHeight(28)
            p_btn.setStyleSheet(
                'background-color:#238636; color:white; border-radius:4px;'
                'font-size:11px; font-weight:bold; padding:0 6px;'
            )
            p_btn.clicked.connect(lambda _, eid=emp_id: self._mark(eid, 'حاضر'))

            a_btn = QPushButton('غائب ✗')
            a_btn.setFixedHeight(28)
            a_btn.setStyleSheet(
                'background-color:#da3633; color:white; border-radius:4px;'
                'font-size:11px; font-weight:bold; padding:0 6px;'
            )
            a_btn.clicked.connect(lambda _, eid=emp_id: self._mark(eid, 'غائب'))

            btn_layout.addWidget(p_btn)
            btn_layout.addWidget(a_btn)
            self.table.setCellWidget(row, 5, btn_widget)

    def _set_row_bg(self, row, color):
        for col in range(5):
            item = self.table.item(row, col)
            if item:
                item.setBackground(QColor(color))

    def _mark(self, employee_id, status):
        date_str = self._get_date()
        time_in = datetime.now().strftime('%H:%M') if status == 'حاضر' else None
        self.db.mark_attendance(employee_id, date_str, status, time_in)
        self.load_attendance()
        # Show toast notification and log
        try:
            main_win = self.window()
            emp = self.db.get_employee_by_id(employee_id)
            name = emp['real_name'] if emp else str(employee_id)
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

    def _mark_all_present(self):
        date_str = self._get_date()
        time_in = datetime.now().strftime('%H:%M')
        for emp in self.db.get_all_employees():
            self.db.mark_attendance(emp['id'], date_str, 'حاضر', time_in)
        self.load_attendance()
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
            row['status'] = att['status'] if att else 'غير مسجل'
            row['time_in'] = att['time_in'] if att else ''
            data.append(row)

        printing_utils.print_attendance_report(self, date_str, data)

    def _build_report_data(self):
        date_str = self._get_date()
        att_map  = {r['employee_id']: r for r in self.db.get_attendance_by_date(date_str)}
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
