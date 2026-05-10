"""
تبويب البحث - Search Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class InfoField(QFrame):
    """حقل عرض معلومات"""
    def __init__(self, label, value='---'):
        super().__init__()
        self.setObjectName('card')
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 10, 12, 10)

        lbl = QLabel(label)
        lbl.setStyleSheet('color: #8b949e; font-size: 11px; background: transparent;')
        lbl.setAlignment(Qt.AlignRight)

        self.val_label = QLabel(value)
        self.val_label.setStyleSheet(
            'color: #e6edf3; font-size: 15px; font-weight: bold; background: transparent;'
        )
        self.val_label.setAlignment(Qt.AlignRight)
        self.val_label.setWordWrap(True)

        layout.addWidget(lbl)
        layout.addWidget(self.val_label)

    def set_value(self, value):
        self.val_label.setText(value or '---')


class SearchTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 20, 30, 20)

        # Title
        title = QLabel('🔍 البحث عن موظف')
        title.setObjectName('page_title')
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Search bar
        search_frame = QFrame()
        search_frame.setObjectName('card')
        search_layout = QHBoxLayout(search_frame)
        search_layout.setSpacing(10)

        search_label = QLabel('كود الموظف:')
        search_label.setStyleSheet('font-size: 15px; font-weight: bold;')

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText('أدخل كود الموظف... مثال: EMP001')
        self.code_input.setStyleSheet('font-size: 15px; min-height: 40px;')
        self.code_input.returnPressed.connect(self._search)

        search_btn = QPushButton('🔍 بحث')
        search_btn.setObjectName('info')
        search_btn.setFixedWidth(120)
        search_btn.setFixedHeight(42)
        search_btn.setStyleSheet('font-size: 14px;')
        search_btn.clicked.connect(self._search)

        clear_btn = QPushButton('🗑 مسح')
        clear_btn.setObjectName('secondary')
        clear_btn.setFixedWidth(90)
        clear_btn.setFixedHeight(42)
        clear_btn.clicked.connect(self._clear)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.code_input)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(clear_btn)
        main_layout.addWidget(search_frame)

        # Result card
        self.result_frame = QFrame()
        self.result_frame.setObjectName('card')
        self.result_frame.setVisible(False)
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setSpacing(12)

        result_title = QLabel('📋 بيانات الموظف')
        result_title.setStyleSheet(
            'font-size: 16px; font-weight: bold; color: #3fb950;'
            'background: transparent; padding: 4px;'
        )
        result_title.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(result_title)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet('color: #30363d;')
        result_layout.addWidget(divider)

        # Info grid
        grid = QGridLayout()
        grid.setSpacing(10)

        self.field_id = InfoField('الرقم')
        self.field_code = InfoField('الكود')
        self.field_job_name = InfoField('الاسم الوظيفي')
        self.field_real_name = InfoField('الاسم الحقيقي')
        self.field_dept = InfoField('القسم')
        self.field_phone = InfoField('رقم الهاتف')
        self.field_marital = InfoField('الحالة الاجتماعية')
        self.field_gov = InfoField('المحافظة')

        grid.addWidget(self.field_id, 0, 0)
        grid.addWidget(self.field_code, 0, 1)
        grid.addWidget(self.field_job_name, 1, 0)
        grid.addWidget(self.field_real_name, 1, 1)
        grid.addWidget(self.field_dept, 2, 0)
        grid.addWidget(self.field_phone, 2, 1)
        grid.addWidget(self.field_marital, 3, 0)
        grid.addWidget(self.field_gov, 3, 1)

        result_layout.addLayout(grid)
        main_layout.addWidget(self.result_frame)

        # Status message
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            'font-size: 14px; padding: 16px;'
            'color: #8b949e; background: transparent;'
        )
        self.status_label.setText('أدخل كود الموظف ثم اضغط بحث')
        main_layout.addWidget(self.status_label)
        main_layout.addStretch()

    def _search(self):
        code = self.code_input.text().strip()
        if not code:
            self.status_label.setText('⚠️ الرجاء إدخال كود الموظف')
            self.status_label.setStyleSheet('font-size:14px; color:#d29922; padding:16px; background:transparent;')
            self.result_frame.setVisible(False)
            return

        emp = self.db.get_employee_by_code(code)
        if emp:
            self.field_id.set_value(str(emp['id']))
            self.field_code.set_value(emp['code'])
            self.field_job_name.set_value(emp['job_name'])
            self.field_real_name.set_value(emp['real_name'])
            self.field_dept.set_value(emp['department'])
            self.field_phone.set_value(emp['phone'])
            self.field_gov.set_value(emp['governorate'])

            marital = emp['marital_status']
            color = '#f0883e' if marital == 'متزوج' else '#56d364'
            self.field_marital.val_label.setStyleSheet(
                f'color:{color}; font-size:16px; font-weight:bold; background:transparent;'
            )
            self.field_marital.set_value(marital)

            self.result_frame.setVisible(True)
            self.status_label.setText('')
        else:
            self.result_frame.setVisible(False)
            self.status_label.setText(f'❌  لم يتم العثور على موظف بالكود: {code}')
            self.status_label.setStyleSheet('font-size:15px; color:#f85149; padding:16px; background:transparent;')

    def _clear(self):
        self.code_input.clear()
        self.result_frame.setVisible(False)
        self.status_label.setText('أدخل كود الموظف ثم اضغط بحث')
        self.status_label.setStyleSheet('font-size:14px; color:#8b949e; padding:16px; background:transparent;')
        self.code_input.setFocus()

    def refresh(self):
        pass
