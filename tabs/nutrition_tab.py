"""
تبويب التغذية - Nutrition Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDateEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFrame, QTextEdit, QMessageBox, QGridLayout,
    QTabWidget, QComboBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from datetime import datetime
import printing_utils
import export_utils


class SpinCard(QFrame):
    """بطاقة إدخال العدد"""
    def __init__(self, label, icon='', color='#58a6ff'):
        super().__init__()
        self.setObjectName('card')
        self.setMinimumWidth(140)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('font-size: 28px; background: transparent;')

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f'color: {color}; font-size: 13px; font-weight: bold; background: transparent;')

        self.spin = QSpinBox()
        self.spin.setRange(0, 9999)
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.setStyleSheet(f'font-size: 16px; font-weight: bold; color: {color};')

        layout.addWidget(icon_label)
        layout.addWidget(lbl)
        layout.addWidget(self.spin)

    def value(self):
        return self.spin.value()

    def set_value(self, v):
        self.spin.setValue(int(v or 0))

    def reset(self):
        self.spin.setValue(0)


class NutritionTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.editing_id = None
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        self.load_records()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel('🍽 تسجيل التغذية واليوميات')
        title.setObjectName('page_title')
        layout.addWidget(title)

        # Input section
        input_frame = QFrame()
        input_frame.setObjectName('card')
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(10)

        # Date + Department row
        top_row = QHBoxLayout()
        date_label = QLabel('التاريخ:')
        date_label.setStyleSheet('font-size: 14px; font-weight: bold;')

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedWidth(150)
        self.date_edit.dateChanged.connect(self.load_records)

        today_btn = QPushButton('📅 اليوم')
        today_btn.setObjectName('info')
        today_btn.setFixedWidth(80)
        today_btn.clicked.connect(self._go_today)

        dept_label = QLabel('القسم:')
        dept_label.setStyleSheet('font-size: 14px; font-weight: bold;')

        self.dept_combo = QComboBox()
        self.dept_combo.setFixedWidth(170)
        self.dept_combo.setStyleSheet('font-size: 13px; min-height: 30px;')
        self._reload_depts()

        top_row.addWidget(date_label)
        top_row.addWidget(self.date_edit)
        top_row.addWidget(today_btn)
        top_row.addSpacing(20)
        top_row.addWidget(dept_label)
        top_row.addWidget(self.dept_combo)
        top_row.addStretch()
        input_layout.addLayout(top_row)

        # Spin cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        self.food_spin      = SpinCard('الوجبات الغذائية', '🍽', '#3fb950')
        self.qat_spin       = SpinCard('القات',             '🌿', '#56d364')
        self.lighter_spin   = SpinCard('الولاعات',          '🔥', '#f0883e')
        self.cigarette_spin = SpinCard('الدخان',            '🚬', '#8b949e')
        self.snuff_spin     = SpinCard('الشمة',             '🟤', '#bb8009')

        cards_row.addWidget(self.food_spin)
        cards_row.addWidget(self.qat_spin)
        cards_row.addWidget(self.lighter_spin)
        cards_row.addWidget(self.cigarette_spin)
        cards_row.addWidget(self.snuff_spin)
        input_layout.addLayout(cards_row)

        # Notes row
        notes_row = QHBoxLayout()
        notes_lbl = QLabel('ملاحظات:')
        notes_lbl.setStyleSheet('font-size: 13px; font-weight: bold;')
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText('أدخل أي ملاحظات إضافية...')
        notes_row.addWidget(notes_lbl)
        notes_row.addWidget(self.notes_edit)
        input_layout.addLayout(notes_row)

        # Buttons
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton('💾 حفظ التسجيل')
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self._save_record)

        self.cancel_edit_btn = QPushButton('❌ إلغاء التعديل')
        self.cancel_edit_btn.setObjectName('danger')
        self.cancel_edit_btn.setFixedHeight(40)
        self.cancel_edit_btn.setVisible(False)
        self.cancel_edit_btn.clicked.connect(self._cancel_edit)

        print_btn = QPushButton('🖨️ طباعة')
        print_btn.setObjectName('print_btn')
        print_btn.setFixedHeight(40)
        print_btn.clicked.connect(self._print_invoice)

        clear_btn = QPushButton('🗑 مسح')
        clear_btn.setObjectName('secondary')
        clear_btn.setFixedHeight(40)
        clear_btn.clicked.connect(self._clear_inputs)

        pdf_btn = QPushButton('📄 PDF')
        pdf_btn.setObjectName('info')
        pdf_btn.setFixedHeight(40)
        pdf_btn.clicked.connect(self._pdf_records)

        excel_btn = QPushButton('📊 Excel')
        excel_btn.setFixedHeight(40)
        excel_btn.setStyleSheet(
            'QPushButton { background: #1a7f37; color: #fff; border-radius: 7px;'
            ' font-weight: bold; padding: 0 10px; }'
            'QPushButton:hover { background: #2ea043; }'
        )
        excel_btn.clicked.connect(self._excel_records)

        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_edit_btn)
        btn_row.addWidget(print_btn)
        btn_row.addWidget(pdf_btn)
        btn_row.addWidget(excel_btn)
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        input_layout.addLayout(btn_row)

        layout.addWidget(input_frame)

        # ── Records section: department tabs ──
        hist_label = QLabel('📜 سجل التغذية حسب الأقسام')
        hist_label.setStyleSheet(
            'font-size: 15px; font-weight: bold; color: #58a6ff;'
            'padding: 4px 8px; background-color: #161b22; border-radius: 4px;'
        )
        layout.addWidget(hist_label)

        self.dept_tabs = QTabWidget()
        self.dept_tabs.setStyleSheet('''
            QTabWidget::pane { border: 1px solid #30363d; border-radius: 6px;
                               background: #0d1117; }
            QTabBar::tab { background: #21262d; color: #8b949e; padding: 8px 18px;
                           border-radius: 4px; margin-right: 3px; font-size: 13px; }
            QTabBar::tab:selected { background: #e3b341; color: #000000; font-weight: bold; }
            QTabBar::tab:hover:!selected { background: #30363d; color: #e6edf3; }
        ''')
        layout.addWidget(self.dept_tabs)

    def _reload_depts(self):
        current = self.dept_combo.currentText()
        self.dept_combo.blockSignals(True)
        self.dept_combo.clear()
        for d in self.db.get_departments():
            self.dept_combo.addItem(d)
        if current and self.dept_combo.findText(current) >= 0:
            self.dept_combo.setCurrentText(current)
        self.dept_combo.blockSignals(False)

    def _go_today(self):
        self.date_edit.setDate(QDate.currentDate())

    def _clear_inputs(self):
        for spin in [self.food_spin, self.qat_spin, self.lighter_spin,
                     self.cigarette_spin, self.snuff_spin]:
            spin.reset()
        self.notes_edit.clear()

    def _cancel_edit(self):
        self.editing_id = None
        self.save_btn.setText('💾 حفظ التسجيل')
        self.cancel_edit_btn.setVisible(False)
        self._clear_inputs()

    def _get_data(self):
        return {
            'date':            self.date_edit.date().toString('yyyy-MM-dd'),
            'department':      self.dept_combo.currentText(),
            'food_count':      self.food_spin.value(),
            'qat_count':       self.qat_spin.value(),
            'lighter_count':   self.lighter_spin.value(),
            'cigarette_count': self.cigarette_spin.value(),
            'snuff_count':     self.snuff_spin.value(),
            'notes':           self.notes_edit.toPlainText().strip(),
        }

    def _save_record(self):
        data = self._get_data()
        if not data['department']:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء اختيار القسم')
            return
        if all(v == 0 for k, v in data.items() if k.endswith('_count')):
            QMessageBox.warning(self, 'تنبيه', 'الرجاء إدخال قيمة واحدة على الأقل')
            return

        if self.editing_id:
            self.db.update_nutrition(self.editing_id, data)
            self._cancel_edit()
            QMessageBox.information(self, '✅ نجاح', 'تم تعديل السجل بنجاح')
        else:
            self.db.add_nutrition(data)
            self._clear_inputs()
            QMessageBox.information(self, '✅ نجاح', 'تم حفظ التسجيل بنجاح')

        self.load_records()

    def load_records(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        depts = self.db.get_departments()

        current_tab = self.dept_tabs.currentIndex()
        self.dept_tabs.blockSignals(True)
        self.dept_tabs.clear()

        for dept in depts:
            records = self.db.get_nutrition_by_date_dept(date_str, dept)
            widget = self._build_dept_widget(dept, records)
            tab_label = f'🏢 {dept}' + (f' ({len(records)})' if records else '')
            self.dept_tabs.addTab(widget, tab_label)

        self.dept_tabs.blockSignals(False)
        if 0 <= current_tab < self.dept_tabs.count():
            self.dept_tabs.setCurrentIndex(current_tab)

    def _build_dept_widget(self, dept, records):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # Summary row
        if records:
            food_total    = sum(r['food_count']     or 0 for r in records)
            qat_total     = sum(r['qat_count']      or 0 for r in records)
            lighter_total = sum(r['lighter_count']  or 0 for r in records)
            cig_total     = sum(r['cigarette_count'] or 0 for r in records)
            snuff_total   = sum(r['snuff_count']    or 0 for r in records)
            summary_lbl = QLabel(
                f'🍽 وجبات: <b style="color:#3fb950">{food_total}</b>   '
                f'🌿 قات: <b style="color:#56d364">{qat_total}</b>   '
                f'🔥 ولاعات: <b style="color:#f0883e">{lighter_total}</b>   '
                f'🚬 دخان: <b style="color:#8b949e">{cig_total}</b>   '
                f'🟤 شمة: <b style="color:#bb8009">{snuff_total}</b>'
            )
            summary_lbl.setTextFormat(Qt.RichText)
            summary_lbl.setStyleSheet('font-size: 13px; padding: 4px;')
            layout.addWidget(summary_lbl)
        else:
            empty_lbl = QLabel('لا توجد سجلات لهذا القسم في التاريخ المحدد')
            empty_lbl.setStyleSheet('color: #8b949e; font-size: 13px; padding: 8px;')
            empty_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty_lbl)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            'التاريخ', 'الوجبات', 'القات', 'الولاعات', 'الدخان', 'الشمة', 'ملاحظات', 'إجراءات'
        ])
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        table.setColumnWidth(7, 120)
        table.setShowGrid(False)
        table.verticalHeader().setDefaultSectionSize(36)

        table.setRowCount(len(records))
        for row, rec in enumerate(records):
            values = [
                rec['date'], str(rec['food_count']), str(rec['qat_count']),
                str(rec['lighter_count']), str(rec['cigarette_count']),
                str(rec['snuff_count']), rec['notes'] or ''
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 0:
                    item.setData(Qt.UserRole, rec['id'])
                table.setItem(row, col, item)

            btn_w = QWidget()
            btn_w.setStyleSheet('background: transparent;')
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(3, 3, 3, 3)
            btn_l.setSpacing(4)

            edit_btn = QPushButton('✏️')
            edit_btn.setFixedSize(32, 28)
            edit_btn.setStyleSheet(
                'background-color:#9e6a03; color:white; border-radius:4px; font-size:13px;'
            )
            edit_btn.clicked.connect(lambda _, r=rec: self._edit_record(r))

            del_btn = QPushButton('🗑')
            del_btn.setFixedSize(32, 28)
            del_btn.setStyleSheet(
                'background-color:#da3633; color:white; border-radius:4px; font-size:13px;'
            )
            del_btn.clicked.connect(lambda _, rid=rec['id']: self._delete_record(rid))

            btn_l.addWidget(edit_btn)
            btn_l.addWidget(del_btn)
            table.setCellWidget(row, 7, btn_w)

        layout.addWidget(table)
        return widget

    def _update_totals(self):
        """placeholder – kept for backward compatibility"""
        pass

    def _edit_record(self, rec):
        self.editing_id = rec['id']
        self.food_spin.set_value(rec['food_count'])
        self.qat_spin.set_value(rec['qat_count'])
        self.lighter_spin.set_value(rec['lighter_count'])
        self.cigarette_spin.set_value(rec['cigarette_count'])
        self.snuff_spin.set_value(rec['snuff_count'])
        self.notes_edit.setPlainText(rec['notes'] or '')
        if 'department' in rec.keys() and rec['department']:
            self.dept_combo.setCurrentText(rec['department'])
        self.save_btn.setText('💾 حفظ التعديل')
        self.cancel_edit_btn.setVisible(True)

    def _delete_record(self, record_id):
        reply = QMessageBox.question(
            self, 'تأكيد', 'هل تريد حذف هذا السجل؟',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_nutrition(record_id)
            self.load_records()

    def _print_invoice(self):
        data = self._get_data()
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        printing_utils.print_nutrition_invoice(self, date_str, data)

    def _pdf_records(self):
        from datetime import datetime as dt
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        depts = self.db.get_departments()
        sections_html = ''
        for dept in depts:
            records = self.db.get_nutrition_by_date_dept(date_str, dept)
            if not records:
                continue
            rows_html = ''.join(
                f'<tr><td>{r["date"]}</td><td>{r["food_count"]}</td>'
                f'<td>{r["qat_count"]}</td><td>{r["lighter_count"]}</td>'
                f'<td>{r["cigarette_count"]}</td><td>{r["snuff_count"]}</td>'
                f'<td>{r["notes"] or ""}</td></tr>'
                for r in records
            )
            sections_html += (
                f'<h3 style="color:#e3b341;margin-top:16px;">🏢 {dept}</h3>'
                f'<table><tr><th>التاريخ</th><th>وجبات</th><th>قات</th>'
                f'<th>ولاعات</th><th>دخان</th><th>شمة</th><th>ملاحظات</th></tr>'
                f'{rows_html}</table>'
            )
        html = (
            '<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><style>'
            'body{font-family:Arial,Tahoma;font-size:11pt;margin:15px;}'
            '.h{text-align:center;border-bottom:4px solid #e3b341;padding-bottom:8px;margin-bottom:12px;}'
            '.h h1{color:#e3b341;font-size:17pt;margin:0;}'
            'table{width:100%;border-collapse:collapse;margin-bottom:8px;}'
            'th{background:#e3b341;color:#000;padding:7px;text-align:right;}'
            'td{padding:5px 8px;border:1px solid #ddd;text-align:right;}'
            'tr:nth-child(even){background:#f5f5f5;}'
            '</style></head><body>'
            f'<div class="h"><h1>🍽️ سجل التغذية حسب الأقسام</h1><p>{date_str}</p></div>'
            f'{sections_html}'
            f'<div style="text-align:center;color:#888;font-size:9pt;margin-top:14px;">'
            f'طُبع في {dt.now().strftime("%Y/%m/%d %H:%M")}</div></body></html>'
        )
        export_utils.save_as_pdf(self, html, f'تغذية_{date_str}.pdf')

    def _excel_records(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        headers = ['القسم', 'التاريخ', 'الوجبات', 'القات', 'الولاعات', 'الدخان', 'الشمة', 'ملاحظات']
        rows = []
        for dept in self.db.get_departments():
            for r in self.db.get_nutrition_by_date_dept(date_str, dept):
                rows.append([dept, r['date'], r['food_count'], r['qat_count'],
                             r['lighter_count'], r['cigarette_count'],
                             r['snuff_count'], r['notes'] or ''])
        export_utils.save_as_excel(self, headers, rows, f'تغذية_{date_str}.xlsx',
                                   sheet_title=f'تغذية {date_str}')

    def refresh(self):
        self._reload_depts()
        self.load_records()
