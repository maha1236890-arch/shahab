"""
تبويب التغذية - Nutrition Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDateEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFrame, QTextEdit, QMessageBox, QGridLayout
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

        # Date row
        date_row = QHBoxLayout()
        date_label = QLabel('تاريخ التسجيل:')
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

        date_row.addWidget(date_label)
        date_row.addWidget(self.date_edit)
        date_row.addWidget(today_btn)
        date_row.addStretch()
        input_layout.addLayout(date_row)

        # Spin cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        self.food_spin = SpinCard('الوجبات الغذائية', '🍽', '#3fb950')
        self.qat_spin = SpinCard('القات', '🌿', '#56d364')
        self.lighter_spin = SpinCard('الولاعات', '🔥', '#f0883e')
        self.cigarette_spin = SpinCard('الدخان', '🚬', '#8b949e')
        self.snuff_spin = SpinCard('الشمة', '🟤', '#bb8009')

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

        print_btn = QPushButton('🖨️ طباعة فاتورة')
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

        # History table
        hist_label = QLabel('📜 سجل التغذية')
        hist_label.setStyleSheet(
            'font-size: 15px; font-weight: bold; color: #58a6ff;'
            'padding: 4px 8px; background-color: #161b22; border-radius: 4px;'
        )
        layout.addWidget(hist_label)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'التاريخ', 'الوجبات', 'القات', 'الولاعات', 'الدخان', 'الشمة', 'ملاحظات', 'إجراءات'
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 160)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.table)

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
            'date': self.date_edit.date().toString('yyyy-MM-dd'),
            'food_count': self.food_spin.value(),
            'qat_count': self.qat_spin.value(),
            'lighter_count': self.lighter_spin.value(),
            'cigarette_count': self.cigarette_spin.value(),
            'snuff_count': self.snuff_spin.value(),
            'notes': self.notes_edit.toPlainText().strip(),
        }

    def _save_record(self):
        data = self._get_data()
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
        records = self.db.get_nutrition_by_date(date_str)

        self.table.setRowCount(len(records))
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
                self.table.setItem(row, col, item)

            # Action buttons
            btn_w = QWidget()
            btn_w.setStyleSheet('background: transparent;')
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(3, 3, 3, 3)
            btn_l.setSpacing(4)

            edit_btn = QPushButton('✏️')
            edit_btn.setFixedSize(32, 28)
            edit_btn.setStyleSheet('background-color:#9e6a03; color:white; border-radius:4px; font-size:13px;')
            edit_btn.clicked.connect(lambda _, r=rec: self._edit_record(r))

            del_btn = QPushButton('🗑')
            del_btn.setFixedSize(32, 28)
            del_btn.setStyleSheet('background-color:#da3633; color:white; border-radius:4px; font-size:13px;')
            del_btn.clicked.connect(lambda _, rid=rec['id']: self._delete_record(rid))

            btn_l.addWidget(edit_btn)
            btn_l.addWidget(del_btn)
            self.table.setCellWidget(row, 7, btn_w)

    def _edit_record(self, rec):
        self.editing_id = rec['id']
        self.food_spin.set_value(rec['food_count'])
        self.qat_spin.set_value(rec['qat_count'])
        self.lighter_spin.set_value(rec['lighter_count'])
        self.cigarette_spin.set_value(rec['cigarette_count'])
        self.snuff_spin.set_value(rec['snuff_count'])
        self.notes_edit.setPlainText(rec['notes'] or '')
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
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        records  = self.db.get_nutrition_by_date(date_str)
        from datetime import datetime
        rows_html = ''.join(
            f'<tr><td>{r["real_name"]}</td><td>{r["code"]}</td>'
            f'<td>{r["department"] or ""}</td><td>{r["meal_type"]}</td>'
            f'<td>{r["count"]}</td><td>{r["price"]}</td></tr>'
            for r in records
        )
        html = (
            '<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><style>'
            'body{font-family:Arial,Tahoma;font-size:11pt;margin:15px;}'
            '.h{text-align:center;border-bottom:4px solid #e3b341;padding-bottom:8px;margin-bottom:12px;}'
            '.h h1{color:#e3b341;font-size:17pt;margin:0;}'
            'table{width:100%;border-collapse:collapse;}'
            'th{background:#e3b341;color:#000;padding:7px;text-align:right;}'
            'td{padding:5px 8px;border:1px solid #ddd;text-align:right;}'
            'tr:nth-child(even){background:#f5f5f5;}'
            '</style></head><body>'
            f'<div class="h"><h1>🍽️ سجل الوجبات</h1><p>{date_str}</p></div>'
            '<table><tr><th>الاسم</th><th>الكود</th><th>القسم</th>'
            '<th>نوع الوجبة</th><th>العدد</th><th>السعر</th></tr>'
            f'{rows_html}</table>'
            f'<div style="text-align:center;color:#888;font-size:9pt;margin-top:14px;">'
            f'طُبع في {datetime.now().strftime("%Y/%m/%d %H:%M")}</div></body></html>'
        )
        export_utils.save_as_pdf(self, html, f'وجبات_{date_str}.pdf')

    def _excel_records(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')
        records  = self.db.get_nutrition_by_date(date_str)
        headers  = ['الاسم', 'الكود', 'القسم', 'نوع الوجبة', 'العدد', 'السعر']
        rows = [[r['real_name'], r['code'], r['department'] or '',
                 r['meal_type'], r['count'], r['price']]
                for r in records]
        export_utils.save_as_excel(self, headers, rows, f'وجبات_{date_str}.xlsx',
                                   sheet_title=f'وجبات {date_str}')

    def refresh(self):
        self.load_records()
