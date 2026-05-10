"""
تبويب القات - Qat Tab (مقسم حسب الأقسام)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame, QDateEdit,
    QPushButton, QDialog, QFormLayout, QComboBox, QSpinBox, QMessageBox,
    QLineEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from datetime import datetime


class QatRecordDialog(QDialog):
    def __init__(self, parent, employees, record=None):
        super().__init__(parent)
        self.setWindowTitle('إضافة سجل قات' if not record else 'تعديل سجل قات')
        self.setMinimumWidth(420)
        self.setLayoutDirection(Qt.RightToLeft)
        self.employees = employees
        self.record = record
        self._setup_ui()
        if record:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel('🌿 ' + ('إضافة سجل قات' if not self.record else 'تعديل سجل قات'))
        title.setStyleSheet('font-size:15px; font-weight:bold; color:#3fb950; padding:8px;')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        frame = QFrame()
        frame.setObjectName('card')
        form = QFormLayout(frame)
        form.setSpacing(10)
        form.setContentsMargins(14, 14, 14, 14)

        self.employee_combo = QComboBox()
        self.employee_combo.setEditable(True)
        for emp in self.employees:
            self.employee_combo.addItem(
                f"{emp['code']} - {emp['job_name']}", userData=emp['id']
            )

        self.function_name = QLineEdit()
        self.function_name.setPlaceholderText('مثال: ضيف خارجي')

        self.count_spin = QSpinBox()
        self.count_spin.setRange(0, 999)
        self.count_spin.setAlignment(Qt.AlignCenter)

        self.lighter_spin = QSpinBox()
        self.lighter_spin.setRange(0, 999)
        self.lighter_spin.setAlignment(Qt.AlignCenter)

        form.addRow('الموظف *', self.employee_combo)
        form.addRow('الظيف / الوظيفة', self.function_name)
        form.addRow('العدد', self.count_spin)
        form.addRow('الولاعات', self.lighter_spin)

        layout.addWidget(frame)

        btn_row = QHBoxLayout()
        save_btn = QPushButton('💾 حفظ')
        save_btn.clicked.connect(self._validate_accept)
        cancel_btn = QPushButton('❌ إلغاء')
        cancel_btn.setObjectName('danger')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _load_data(self):
        rec = self.record
        # Find employee index
        for i in range(self.employee_combo.count()):
            if self.employee_combo.itemData(i) == rec['employee_id']:
                self.employee_combo.setCurrentIndex(i)
                break
        self.function_name.setText(rec['function_name'] or '')
        self.count_spin.setValue(rec['count'] or 0)
        self.lighter_spin.setValue(rec['lighter_count'] or 0)

    def get_data(self):
        idx = self.employee_combo.currentIndex()
        employee_id = self.employee_combo.itemData(idx)
        # If typed manually, try to match
        if not employee_id:
            text = self.employee_combo.currentText()
            code = text.split(' - ')[0].strip() if ' - ' in text else text
            for emp in self.employees:
                if emp['code'] == code:
                    employee_id = emp['id']
                    break
        return {
            'employee_id': employee_id,
            'function_name': self.function_name.text().strip(),
            'count': self.count_spin.value(),
            'lighter_count': self.lighter_spin.value(),
        }

    def _validate_accept(self):
        data = self.get_data()
        if not data['employee_id']:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء اختيار الموظف')
            return
        self.accept()


class DeptQatWidget(QWidget):
    """قسم خاص بكل تبويب قسم"""
    def __init__(self, db, department, date_getter):
        super().__init__()
        self.db = db
        self.department = department
        self.date_getter = date_getter
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        self.load_records()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Toolbar
        bar = QHBoxLayout()
        add_btn = QPushButton('➕ إضافة')
        add_btn.setFixedWidth(110)
        add_btn.clicked.connect(self._add_record)

        self.total_label = QLabel()
        self.total_label.setStyleSheet('color:#3fb950; font-size:13px; font-weight:bold;')

        bar.addWidget(add_btn)
        bar.addStretch()
        bar.addWidget(self.total_label)
        layout.addLayout(bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'الكود', 'الاسم الوظيفي', 'القسم', 'الظيف', 'العدد', 'الولاعات', 'إجراءات'
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 110)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.table)

    def load_records(self):
        date_str = self.date_getter()
        records = self.db.get_qat_by_date_dept(date_str, self.department)

        self.table.setRowCount(len(records))
        total_count = 0
        total_lighter = 0

        for row, rec in enumerate(records):
            values = [
                rec['code'], rec['job_name'], rec['department'],
                rec['function_name'] or '', str(rec['count'] or 0),
                str(rec['lighter_count'] or 0)
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 0:
                    item.setData(Qt.UserRole, rec['id'])
                self.table.setItem(row, col, item)

            total_count += rec['count'] or 0
            total_lighter += rec['lighter_count'] or 0

            # Action buttons
            btn_w = QWidget()
            btn_w.setStyleSheet('background:transparent;')
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(3, 3, 3, 3)
            btn_l.setSpacing(4)

            edit_btn = QPushButton('✏️')
            edit_btn.setFixedSize(32, 28)
            edit_btn.setStyleSheet('background-color:#9e6a03;color:white;border-radius:4px;font-size:13px;')
            edit_btn.clicked.connect(lambda _, r=dict(rec): self._edit_record(r))

            del_btn = QPushButton('🗑')
            del_btn.setFixedSize(32, 28)
            del_btn.setStyleSheet('background-color:#da3633;color:white;border-radius:4px;font-size:13px;')
            del_btn.clicked.connect(lambda _, rid=rec['id']: self._delete_record(rid))

            btn_l.addWidget(edit_btn)
            btn_l.addWidget(del_btn)
            self.table.setCellWidget(row, 6, btn_w)

        self.total_label.setText(f'إجمالي: {total_count} قات | {total_lighter} ولاعة')

    def _get_dept_employees(self):
        return self.db.get_employees_by_department(self.department)

    def _add_record(self):
        employees = self._get_dept_employees()
        if not employees:
            QMessageBox.warning(self, 'تنبيه', 'لا يوجد موظفون في هذا القسم')
            return
        dialog = QatRecordDialog(self, employees)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            date_str = self.date_getter()
            self.db.add_qat_record(
                data['employee_id'], date_str,
                data['function_name'], data['count'], data['lighter_count']
            )
            self.load_records()

    def _edit_record(self, rec):
        employees = self._get_dept_employees()
        dialog = QatRecordDialog(self, employees, rec)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.update_qat_record(
                rec['id'], data['function_name'], data['count'], data['lighter_count']
            )
            self.load_records()

    def _delete_record(self, record_id):
        reply = QMessageBox.question(
            self, 'تأكيد', 'هل تريد حذف هذا السجل؟',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_qat_record(record_id)
            self.load_records()


class QatTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Toolbar
        toolbar = QHBoxLayout()
        title = QLabel('🌿 سجل القات')
        title.setObjectName('page_title')

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedWidth(140)
        self.date_edit.dateChanged.connect(self._on_date_changed)

        today_btn = QPushButton('📅 اليوم')
        today_btn.setObjectName('info')
        today_btn.setFixedWidth(80)
        today_btn.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(QLabel('التاريخ:'))
        toolbar.addWidget(self.date_edit)
        toolbar.addWidget(today_btn)
        layout.addLayout(toolbar)

        # Department tabs
        self.dept_tabs = QTabWidget()
        self.dept_tabs.setTabPosition(QTabWidget.North)
        layout.addWidget(self.dept_tabs)

        self._build_dept_tabs()

    def _get_date(self):
        return self.date_edit.date().toString('yyyy-MM-dd')

    def _build_dept_tabs(self):
        self.dept_tabs.clear()
        self.dept_widgets = {}

        departments = self.db.get_departments()
        if not departments:
            no_dept = QLabel('⚠️ لا توجد أقسام. الرجاء إضافة موظفين أولاً.')
            no_dept.setAlignment(Qt.AlignCenter)
            no_dept.setStyleSheet('color:#d29922; font-size:15px; padding:30px;')
            self.dept_tabs.addTab(no_dept, 'لا توجد أقسام')
            return

        for dept in departments:
            widget = DeptQatWidget(self.db, dept, self._get_date)
            self.dept_widgets[dept] = widget
            self.dept_tabs.addTab(widget, f'🏢 {dept}')

    def _on_date_changed(self):
        for widget in self.dept_widgets.values():
            widget.load_records()

    def refresh(self):
        # Rebuild tabs to pick up new departments
        self._build_dept_tabs()
