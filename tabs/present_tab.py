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
    def __init__(self, emp, color='#1f6feb', bg='#0d2040', qat_info=None):
        """
        emp       - sqlite3.Row أو dict
        qat_info  - {'function_name':str, 'count':int, 'lighter_count':int} أو None
        """
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
        layout.setSpacing(3)
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

        time_label = QLabel(f'⏰ {emp["time_in"] or "" if "time_in" in emp.keys() else ""}')
        time_label.setStyleSheet('color: #8b949e; font-size: 11px; background: transparent;')
        time_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(code_label)
        layout.addWidget(name_label)
        layout.addWidget(time_label)

        # عرض الظيف والقات إن وجد
        if qat_info:
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet('color: #30363d; margin: 2px 0;')
            layout.addWidget(sep)

            if qat_info.get('function_name'):
                fn_lbl = QLabel(f'💼 ظيف: {qat_info["function_name"]}')
                fn_lbl.setStyleSheet('color: #e3b341; font-size: 11px; background: transparent;')
                fn_lbl.setAlignment(Qt.AlignCenter)
                fn_lbl.setWordWrap(True)
                layout.addWidget(fn_lbl)

            qat_lbl = QLabel(f'🌿 {qat_info["count"]} قات  🔥 {qat_info["lighter_count"]} ولاعة')
            qat_lbl.setStyleSheet('color: #56d364; font-size: 11px; font-weight:bold; background: transparent;')
            qat_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(qat_lbl)


