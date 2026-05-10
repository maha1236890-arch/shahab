"""
تبويب إدارة الموظفين - Employees Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDialog, QFormLayout, QComboBox,
    QMessageBox, QHeaderView, QAbstractItemView, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import export_utils


GOVERNORATES = [
    'صنعاء', 'عدن', 'تعز', 'إب', 'حضرموت', 'الحديدة', 'مأرب', 'ذمار',
    'المحويت', 'لحج', 'أبين', 'شبوة', 'البيضاء', 'الجوف', 'عمران',
    'حجة', 'ريمة', 'المهرة', 'سقطرى', 'صعدة'
]

DEPARTMENTS = [
    'الإدارة', 'المالية', 'الهندسة', 'العمليات', 'الموارد البشرية',
    'الأمن', 'الخدمات', 'تقنية المعلومات', 'المشتريات', 'المخازن'
]


class EmployeeDialog(QDialog):
    def __init__(self, parent=None, employee=None):
        super().__init__(parent)
        self.employee = employee
        self.setWindowTitle('إضافة موظف جديد' if not employee else 'تعديل بيانات الموظف')
        self.setMinimumWidth(500)
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        if employee:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)

        # Title
        title = QLabel('👤 ' + ('إضافة موظف جديد' if not self.employee else 'تعديل بيانات الموظف'))
        title.setObjectName('page_title')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('font-size: 16px; font-weight: bold; color: #58a6ff; padding: 10px;')
        layout.addWidget(title)

        form_frame = QFrame()
        form_frame.setObjectName('card')
        form = QFormLayout(form_frame)
        form.setSpacing(10)
        form.setContentsMargins(16, 16, 16, 16)

        self.real_name = QLineEdit()
        self.real_name.setPlaceholderText('الاسم الثلاثي الكامل')

        self.job_name = QLineEdit()
        self.job_name.setPlaceholderText('المسمى الوظيفي')

        self.code = QLineEdit()
        self.code.setPlaceholderText('مثال: EMP001')

        self.marital_status = QComboBox()
        self.marital_status.addItems(['أعزب', 'متزوج'])

        self.governorate = QComboBox()
        self.governorate.setEditable(True)
        self.governorate.addItems(GOVERNORATES)

        self.department = QComboBox()
        self.department.setEditable(True)
        self.department.addItems(DEPARTMENTS)

        self.phone = QLineEdit()
        self.phone.setPlaceholderText('7XXXXXXXX')

        form.addRow('الاسم الحقيقي *', self.real_name)
        form.addRow('الاسم الوظيفي *', self.job_name)
        form.addRow('الكود *', self.code)
        form.addRow('الحالة الاجتماعية', self.marital_status)
        form.addRow('المحافظة', self.governorate)
        form.addRow('القسم *', self.department)
        form.addRow('رقم الهاتف', self.phone)

        layout.addWidget(form_frame)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(0, 12, 0, 0)

        save_btn = QPushButton('💾 حفظ')
        save_btn.clicked.connect(self._validate_and_accept)

        cancel_btn = QPushButton('❌ إلغاء')
        cancel_btn.setObjectName('danger')
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _load_data(self):
        emp = self.employee
        self.real_name.setText(emp['real_name'] or '')
        self.job_name.setText(emp['job_name'] or '')
        self.code.setText(emp['code'] or '')
        idx = self.marital_status.findText(emp['marital_status'])
        if idx >= 0:
            self.marital_status.setCurrentIndex(idx)
        self.governorate.setCurrentText(emp['governorate'] or '')
        self.department.setCurrentText(emp['department'] or '')
        self.phone.setText(emp['phone'] or '')

    def get_data(self):
        return {
            'real_name': self.real_name.text().strip(),
            'job_name': self.job_name.text().strip(),
            'code': self.code.text().strip().upper(),
            'marital_status': self.marital_status.currentText(),
            'governorate': self.governorate.currentText().strip(),
            'department': self.department.currentText().strip(),
            'phone': self.phone.text().strip(),
        }

    def _validate_and_accept(self):
        data = self.get_data()
        if not data['real_name']:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء إدخال الاسم الحقيقي')
            self.real_name.setFocus()
            return
        if not data['job_name']:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء إدخال الاسم الوظيفي')
            self.job_name.setFocus()
            return
        if not data['code']:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء إدخال الكود')
            self.code.setFocus()
            return
        if not data['department']:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء تحديد القسم')
            self.department.setFocus()
            return
        self.accept()


class EmployeesTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        self.load_employees()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        title = QLabel('👥 إدارة الموظفين')
        title.setObjectName('page_title')

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('🔍 بحث بالاسم أو الكود أو القسم...')
        self.search_input.setFixedWidth(320)
        self.search_input.textChanged.connect(self.search_employees)

        add_btn = QPushButton('➕ إضافة موظف')
        edit_btn = QPushButton('✏️ تعديل')
        edit_btn.setObjectName('warning')
        delete_btn = QPushButton('🗑️ حذف')
        delete_btn.setObjectName('danger')

        add_btn.clicked.connect(self.add_employee)
        edit_btn.clicked.connect(self.edit_employee)
        delete_btn.clicked.connect(self.delete_employee)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)

        pdf_btn = QPushButton('📄 PDF')
        pdf_btn.setObjectName('info')
        pdf_btn.clicked.connect(self._pdf_employees)
        excel_btn = QPushButton('📊 Excel')
        excel_btn.setStyleSheet(
            'QPushButton { background: #1a7f37; color: #fff; border-radius: 7px;'
            ' font-weight: bold; padding: 0 10px; }'
            'QPushButton:hover { background: #2ea043; }'
        )
        excel_btn.clicked.connect(self._excel_employees)
        toolbar.addWidget(pdf_btn)
        toolbar.addWidget(excel_btn)
        layout.addLayout(toolbar)

        # Stats bar
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(
            'color: #3fb950; font-size: 13px; font-weight: bold; padding: 4px 8px;'
            'background-color: #1a3a1a; border-radius: 6px;'
        )
        layout.addWidget(self.stats_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'الرقم', 'الاسم الحقيقي', 'الاسم الوظيفي', 'الكود',
            'الحالة الاجتماعية', 'المحافظة', 'القسم', 'رقم الهاتف'
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(self.edit_employee)
        layout.addWidget(self.table)

    def load_employees(self, employees=None):
        if employees is None:
            employees = self.db.get_all_employees()

        self.table.setRowCount(len(employees))
        for row, emp in enumerate(employees):
            items = [
                str(emp['id']), emp['real_name'], emp['job_name'], emp['code'],
                emp['marital_status'], emp['governorate'] or '', emp['department'] or '',
                emp['phone'] or ''
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 0:
                    item.setData(Qt.UserRole, emp['id'])
                self.table.setItem(row, col, item)

            # Color marital status
            status_item = self.table.item(row, 4)
            if emp['marital_status'] == 'متزوج':
                status_item.setForeground(QColor('#f0883e'))
            else:
                status_item.setForeground(QColor('#56d364'))

        self.stats_label.setText(
            f'  📊 إجمالي الموظفين: {len(employees)}  '
            f'| متزوج: {sum(1 for e in employees if e["marital_status"]=="متزوج")}  '
            f'| أعزب: {sum(1 for e in employees if e["marital_status"]=="أعزب")}'
        )

    def search_employees(self, query):
        if query.strip():
            employees = self.db.search_employees(query.strip())
        else:
            employees = self.db.get_all_employees()
        self.load_employees(employees)

    def _get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def add_employee(self):
        dialog = EmployeeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                self.db.add_employee(dialog.get_data())
                self.load_employees()
                QMessageBox.information(self, '✅ نجاح', 'تم إضافة الموظف بنجاح')
            except Exception as e:
                if 'UNIQUE' in str(e):
                    QMessageBox.warning(self, '❌ خطأ', 'هذا الكود مستخدم مسبقاً، الرجاء استخدام كود آخر')
                else:
                    QMessageBox.warning(self, '❌ خطأ', f'حدث خطأ: {str(e)}')

    def edit_employee(self):
        emp_id = self._get_selected_id()
        if not emp_id:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء تحديد موظف أولاً')
            return
        employee = self.db.get_employee_by_id(emp_id)
        dialog = EmployeeDialog(self, employee)
        if dialog.exec_() == QDialog.Accepted:
            try:
                self.db.update_employee(emp_id, dialog.get_data())
                self.load_employees()
                QMessageBox.information(self, '✅ نجاح', 'تم تعديل بيانات الموظف بنجاح')
            except Exception as e:
                if 'UNIQUE' in str(e):
                    QMessageBox.warning(self, '❌ خطأ', 'هذا الكود مستخدم مسبقاً')
                else:
                    QMessageBox.warning(self, '❌ خطأ', f'حدث خطأ: {str(e)}')

    def delete_employee(self):
        emp_id = self._get_selected_id()
        if not emp_id:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء تحديد موظف أولاً')
            return
        row = self.table.currentRow()
        name = self.table.item(row, 1).text() if self.table.item(row, 1) else ''
        reply = QMessageBox.question(
            self, 'تأكيد الحذف',
            f'هل أنت متأكد من حذف الموظف:\n{name}؟\nسيتم حذف جميع بياناته المرتبطة.',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_employee(emp_id)
            self.load_employees()

    def refresh(self):
        self.load_employees()

    def _get_emp_rows(self):
        employees = self.db.get_all_employees()
        headers = ['الرقم', 'الاسم الحقيقي', 'الاسم الوظيفي', 'الكود',
                   'الحالة الاجتماعية', 'المحافظة', 'القسم', 'رقم الهاتف']
        rows = [[str(e['id']), e['real_name'], e['job_name'], e['code'],
                 e['marital_status'] or '', e['governorate'] or '',
                 e['department'] or '', e['phone'] or '']
                for e in employees]
        return headers, rows

    def _pdf_employees(self):
        from datetime import datetime
        headers, rows = self._get_emp_rows()
        rows_html = ''.join(
            f'<tr>{"".join(f"<td>{c}</td>" for c in r)}</tr>' for r in rows
        )
        html = (
            '<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><style>'
            'body{font-family:Arial,Tahoma;font-size:10pt;margin:15px;}'
            '.h{text-align:center;border-bottom:4px solid #1f6feb;padding-bottom:8px;margin-bottom:12px;}'
            '.h h1{color:#1f6feb;font-size:17pt;margin:0;}'
            'table{width:100%;border-collapse:collapse;}'
            'th{background:#1f6feb;color:#fff;padding:6px;text-align:right;font-size:9pt;}'
            'td{padding:4px 7px;border:1px solid #ddd;text-align:right;font-size:9pt;}'
            'tr:nth-child(even){background:#f5f5f5;}'
            '</style></head><body>'
            '<div class="h"><h1>👥 قائمة الموظفين</h1></div>'
            f'<table><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr>'
            f'{rows_html}</table>'
            f'<div style="text-align:center;color:#888;font-size:9pt;margin-top:14px;">'
            f'طُبع في {datetime.now().strftime("%Y/%m/%d %H:%M")}</div></body></html>'
        )
        export_utils.save_as_pdf(self, html, 'قائمة_الموظفين.pdf')

    def _excel_employees(self):
        headers, rows = self._get_emp_rows()
        export_utils.save_as_excel(self, headers, rows, 'قائمة_الموظفين.xlsx',
                                   sheet_title='الموظفون')
