"""
تبويب تصاريح الخروج - Exit Permits Tab
إصدار واسترجاع وطباعة تصاريح الخروج للموظفين
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QTimeEdit, QPushButton, QFrame,
    QScrollArea, QGridLayout, QSizePolicy, QMessageBox,
    QDialog, QDialogButtonBox, QTextEdit, QCompleter,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QAbstractItemView, QApplication, QSplitter
)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal, QSortFilterProxyModel, QStringListModel
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from datetime import datetime
import export_utils


# ── نموذج إنشاء تصريح ─────────────────────────────────────────────────────────

class PermitFormDialog(QDialog):
    """نافذة حوار لإدخال بيانات تصريح الخروج"""

    def __init__(self, db, parent=None, permit_data=None):
        super().__init__(parent)
        self.db = db
        self.permit_data = permit_data  # للتعديل مستقبلاً
        self.setWindowTitle('إصدار تصريح خروج')
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(500)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── عنوان ──
        title = QLabel('🚗  إصدار تصريح خروج جديد')
        title.setStyleSheet('font-size:15px;font-weight:bold;color:#3fb950;padding:4px;')
        layout.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('color:#30363d;'); layout.addWidget(sep)

        grid = QGridLayout(); grid.setSpacing(8)

        # ─ بحث الموظف ─
        grid.addWidget(QLabel('الموظف (اختياري):'), 0, 0)
        self.emp_combo = QComboBox()
        self.emp_combo.setEditable(True)
        self.emp_combo.setPlaceholderText('ابحث أو أدخل الاسم الوظيفي...')
        self._load_employees()
        self.emp_combo.currentIndexChanged.connect(self._on_emp_selected)
        grid.addWidget(self.emp_combo, 0, 1)

        # ─ الاسم الوظيفي ─
        grid.addWidget(QLabel('الاسم الوظيفي *:'), 1, 0)
        self.job_name_edit = QLineEdit()
        self.job_name_edit.setPlaceholderText('الاسم الوظيفي للموظف')
        grid.addWidget(self.job_name_edit, 1, 1)

        # ─ الكود ─
        grid.addWidget(QLabel('الكود *:'), 2, 0)
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText('كود الموظف')
        grid.addWidget(self.code_edit, 2, 1)

        # ─ القسم ─
        grid.addWidget(QLabel('القسم:'), 3, 0)
        self.dept_combo = QComboBox()
        self.dept_combo.addItem('')
        for d in self.db.get_departments():
            self.dept_combo.addItem(d)
        grid.addWidget(self.dept_combo, 3, 1)

        # ─ تاريخ الخروج ─
        grid.addWidget(QLabel('تاريخ الخروج *:'), 4, 0)
        self.exit_date = QDateEdit(QDate.currentDate())
        self.exit_date.setCalendarPopup(True)
        self.exit_date.setDisplayFormat('yyyy-MM-dd')
        grid.addWidget(self.exit_date, 4, 1)

        # ─ وقت الخروج ─
        grid.addWidget(QLabel('وقت الخروج *:'), 5, 0)
        self.exit_time = QTimeEdit(QTime.currentTime())
        self.exit_time.setDisplayFormat('HH:mm')
        grid.addWidget(self.exit_time, 5, 1)

        # ─ سبب الخروج ─
        grid.addWidget(QLabel('سبب الخروج:'), 6, 0)
        self.reason_edit = QLineEdit()
        self.reason_edit.setPlaceholderText('مهمة رسمية / زيارة طبية / ...')
        grid.addWidget(self.reason_edit, 6, 1)

        # ─ اسم السائق ─
        grid.addWidget(QLabel('اسم السائق:'), 7, 0)
        self.driver_edit = QLineEdit()
        self.driver_edit.setPlaceholderText('اسم السائق إن وُجد')
        grid.addWidget(self.driver_edit, 7, 1)

        # ─ نوع الوسيلة ─
        grid.addWidget(QLabel('نوع الوسيلة:'), 8, 0)
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.addItems(['سيارة', 'باص', 'دراجة نارية', 'سيارة أجرة', 'مشياً', 'أخرى'])
        grid.addWidget(self.vehicle_combo, 8, 1)

        # ─ تاريخ التصريح ─
        grid.addWidget(QLabel('تاريخ التصريح:'), 9, 0)
        self.permit_date = QDateEdit(QDate.currentDate())
        self.permit_date.setCalendarPopup(True)
        self.permit_date.setDisplayFormat('yyyy-MM-dd')
        grid.addWidget(self.permit_date, 9, 1)

        # ─ حجم الطباعة ─
        grid.addWidget(QLabel('حجم الطباعة:'), 10, 0)
        self.size_combo = QComboBox()
        self.size_combo.addItems(['A5 (افتراضي)', 'A4'])
        grid.addWidget(self.size_combo, 10, 1)

        layout.addLayout(grid)

        # ── ملاحظة الحقول الإلزامية ──
        note = QLabel('* حقل إلزامي')
        note.setStyleSheet('color:#8b949e;font-size:10px;')
        layout.addWidget(note)

        # ── أزرار ──
        btn_row = QHBoxLayout()
        self.issue_btn = QPushButton('🖨️  إصدار وطباعة')
        self.issue_btn.setObjectName('success')
        self.issue_btn.clicked.connect(self._issue)
        save_btn = QPushButton('💾  حفظ بدون طباعة')
        save_btn.clicked.connect(self._save_only)
        cancel_btn = QPushButton('إلغاء')
        cancel_btn.setObjectName('danger')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.issue_btn)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self._last_permit_id = None

    def _load_employees(self):
        self._employees = self.db.get_all_employees()
        self.emp_combo.addItem('-- لا يوجد --', None)
        for emp in self._employees:
            label = f"{emp['job_name']}  [{emp['code']}]  {emp['department']}"
            self.emp_combo.addItem(label, emp['id'])
        self.emp_combo.setCurrentIndex(0)

    def _on_emp_selected(self, idx):
        if idx <= 0:
            return
        emp_id = self.emp_combo.itemData(idx)
        if emp_id is None:
            return
        for emp in self._employees:
            if emp['id'] == emp_id:
                self.job_name_edit.setText(emp['job_name'])
                self.code_edit.setText(emp['code'])
                dept_idx = self.dept_combo.findText(emp['department'] or '')
                if dept_idx >= 0:
                    self.dept_combo.setCurrentIndex(dept_idx)
                break

    def _collect_data(self):
        job_name = self.job_name_edit.text().strip()
        code     = self.code_edit.text().strip()
        if not job_name or not code:
            QMessageBox.warning(self, 'تنبيه', 'الاسم الوظيفي والكود حقول إلزامية.')
            return None
        emp_id = self.emp_combo.currentData()
        return {
            'employee_id':  emp_id,
            'job_name':     job_name,
            'code':         code,
            'department':   self.dept_combo.currentText(),
            'exit_date':    self.exit_date.date().toString('yyyy-MM-dd'),
            'exit_time':    self.exit_time.time().toString('HH:mm'),
            'reason':       self.reason_edit.text().strip(),
            'driver_name':  self.driver_edit.text().strip(),
            'vehicle_type': self.vehicle_combo.currentText(),
            'permit_date':  self.permit_date.date().toString('yyyy-MM-dd'),
        }

    def _save_only(self):
        data = self._collect_data()
        if data is None:
            return
        permit_id = self.db.add_exit_permit(data)
        self._last_permit_id = permit_id
        QMessageBox.information(self, '✅ تم الحفظ',
                                f'تم حفظ تصريح الخروج رقم {permit_id}.')
        self.accept()

    def _issue(self):
        data = self._collect_data()
        if data is None:
            return
        permit_id = self.db.add_exit_permit(data)
        self._last_permit_id = permit_id
        data['id'] = permit_id
        size = 'A4' if 'A4' in self.size_combo.currentText() else 'A5'
        _print_permit(self, data, size)
        self.accept()

    def get_last_permit_id(self):
        return self._last_permit_id


# ── توليد HTML للتصريح ────────────────────────────────────────────────────────

def _build_permit_html(data: dict) -> str:
    permit_no = data.get('id', '---')
    job_name  = data.get('job_name', '')
    code      = data.get('code', '')
    dept      = data.get('department', '')
    exit_date = data.get('exit_date', '')
    exit_time = data.get('exit_time', '')
    reason    = data.get('reason', '') or '—'
    driver    = data.get('driver_name', '') or '—'
    vehicle   = data.get('vehicle_type', '')
    pdate     = data.get('permit_date', datetime.now().strftime('%Y-%m-%d'))
    printed   = datetime.now().strftime('%Y/%m/%d  %H:%M')

    return f'''<!DOCTYPE html>
<html dir="rtl">
<head>
<meta charset="utf-8">
<style>
  @page {{ size: A5; margin: 10mm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: Arial, Tahoma, sans-serif;
    font-size: 12pt;
    color: #000;
    background: #fff;
    padding: 6mm;
  }}
  .header {{
    text-align: center;
    border-bottom: 3px double #1a5276;
    padding-bottom: 6px;
    margin-bottom: 8px;
  }}
  .header h1 {{
    font-size: 16pt;
    color: #1a5276;
    letter-spacing: 1px;
  }}
  .header .subtitle {{
    font-size: 10pt;
    color: #555;
    margin-top: 2px;
  }}
  .permit-no {{
    display: inline-block;
    background: #1a5276;
    color: #fff;
    font-size: 11pt;
    font-weight: bold;
    padding: 3px 12px;
    border-radius: 3px;
    margin-top: 4px;
  }}
  .info-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
  }}
  .info-table td {{
    padding: 6px 8px;
    border: 1px solid #aaa;
    vertical-align: middle;
  }}
  .info-table .lbl {{
    background: #d6eaf8;
    font-weight: bold;
    width: 38%;
    color: #1a5276;
  }}
  .info-table .val {{
    background: #fff;
    width: 62%;
  }}
  .highlight-row td {{
    background: #eaf4fc !important;
  }}
  .footer {{
    margin-top: 14px;
    border-top: 1px solid #aaa;
    padding-top: 8px;
    font-size: 9pt;
    color: #555;
    text-align: center;
  }}
  .sig-row {{
    display: flex;
    justify-content: space-between;
    margin-top: 16px;
    font-size: 10pt;
  }}
  .sig-box {{
    text-align: center;
    border-top: 1px solid #555;
    padding-top: 4px;
    width: 30%;
    font-weight: bold;
  }}
</style>
</head>
<body>
  <div class="header">
    <h1>تصريح خروج</h1>
    <div class="subtitle">نظام إدارة الموظفين</div>
    <div class="permit-no">رقم التصريح: {permit_no}</div>
  </div>

  <table class="info-table">
    <tr class="highlight-row">
      <td class="lbl">الاسم الوظيفي</td>
      <td class="val">{job_name}</td>
    </tr>
    <tr>
      <td class="lbl">الكود</td>
      <td class="val">{code}</td>
    </tr>
    <tr class="highlight-row">
      <td class="lbl">القسم</td>
      <td class="val">{dept}</td>
    </tr>
    <tr>
      <td class="lbl">تاريخ الخروج</td>
      <td class="val">{exit_date}</td>
    </tr>
    <tr class="highlight-row">
      <td class="lbl">وقت الخروج</td>
      <td class="val">{exit_time}</td>
    </tr>
    <tr>
      <td class="lbl">سبب الخروج</td>
      <td class="val">{reason}</td>
    </tr>
    <tr class="highlight-row">
      <td class="lbl">اسم السائق</td>
      <td class="val">{driver}</td>
    </tr>
    <tr>
      <td class="lbl">نوع الوسيلة</td>
      <td class="val">{vehicle}</td>
    </tr>
    <tr class="highlight-row">
      <td class="lbl">تاريخ التصريح</td>
      <td class="val">{pdate}</td>
    </tr>
  </table>

  <div class="sig-row">
    <div class="sig-box">توقيع الموظف</div>
    <div class="sig-box">توقيع المشرف</div>
    <div class="sig-box">حارس البوابة</div>
  </div>

  <div class="footer">
    صدر في: {printed}  |  هذا التصريح صالح ليوم إصداره فقط
  </div>
</body>
</html>'''


def _print_permit(parent, data: dict, size: str = 'A5'):
    """طباعة التصريح مباشرة إلى الطابعة"""
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        _print_via_webengine(parent, data, size)
        return
    except ImportError:
        pass

    # Fallback: QTextEdit print
    from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
    from PyQt5.QtWidgets import QTextEdit

    printer = QPrinter(QPrinter.HighResolution)
    if size == 'A4':
        printer.setPageSize(QPrinter.A4)
    else:
        printer.setPageSize(QPrinter.A5)
    printer.setOrientation(QPrinter.Portrait)

    html = _build_permit_html(data)

    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle('معاينة التصريح قبل الطباعة')
    preview.resize(700, 900)

    te = QTextEdit()
    te.setHtml(html)

    def do_print(p):
        te.print_(p)

    preview.paintRequested.connect(do_print)
    preview.exec_()


def _print_via_webengine(parent, data, size):
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(QPrinter.A4 if size == 'A4' else QPrinter.A5)
    printer.setOrientation(QPrinter.Portrait)
    html = _build_permit_html(data)
    view = QWebEngineView()
    view.setHtml(html)
    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle('معاينة التصريح')
    preview.resize(700, 900)
    preview.paintRequested.connect(view.print_)
    preview.exec_()


# ── تبويب تصاريح الخروج ──────────────────────────────────────────────────────

class ExitPermitTab(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ── شريط الأدوات ──
        toolbar = QHBoxLayout()

        title_lbl = QLabel('🚗  تصاريح الخروج')
        title_lbl.setStyleSheet('font-size:15px;font-weight:bold;color:#3fb950;')
        toolbar.addWidget(title_lbl)
        toolbar.addStretch()

        new_btn = QPushButton('➕  إصدار تصريح جديد')
        new_btn.setObjectName('success')
        new_btn.clicked.connect(self._new_permit)
        toolbar.addWidget(new_btn)

        refresh_btn = QPushButton('🔄  تحديث')
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # ── فلتر التاريخ ──
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel('عرض تصاريح يوم:'))

        self.filter_date = QDateEdit(QDate.currentDate())
        self.filter_date.setCalendarPopup(True)
        self.filter_date.setDisplayFormat('yyyy-MM-dd')
        self.filter_date.dateChanged.connect(self._load_table)
        filter_row.addWidget(self.filter_date)

        today_btn = QPushButton('اليوم')
        today_btn.setFixedWidth(65)
        today_btn.clicked.connect(lambda: self.filter_date.setDate(QDate.currentDate()))
        filter_row.addWidget(today_btn)
        filter_row.addStretch()

        self.count_lbl = QLabel('')
        self.count_lbl.setStyleSheet('color:#8b949e;font-size:11px;')
        filter_row.addWidget(self.count_lbl)

        layout.addLayout(filter_row)

        # ── جدول التصاريح ──
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'رقم', 'الاسم الوظيفي', 'الكود', 'القسم',
            'تاريخ الخروج', 'وقت الخروج', 'سبب الخروج',
            'السائق', 'نوع الوسيلة'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setLayoutDirection(Qt.RightToLeft)
        layout.addWidget(self.table)

        # ── أزرار سجل محدد ──
        act_row = QHBoxLayout()
        print_btn = QPushButton('🖨️  طباعة المحدد')
        print_btn.clicked.connect(self._print_selected)
        delete_btn = QPushButton('🗑  حذف المحدد')
        delete_btn.setObjectName('danger')
        delete_btn.clicked.connect(self._delete_selected)

        size_lbl = QLabel('حجم الطباعة:')
        self.size_combo = QComboBox()
        self.size_combo.addItems(['A5 (افتراضي)', 'A4'])
        self.size_combo.setFixedWidth(120)

        act_row.addWidget(print_btn)
        act_row.addWidget(size_lbl)
        act_row.addWidget(self.size_combo)
        act_row.addStretch()
        act_row.addWidget(delete_btn)
        layout.addLayout(act_row)

        self._load_table()

    def _load_table(self):
        date_str = self.filter_date.date().toString('yyyy-MM-dd')
        permits = self.db.get_exit_permits_by_date(date_str)
        self.table.setRowCount(len(permits))
        for row, p in enumerate(permits):
            vals = [
                str(p['id']),
                p['job_name'],
                p['code'],
                p['department'] or '',
                p['exit_date'],
                p['exit_time'],
                p['reason'] or '',
                p['driver_name'] or '',
                p['vehicle_type'] or '',
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, col, item)

        self.count_lbl.setText(f'عدد التصاريح: {len(permits)}')

    def _new_permit(self):
        dlg = PermitFormDialog(self.db, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_table()
            self.data_changed.emit()

    def _get_selected_permit(self):
        rows = self.table.selectedItems()
        if not rows:
            QMessageBox.information(self, 'تنبيه', 'الرجاء تحديد تصريح من القائمة.')
            return None
        row = self.table.currentRow()
        permit_id = int(self.table.item(row, 0).text())
        return self.db.get_exit_permit(permit_id)

    def _print_selected(self):
        permit = self._get_selected_permit()
        if permit is None:
            return
        data = dict(permit)
        size = 'A4' if 'A4' in self.size_combo.currentText() else 'A5'
        _print_permit(self, data, size)

    def _delete_selected(self):
        permit = self._get_selected_permit()
        if permit is None:
            return
        reply = QMessageBox.question(
            self, 'تأكيد الحذف',
            f'هل تريد حذف تصريح رقم {permit["id"]} للموظف {permit["job_name"]}؟',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_exit_permit(permit['id'])
            self._load_table()
            self.data_changed.emit()

    def refresh(self):
        self._load_table()