class DepartmentSection(QFrame):
    def __init__(self, dept_name, employees, color, bg,
                 qat_by_emp=None, nutrition_records=None):
        """
        qat_by_emp       - {employee_id: {'function_name','count','lighter_count'}}
        nutrition_records - list of nutrition rows for this dept
        """
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

        # ── Header: اسم القسم + إحصائيات ──
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

        # ── ملخص القات لهذا القسم ──
        qat_total = sum((qat_by_emp or {}).get(e['id'], {}).get('count', 0)
                        for e in employees)
        lighter_total = sum((qat_by_emp or {}).get(e['id'], {}).get('lighter_count', 0)
                            for e in employees)

        # ملخص التغذية لهذا القسم
        nut_food = sum(r['food_count'] or 0 for r in (nutrition_records or []))
        nut_qat  = sum(r['qat_count']  or 0 for r in (nutrition_records or []))

        has_qat  = qat_total > 0 or lighter_total > 0
        has_nutr = nut_food > 0 or nut_qat > 0

        if has_qat or has_nutr:
            summary_row = QHBoxLayout()
            if has_qat:
                qat_lbl = QLabel(
                    f'🌿 إجمالي القات: <b style="color:#56d364">{qat_total}</b>'  
                    f'   🔥 ولاعات: <b style="color:#f0883e">{lighter_total}</b>'
                )
                qat_lbl.setTextFormat(Qt.RichText)
                qat_lbl.setStyleSheet('font-size:12px; background:transparent; '
                                      'padding:3px 8px; color:#8b949e;')
                summary_row.addWidget(qat_lbl)
            if has_nutr:
                nut_lbl = QLabel(
                    f'🍽 وجبات: <b style="color:#3fb950">{nut_food}</b>'  
                    f'   🌿 تغذية-قات: <b style="color:#56d364">{nut_qat}</b>'
                )
                nut_lbl.setTextFormat(Qt.RichText)
                nut_lbl.setStyleSheet('font-size:12px; background:transparent; '
                                      'padding:3px 8px; color:#8b949e;')
                summary_row.addWidget(nut_lbl)
            summary_row.addStretch()
            layout.addLayout(summary_row)

        # ── بطاقات الموظفين ──
        if employees:
            grid_widget = QWidget()
            grid_widget.setStyleSheet('background: transparent;')
            grid = QGridLayout(grid_widget)
            grid.setSpacing(8)
            for i, emp in enumerate(employees):
                qat_info = (qat_by_emp or {}).get(emp['id'])
                card = EmployeeCard(emp, color, bg, qat_info=qat_info)
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
                 e['department'] or '', (e['time_in'] if 'time_in' in e.keys() else '') or '']
                for e in present]
        return date_str, headers, rows

    def _pdf_present(self):
        from datetime import datetime
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        present  = self.db.get_present_employees(date_str)

        # تجميع حسب القسم
        dept_map = {}
        for emp in present:
            dept = emp['department'] or 'غير محدد'
            dept_map.setdefault(dept, []).append(emp)

        DEPT_COLORS_HEX = ['#1F6FEB', '#238636', '#9E6A03', '#8250DF',
                            '#DA3633', '#0CA4A5', '#E3B341', '#F78166']

        dept_sections_html = ''
        for i, (dept, emps) in enumerate(sorted(dept_map.items())):
            color = DEPT_COLORS_HEX[i % len(DEPT_COLORS_HEX)]
            rows_html = ''.join(
                f'<tr><td>{e["real_name"]}</td><td>{e["code"]}</td>'
                f'<td>{e["job_name"]}</td>'
                f'<td>{(e["time_in"] if "time_in" in e.keys() else "") or ""}</td></tr>'
                for e in emps
            )
            dept_sections_html += (
                f'<div class="dept-hdr" style="background:{color};">'
                f'{dept}  —  {len(emps)} موظف</div>'
                f'<table><tr>'
                f'<th>الاسم</th><th>الكود</th><th>الاسم الوظيفي</th><th>وقت الحضور</th>'
                f'</tr>{rows_html}</table><br>'
            )

        total = sum(len(v) for v in dept_map.values())
        html = (
            '<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><style>'
            'body{font-family:Arial,Tahoma;font-size:11pt;margin:15px;}'
            '.h{text-align:center;border-bottom:4px solid #3fb950;padding-bottom:8px;margin-bottom:16px;}'
            '.h h1{color:#3fb950;font-size:17pt;margin:0;}'
            '.dept-hdr{color:#fff;font-weight:bold;font-size:13pt;padding:6px 10px;'
            'border-radius:4px;margin-bottom:4px;margin-top:10px;}'
            'table{width:100%;border-collapse:collapse;margin-bottom:6px;}'
            'th{background:#2d333b;color:#fff;padding:6px;text-align:right;}'
            'td{padding:5px 8px;border:1px solid #ddd;text-align:right;}'
            'tr:nth-child(even){background:#f5f5f5;}'
            '</style></head><body>'
            f'<div class="h"><h1>✅ الموظفون الحاضرون</h1>'
            f'<p>{date_str}  —  الإجمالي: {total} موظف</p></div>'
            f'{dept_sections_html}'
            f'<div style="text-align:center;color:#888;font-size:9pt;margin-top:14px;">'
            f'طُبع في {datetime.now().strftime("%Y/%m/%d %H:%M")}</div></body></html>'
        )
        export_utils.save_as_pdf(self, html, f'حاضرون_{date_str}.pdf')

    def _excel_present(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        present  = self.db.get_present_employees(date_str)

        # تجميع حسب القسم (مرتب أبجدياً)
        dept_map = {}
        for emp in present:
            dept = emp['department'] or 'غير محدد'
            dept_map.setdefault(dept, []).append(emp)

        export_utils.save_grouped_excel(
            self, dept_map, date_str,
            default_name=f'حاضرون_{date_str}.xlsx'
        )

    def refresh(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        present = self.db.get_present_employees(date_str)

        # جمع سجلات القات حسب الموظف
        qat_by_emp = {}
        for rec in self.db.get_qat_by_date(date_str):
            eid = rec['employee_id'] if 'employee_id' in rec.keys() else None
            if eid and eid not in qat_by_emp:
                qat_by_emp[eid] = {
                    'function_name':  rec['function_name'] or '',
                    'count':          rec['count'] or 0,
                    'lighter_count':  rec['lighter_count'] or 0,
                }
            elif eid:
                # جمع الإجماليات إذا كان للموظف أكثر من سجل
                qat_by_emp[eid]['count']         += rec['count'] or 0
                qat_by_emp[eid]['lighter_count'] += rec['lighter_count'] or 0

        # سجلات التغذية حسب القسم
        nut_by_dept = {}
        for r in self.db.get_nutrition_by_date(date_str):
            dept = r['department'] or ''
            nut_by_dept.setdefault(dept, []).append(r)

        # تجميع حسب القسم
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
                section = DepartmentSection(
                    dept, emps, color, bg,
                    qat_by_emp=qat_by_emp,
                    nutrition_records=nut_by_dept.get(dept, []),
                )
                v_layout.addWidget(section)

        v_layout.addStretch()
        self.scroll.setWidget(container)
