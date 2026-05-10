"""
تبويب حركة الزيارات - Visits Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QComboBox, QDateEdit, QMessageBox, QSplitter, QTextEdit,
    QCheckBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from datetime import datetime
import printing_utils
import export_utils


VISIT_TYPES = ['عادية', 'طارئة', 'رسمية', 'شخصية', 'عمل', 'زيارة طبية', 'إجازة', 'أخرى']


class VisitsTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_employee = None
        self.current_visit_id = None
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        self.load_visits()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title + Date
        top_row = QHBoxLayout()
        title = QLabel('🚪 حركة الزيارات')
        title.setObjectName('page_title')

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedWidth(140)
        self.date_edit.dateChanged.connect(self.load_visits)

        today_btn = QPushButton('📅 اليوم')
        today_btn.setObjectName('info')
        today_btn.setFixedWidth(80)
        today_btn.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))

        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(QLabel('التاريخ:'))
        top_row.addWidget(self.date_edit)
        top_row.addWidget(today_btn)
        main_layout.addLayout(top_row)

        # Splitter: left=form, right=table
        splitter = QSplitter(Qt.Horizontal)
        splitter.setLayoutDirection(Qt.RightToLeft)

        # ===== Left: Input Form =====
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(0, 0, 0, 0)

        # Code search
        code_frame = QFrame()
        code_frame.setObjectName('card')
        code_layout = QVBoxLayout(code_frame)
        code_layout.setSpacing(8)

        code_title = QLabel('🔍 البحث بالكود')
        code_title.setStyleSheet(
            'font-size: 14px; font-weight: bold; color: #58a6ff; background: transparent;'
        )
        code_layout.addWidget(code_title)

        code_row = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText('أدخل كود الموظف...')
        self.code_input.setFixedHeight(38)
        self.code_input.returnPressed.connect(self._search_employee)

        search_btn = QPushButton('بحث')
        search_btn.setObjectName('info')
        search_btn.setFixedWidth(70)
        search_btn.setFixedHeight(38)
        search_btn.clicked.connect(self._search_employee)

        code_row.addWidget(self.code_input)
        code_row.addWidget(search_btn)
        code_layout.addLayout(code_row)
        form_layout.addWidget(code_frame)

        # Employee info display
        info_frame = QFrame()
        info_frame.setObjectName('card')
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(6)

        info_title = QLabel('👤 بيانات الموظف')
        info_title.setStyleSheet('font-size: 14px; font-weight: bold; color: #58a6ff; background: transparent;')
        info_layout.addWidget(info_title)

        def info_row(label):
            row = QHBoxLayout()
            lbl = QLabel(f'{label}:')
            lbl.setStyleSheet('color: #8b949e; font-size: 12px; background: transparent; min-width: 80px;')
            val = QLabel('---')
            val.setStyleSheet('color: #e6edf3; font-size: 13px; font-weight: bold; background: transparent;')
            val.setWordWrap(True)
            row.addWidget(lbl)
            row.addWidget(val, 1)
            return row, val

        r1, self.emp_name = info_row('الاسم')
        r2, self.emp_code = info_row('الكود')
        r3, self.emp_dept = info_row('القسم')
        r4, self.emp_gov = info_row('المحافظة')
        r5, self.emp_marital = info_row('الحالة')

        for r in [r1, r2, r3, r4, r5]:
            info_layout.addLayout(r)
        form_layout.addWidget(info_frame)

        # Visit form
        visit_frame = QFrame()
        visit_frame.setObjectName('card')
        visit_layout = QVBoxLayout(visit_frame)
        visit_layout.setSpacing(8)

        visit_title = QLabel('📝 تفاصيل الزيارة')
        visit_title.setStyleSheet('font-size: 14px; font-weight: bold; color: #58a6ff; background: transparent;')
        visit_layout.addWidget(visit_title)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel('نوع الزيارة:'))
        self.visit_type = QComboBox()
        self.visit_type.addItems(VISIT_TYPES)
        type_row.addWidget(self.visit_type, 1)
        visit_layout.addLayout(type_row)

        notes_row = QHBoxLayout()
        notes_row.addWidget(QLabel('ملاحظات:'))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText('ملاحظات اختيارية...')
        notes_row.addWidget(self.notes_input, 1)
        visit_layout.addLayout(notes_row)

        form_layout.addWidget(visit_frame)

        # Action buttons
        btn_frame = QFrame()
        btn_frame.setObjectName('card')
        btn_layout = QVBoxLayout(btn_frame)
        btn_layout.setSpacing(8)

        entry_btn = QPushButton('🟢 تسجيل دخول')
        entry_btn.setFixedHeight(42)
        entry_btn.setStyleSheet('background-color:#238636; font-size:14px; font-weight:bold;')
        entry_btn.clicked.connect(self._record_entry)

        exit_btn = QPushButton('🔴 تسجيل خروج')
        exit_btn.setFixedHeight(42)
        exit_btn.setObjectName('danger')
        exit_btn.setStyleSheet('font-size:14px; font-weight:bold;')
        exit_btn.clicked.connect(self._record_exit)

        self.print_permit_btn = QPushButton('🖨️ طباعة التصريح')
        self.print_permit_btn.setFixedHeight(38)
        self.print_permit_btn.setObjectName('print_btn')
        self.print_permit_btn.setEnabled(False)
        self.print_permit_btn.clicked.connect(self._print_permit)

        # Auto-print checkbox
        self.auto_print_chk = QCheckBox('طباعة تلقائية عند التسجيل')
        self.auto_print_chk.setChecked(False)
        self.auto_print_chk.setToolTip('عند التفعيل: يُطبع التصريح تلقائياً بعد تسجيل الدخول أو الخروج')

        btn_layout.addWidget(entry_btn)
        btn_layout.addWidget(exit_btn)
        pdf_btn = QPushButton('📄 PDF الزيارات')
        pdf_btn.setObjectName('info')
        pdf_btn.setFixedHeight(38)
        pdf_btn.clicked.connect(self._pdf_visits)

        excel_btn = QPushButton('📊 Excel')
        excel_btn.setFixedHeight(38)
        excel_btn.setStyleSheet(
            'QPushButton { background: #1a7f37; color: #fff; border-radius: 7px;'
            ' font-weight: bold; padding: 0 10px; }'
            'QPushButton:hover { background: #2ea043; }'
        )
        excel_btn.clicked.connect(self._excel_visits)

        btn_layout.addWidget(self.print_permit_btn)
        btn_layout.addWidget(pdf_btn)
        btn_layout.addWidget(excel_btn)
        btn_layout.addWidget(self.auto_print_chk)
        form_layout.addWidget(btn_frame)
        form_layout.addStretch()

        # ===== Right: Visits Table =====
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setSpacing(6)
        table_layout.setContentsMargins(0, 0, 0, 0)

        table_title = QLabel('📋 سجل الزيارات اليومية')
        table_title.setStyleSheet(
            'font-size: 14px; font-weight: bold; color: #58a6ff;'
            'padding: 4px 8px; background-color: #161b22; border-radius: 4px;'
        )
        table_layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'الاسم', 'الكود', 'القسم', 'المحافظة', 'الحالة الاجتماعية', 'نوع الزيارة', 'دخول', 'خروج'
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.clicked.connect(self._on_table_click)
        table_layout.addWidget(self.table)

        splitter.addWidget(form_widget)
        splitter.addWidget(table_widget)
        splitter.setSizes([380, 700])

        main_layout.addWidget(splitter)

    def _search_employee(self):
        code = self.code_input.text().strip()
        if not code:
            return

        emp = self.db.get_employee_by_code(code)
        if emp:
            self.current_employee = dict(emp)
            self.emp_name.setText(emp['real_name'])
            self.emp_code.setText(emp['code'])
            self.emp_dept.setText(emp['department'] or '---')
            self.emp_gov.setText(emp['governorate'] or '---')
            self.emp_marital.setText(emp['marital_status'])
            marital_color = '#f0883e' if emp['marital_status'] == 'متزوج' else '#56d364'
            self.emp_marital.setStyleSheet(f'color:{marital_color}; font-size:13px; font-weight:bold; background:transparent;')
        else:
            self.current_employee = None
            for lbl in [self.emp_name, self.emp_code, self.emp_dept, self.emp_gov, self.emp_marital]:
                lbl.setText('---')
            QMessageBox.warning(self, 'تنبيه', f'لم يتم العثور على موظف بالكود: {code}')

    def _record_entry(self):
        if not self.current_employee:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء البحث عن الموظف أولاً')
            return
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        entry_time = datetime.now().strftime('%H:%M:%S')
        visit_type = self.visit_type.currentText()
        notes = self.notes_input.toPlainText().strip()

        visit_id = self.db.add_visit(
            self.current_employee['id'], visit_type, entry_time, date_str, notes
        )
        self.current_visit_id = visit_id
        self.print_permit_btn.setEnabled(True)
        self.load_visits()

        # Show toast if main window is available
        self._show_toast(
            f'✅ تم تسجيل دخول: {self.current_employee["real_name"]}  |  {entry_time}',
            'success'
        )

        # Auto-print if enabled
        if self.auto_print_chk.isChecked():
            self._print_permit()

    def _record_exit(self):
        if not self.current_visit_id:
            # Try to find latest open visit for this employee
            if not self.current_employee:
                QMessageBox.warning(self, 'تنبيه', 'الرجاء البحث عن الموظف أولاً')
                return
            date_str = self.date_edit.date().toString('yyyy-MM-dd')
            open_visits = self.db.get_open_visits(date_str)
            emp_visits = [v for v in open_visits if v['employee_id'] == self.current_employee['id']]
            if not emp_visits:
                QMessageBox.warning(self, 'تنبيه', 'لا يوجد تسجيل دخول مفتوح لهذا الموظف')
                return
            self.current_visit_id = emp_visits[0]['id']

        exit_time = datetime.now().strftime('%H:%M:%S')
        self.db.update_visit_exit(self.current_visit_id, exit_time)
        self.print_permit_btn.setEnabled(True)
        self.load_visits()

        name = self.current_employee['real_name'] if self.current_employee else ''
        self._show_toast(f'🔴 تم تسجيل الخروج: {name}  |  {exit_time}', 'info')

        # Auto-print if enabled
        if self.auto_print_chk.isChecked():
            self._print_permit()

    def _show_toast(self, message, toast_type='success'):
        """إرسال toast إلى النافذة الرئيسية إن أمكن"""
        try:
            main_win = self.window()
            if hasattr(main_win, 'show_toast'):
                main_win.show_toast(message, toast_type)
        except Exception:
            pass

    def _print_permit(self):
        if not self.current_employee or not self.current_visit_id:
            return
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        visits = self.db.get_visits_by_date(date_str)
        visit = next((v for v in visits if v['id'] == self.current_visit_id), None)
        if visit:
            printing_utils.print_visit_permit(
                self, self.current_employee,
                visit['visit_type'], visit['entry_time'], visit['exit_time']
            )

    def _get_visits_rows(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        visits   = self.db.get_visits_by_date(date_str)
        headers  = ['الاسم', 'الكود', 'القسم', 'المحافظة', 'الحالة الاجتماعية',
                    'نوع الزيارة', 'دخول', 'خروج']
        rows = [
            [v['real_name'], v['code'], v['department'] or '', v['governorate'] or '',
             v['marital_status'], v['visit_type'],
             v['entry_time'] or '', v['exit_time'] or 'لم يغادر']
            for v in visits
        ]
        return date_str, headers, rows

    def _pdf_visits(self):
        from datetime import datetime
        date_str, headers, rows = self._get_visits_rows()
        rows_html = ''.join(
            f'<tr>{"".join(f"<td>{c}</td>" for c in r)}</tr>'
            for r in rows
        )
        html = (
            '<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><style>'
            'body{font-family:Arial,Tahoma;font-size:11pt;margin:15px;}'
            '.h{text-align:center;border-bottom:4px solid #1f6feb;padding-bottom:8px;margin-bottom:12px;}'
            '.h h1{color:#1f6feb;font-size:17pt;margin:0;}'
            'table{width:100%;border-collapse:collapse;}'
            'th{background:#1f6feb;color:#fff;padding:7px;text-align:right;}'
            'td{padding:5px 8px;border:1px solid #ddd;text-align:right;}'
            'tr:nth-child(even){background:#f5f5f5;}'
            '</style></head><body>'
            f'<div class="h"><h1>🚪 سجل الزيارات اليومية</h1><p>{date_str}</p></div>'
            f'<table><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr>'
            f'{rows_html}</table>'
            f'<div style="text-align:center;color:#888;font-size:9pt;margin-top:14px;">'
            f'طُبع في {datetime.now().strftime("%Y/%m/%d %H:%M")}</div></body></html>'
        )
        export_utils.save_as_pdf(self, html, f'زيارات_{date_str}.pdf')

    def _excel_visits(self):
        date_str, headers, rows = self._get_visits_rows()
        export_utils.save_as_excel(self, headers, rows, f'زيارات_{date_str}.xlsx',
                                   sheet_title=f'زيارات {date_str}')

    def _on_table_click(self):
        row = self.table.currentRow()
        if row < 0:
            return
        visit_id_item = self.table.item(row, 0)
        if visit_id_item:
            self.current_visit_id = visit_id_item.data(Qt.UserRole)
            self.print_permit_btn.setEnabled(True)

    def load_visits(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        visits = self.db.get_visits_by_date(date_str)

        self.table.setRowCount(len(visits))
        for row, v in enumerate(visits):
            values = [
                v['real_name'], v['code'], v['department'] or '',
                v['governorate'] or '', v['marital_status'],
                v['visit_type'], v['entry_time'] or '', v['exit_time'] or '---'
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 0:
                    item.setData(Qt.UserRole, v['id'])
                self.table.setItem(row, col, item)

            # Color exit status
            exit_item = self.table.item(row, 7)
            if v['exit_time']:
                exit_item.setForeground(QColor('#f85149'))
            else:
                exit_item.setForeground(QColor('#3fb950'))
                exit_item.setText('لم يغادر')

    def refresh(self):
        self.load_visits()
