"""
تبويب الأقسام والموظفين - Departments Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame,
    QSplitter, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import export_utils


DEPT_COLORS = [
    '#1f6feb', '#238636', '#9e6a03', '#8250df',
    '#da3633', '#0ca4a5', '#e3b341', '#f78166',
]


class DepartmentsTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        self.load_departments()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        top_row = QHBoxLayout()
        title = QLabel('🏢 الأقسام والموظفون')
        title.setObjectName('page_title')

        refresh_btn = QPushButton('🔄 تحديث')
        refresh_btn.setObjectName('secondary')
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.refresh)

        top_row.addWidget(title)
        top_row.addStretch()

        pdf_btn = QPushButton('📄 PDF')
        pdf_btn.setObjectName('info')
        pdf_btn.clicked.connect(self._pdf_dept)
        excel_btn = QPushButton('📊 Excel')
        excel_btn.setStyleSheet(
            'QPushButton { background: #1a7f37; color: #fff; border-radius: 7px;'
            ' font-weight: bold; padding: 0 10px; }'
            'QPushButton:hover { background: #2ea043; }'
        )
        excel_btn.clicked.connect(self._excel_dept)

        top_row.addWidget(pdf_btn)
        top_row.addWidget(excel_btn)
        top_row.addWidget(refresh_btn)
        layout.addLayout(top_row)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setLayoutDirection(Qt.RightToLeft)

        # ===== Left: Departments list =====
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(6)
        left_layout.setContentsMargins(0, 0, 0, 0)

        dept_title = QLabel('📂 قائمة الأقسام')
        dept_title.setStyleSheet(
            'font-size: 14px; font-weight: bold; color: #58a6ff;'
            'padding: 6px 10px; background-color: #21262d; border-radius: 6px;'
        )
        left_layout.addWidget(dept_title)

        self.dept_list = QListWidget()
        self.dept_list.setSpacing(2)
        self.dept_list.currentItemChanged.connect(self._on_dept_selected)
        left_layout.addWidget(self.dept_list)

        # Totals
        self.total_label = QLabel()
        self.total_label.setStyleSheet(
            'font-size: 12px; color: #8b949e; padding: 4px;'
        )
        self.total_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.total_label)

        # ===== Right: Employees table =====
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(6)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.dept_header = QLabel('اختر قسماً للعرض')
        self.dept_header.setStyleSheet(
            'font-size: 16px; font-weight: bold; color: #3fb950;'
            'padding: 8px 12px; background-color: #1a3a1a;'
            'border-radius: 6px; border-right: 4px solid #3fb950;'
        )
        right_layout.addWidget(self.dept_header)

        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(5)
        self.employees_table.setHorizontalHeaderLabels([
            'الرقم', 'الاسم الحقيقي', 'الكود', 'الاسم الوظيفي', 'الحالة الاجتماعية'
        ])
        self.employees_table.setAlternatingRowColors(True)
        self.employees_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.employees_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.employees_table.setShowGrid(False)
        self.employees_table.verticalHeader().setDefaultSectionSize(36)
        right_layout.addWidget(self.employees_table)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

    def load_departments(self):
        stats = self.db.get_department_stats()
        total_employees = sum(row['count'] for row in stats)

        self.dept_list.clear()
        for i, row in enumerate(stats):
            color = DEPT_COLORS[i % len(DEPT_COLORS)]
            item = QListWidgetItem()
            item.setData(Qt.UserRole, row['department'])

            # Custom display widget
            widget = QFrame()
            widget.setStyleSheet('background: transparent;')
            widget_layout = QHBoxLayout(widget)
            widget_layout.setContentsMargins(8, 6, 8, 6)
            widget_layout.setSpacing(8)

            dept_icon = QLabel('🏢')
            dept_icon.setStyleSheet('font-size: 18px; background: transparent;')

            dept_name = QLabel(row['department'])
            dept_name.setStyleSheet(
                f'color: {color}; font-size: 14px; font-weight: bold; background: transparent;'
            )

            count_badge = QLabel(f'{row["count"]} موظف')
            count_badge.setStyleSheet(
                f'color: white; background-color: {color}; padding: 2px 10px;'
                f'border-radius: 10px; font-size: 12px; font-weight: bold;'
            )

            widget_layout.addWidget(dept_icon)
            widget_layout.addWidget(dept_name)
            widget_layout.addStretch()
            widget_layout.addWidget(count_badge)

            item.setSizeHint(widget.sizeHint())
            self.dept_list.addItem(item)
            self.dept_list.setItemWidget(item, widget)

        self.total_label.setText(
            f'إجمالي: {len(stats)} قسم | {total_employees} موظف'
        )

    def _on_dept_selected(self, current, previous):
        if not current:
            return
        dept = current.data(Qt.UserRole)
        if not dept:
            return
        self._load_employees(dept)

    def _load_employees(self, department):
        employees = self.db.get_employees_by_department(department)

        # Find color for this dept
        stats = self.db.get_department_stats()
        depts = [r['department'] for r in stats]
        idx = depts.index(department) if department in depts else 0
        color = DEPT_COLORS[idx % len(DEPT_COLORS)]

        self.dept_header.setText(f'🏢 {department}  ({len(employees)} موظف)')
        self.dept_header.setStyleSheet(
            f'font-size: 16px; font-weight: bold; color: {color};'
            f'padding: 8px 12px; background-color: #161b22;'
            f'border-radius: 6px; border-right: 4px solid {color};'
        )

        self.employees_table.setRowCount(len(employees))
        for row, emp in enumerate(employees):
            values = [
                str(emp['id']), emp['real_name'], emp['code'],
                emp['job_name'], emp['marital_status']
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.employees_table.setItem(row, col, item)

            # Color marital status
            ms_item = self.employees_table.item(row, 4)
            if emp['marital_status'] == 'متزوج':
                ms_item.setForeground(QColor('#f0883e'))
            else:
                ms_item.setForeground(QColor('#56d364'))

    def refresh(self):
        self.load_departments()
        # Reload current department if selected
        current = self.dept_list.currentItem()

    def _pdf_dept(self):
        from datetime import datetime
        all_emps = self.db.get_all_employees()
        dept_map = {}
        for e in all_emps:
            d = e['department'] or 'غير محدد'
            dept_map.setdefault(d, []).append(e)
        rows_html = ''
        for dept, emps in sorted(dept_map.items()):
            rows_html += (
                f'<tr style="background:#1f6feb;color:#fff;">'
                f'<td colspan="5"><b>{dept} ({len(emps)} موظف)</b></td></tr>'
            )
            rows_html += ''.join(
                f'<tr><td>{e["id"]}</td><td>{e["real_name"]}</td>'
                f'<td>{e["code"]}</td><td>{e["job_name"]}</td>'
                f'<td>{e["marital_status"] or ""}</td></tr>'
                for e in emps
            )
        html = (
            '<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><style>'
            'body{font-family:Arial,Tahoma;font-size:10pt;margin:15px;}'
            '.h{text-align:center;border-bottom:4px solid #1f6feb;padding-bottom:8px;margin-bottom:12px;}'
            '.h h1{color:#1f6feb;font-size:17pt;margin:0;}'
            'table{width:100%;border-collapse:collapse;}'
            'th{background:#21262d;color:#fff;padding:6px;text-align:right;}'
            'td{padding:4px 7px;border:1px solid #ddd;text-align:right;}'
            'tr:nth-child(even){background:#f9f9f9;}'
            '</style></head><body>'
            '<div class="h"><h1>🏢 الموظفون حسب الأقسام</h1></div>'
            '<table><tr><th>رقم</th><th>الاسم</th><th>كود</th><th>الوظيفة</th><th>الحالة الاجتماعية</th></tr>'
            f'{rows_html}</table>'
            f'<div style="text-align:center;color:#888;font-size:9pt;margin-top:14px;">'
            f'طُبع في {datetime.now().strftime("%Y/%m/%d %H:%M")}</div></body></html>'
        )
        export_utils.save_as_pdf(self, html, 'موظفون_حسب_الأقسام.pdf')

    def _excel_dept(self):
        all_emps = self.db.get_all_employees()
        headers  = ['الرقم', 'الاسم', 'الكود', 'الوظيفة', 'القسم', 'الحالة الاجتماعية']
        rows = [[str(e['id']), e['real_name'], e['code'], e['job_name'],
                 e['department'] or '', e['marital_status'] or '']
                for e in sorted(all_emps, key=lambda x: x['department'] or '')]
        export_utils.save_as_excel(self, headers, rows, 'موظفون_حسب_الأقسام.xlsx',
                                   sheet_title='الأقسام')
        if current:
            dept = current.data(Qt.UserRole)
            if dept:
                self._load_employees(dept)
