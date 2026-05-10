"""
تبويب الحاضرون - Present Employees Tab (مقسم حسب الأقسام)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QDateEdit, QPushButton, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import export_utils


DEPT_COLORS = [
    ('#1f6feb', '#0d2040'),
    ('#238636', '#0d2a0d'),
    ('#9e6a03', '#2a1f0d'),
    ('#8250df', '#1a0d2a'),
    ('#da3633', '#2a0d0d'),
    ('#0ca4a5', '#0d2020'),
    ('#e3b341', '#2a200d'),
    ('#f78166', '#2a1510'),
]


class EmployeeCard(QFrame):
    def __init__(self, emp, color='#1f6feb', bg='#0d2040'):
        super().__init__()
        self.setObjectName('card')
        self.setStyleSheet(f'''
            QFrame {{
                background-color: {bg};
                border: 1px solid {color};
                border-radius: 8px;
                padding: 6px;
            }}
        ''')
        self.setFixedWidth(200)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        code_label = QLabel(emp['code'])
        code_label.setStyleSheet(
            f'color: {color}; font-weight: bold; font-size: 14px;'
            'background: transparent;'
        )
        code_label.setAlignment(Qt.AlignCenter)

        name_label = QLabel(emp['job_name'])
        name_label.setStyleSheet('color: #e6edf3; font-size: 12px; background: transparent;')
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)

        time_label = QLabel(f'⏰ {emp.get("time_in", "") or ""}')
        time_label.setStyleSheet('color: #8b949e; font-size: 11px; background: transparent;')
        time_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(code_label)
        layout.addWidget(name_label)
        layout.addWidget(time_label)


class DepartmentSection(QFrame):
    def __init__(self, dept_name, employees, color, bg):
        super().__init__()
        self.setObjectName('card')
        self.setStyleSheet(f'''
            QFrame {{
                background-color: #161b22;
                border: 2px solid {color};
                border-radius: 10px;
                margin: 4px;
            }}
        ''')

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header = QHBoxLayout()
        dept_label = QLabel(f'🏢 {dept_name}')
        dept_label.setStyleSheet(
            f'color: {color}; font-size: 16px; font-weight: bold;'
            f'background-color: {bg}; padding: 6px 12px; border-radius: 6px;'
        )
        count_label = QLabel(f'{len(employees)} موظف حاضر')
        count_label.setStyleSheet(
            f'color: {color}; font-size: 13px; background: transparent;'
        )
        header.addWidget(dept_label)
        header.addStretch()
        header.addWidget(count_label)
        layout.addLayout(header)

        # Employee cards in grid
        if employees:
            grid_widget = QWidget()
            grid_widget.setStyleSheet('background: transparent;')
            grid = QGridLayout(grid_widget)
            grid.setSpacing(8)
            for i, emp in enumerate(employees):
                card = EmployeeCard(emp, color, bg)
                grid.addWidget(card, i // 5, i % 5)
            layout.addWidget(grid_widget)
        else:
            empty = QLabel('لا يوجد موظفون حاضرون في هذا القسم')
            empty.setStyleSheet('color: #484f58; font-size: 13px; background: transparent;')
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)


class PresentTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Toolbar
        toolbar = QHBoxLayout()

        title = QLabel('✅ الموظفون الحاضرون')
        title.setObjectName('page_title')

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedWidth(140)
        self.date_edit.dateChanged.connect(self.refresh)

        today_btn = QPushButton('📅 اليوم')
        today_btn.setObjectName('info')
        today_btn.setFixedWidth(90)
        today_btn.clicked.connect(self._go_today)

        refresh_btn = QPushButton('🔄 تحديث')
        refresh_btn.setObjectName('secondary')
        refresh_btn.clicked.connect(self.refresh)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(
            'color: #3fb950; font-size: 13px; font-weight: bold;'
            'padding: 4px 8px; background-color: #1a3a1a; border-radius: 6px;'
        )

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(self.summary_label)
        toolbar.addWidget(QLabel('التاريخ:'))
        toolbar.addWidget(self.date_edit)
        toolbar.addWidget(today_btn)
        toolbar.addWidget(refresh_btn)

        pdf_btn = QPushButton('📄 PDF')
        pdf_btn.setObjectName('info')
        pdf_btn.clicked.connect(self._pdf_present)
        excel_btn = QPushButton('📊 Excel')
        excel_btn.setStyleSheet(
            'QPushButton { background: #1a7f37; color: #fff; border-radius: 7px;'
            ' font-weight: bold; padding: 0 10px; }'
            'QPushButton:hover { background: #2ea043; }'
        )
        excel_btn.clicked.connect(self._excel_present)
        toolbar.addWidget(pdf_btn)
        toolbar.addWidget(excel_btn)
        layout.addLayout(toolbar)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self.scroll)

    def _go_today(self):
        self.date_edit.setDate(QDate.currentDate())

    def _get_present_data(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        present  = self.db.get_present_employees(date_str)
        headers  = ['الاسم', 'الكود', 'الاسم الوظيفي', 'القسم', 'وقت الحضور']
        rows = [[e['real_name'], e['code'], e['job_name'],
                 e['department'] or '', e.get('time_in') or '']
                for e in present]
        return date_str, headers, rows

    def _pdf_present(self):
        from datetime import datetime
        date_str, headers, rows = self._get_present_data()
        rows_html = ''.join(
            f'<tr>{"".join(f"<td>{c}</td>" for c in r)}</tr>' for r in rows
        )
        html = (
            '<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><style>'
            'body{font-family:Arial,Tahoma;font-size:11pt;margin:15px;}'
            '.h{text-align:center;border-bottom:4px solid #3fb950;padding-bottom:8px;margin-bottom:12px;}'
            '.h h1{color:#3fb950;font-size:17pt;margin:0;}'
            'table{width:100%;border-collapse:collapse;}'
            'th{background:#238636;color:#fff;padding:7px;text-align:right;}'
            'td{padding:5px 8px;border:1px solid #ddd;text-align:right;}'
            'tr:nth-child(even){background:#f5f5f5;}'
            '</style></head><body>'
            f'<div class="h"><h1>✅ الموظفون الحاضرون</h1><p>{date_str}</p></div>'
            f'<table><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr>'
            f'{rows_html}</table>'
            f'<div style="text-align:center;color:#888;font-size:9pt;margin-top:14px;">'
            f'طُبع في {datetime.now().strftime("%Y/%m/%d %H:%M")}</div></body></html>'
        )
        export_utils.save_as_pdf(self, html, f'حاضرون_{date_str}.pdf')

    def _excel_present(self):
        date_str, headers, rows = self._get_present_data()
        export_utils.save_as_excel(self, headers, rows, f'حاضرون_{date_str}.xlsx',
                                   sheet_title=f'حاضرون {date_str}')

    def refresh(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        present = self.db.get_present_employees(date_str)

        # Group by department
        dept_map = {}
        for emp in present:
            dept = emp['department'] or 'غير محدد'
            dept_map.setdefault(dept, []).append(emp)

        total = sum(len(v) for v in dept_map.values())
        self.summary_label.setText(f'  إجمالي الحاضرين: {total} موظف  ')

        container = QWidget()
        container.setStyleSheet('background: transparent;')
        v_layout = QVBoxLayout(container)
        v_layout.setSpacing(12)
        v_layout.setContentsMargins(4, 4, 4, 4)

        if not dept_map:
            empty = QLabel('⚠️  لا يوجد موظفون مسجلون كحاضرين في هذا اليوم')
            empty.setStyleSheet(
                'color: #d29922; font-size: 16px; font-weight: bold;'
                'padding: 40px; background: transparent;'
            )
            empty.setAlignment(Qt.AlignCenter)
            v_layout.addWidget(empty)
        else:
            for i, (dept, emps) in enumerate(sorted(dept_map.items())):
                color, bg = DEPT_COLORS[i % len(DEPT_COLORS)]
                section = DepartmentSection(dept, emps, color, bg)
                v_layout.addWidget(section)

        v_layout.addStretch()
        self.scroll.setWidget(container)
