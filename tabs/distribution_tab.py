"""
تبويب التوزيع الذكي - Smart Distribution Tab
توزيع القات والتغذية تلقائياً حسب عدد الحاضرين في كل قسم
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDateEdit,
    QPushButton, QFrame, QMessageBox, QScrollArea, QGridLayout,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from datetime import datetime


# ── helper ────────────────────────────────────────────────────────────────────
def _proportional_distribute(total: int, counts: list[int]) -> list[int]:
    """وزّع total على الأقسام بنسبة counts مع الحفاظ على المجموع الكلي."""
    total_count = sum(counts)
    if total_count == 0 or total == 0:
        return [0] * len(counts)
    floors = [int(total * c / total_count) for c in counts]
    remainder = total - sum(floors)
    # وزّع الباقي على الأقسام ذات أعلى كسر
    fracs = sorted(
        range(len(counts)),
        key=lambda i: (total * counts[i] / total_count) - floors[i],
        reverse=True
    )
    for i in range(remainder):
        floors[fracs[i]] += 1
    return floors


# ── بطاقة إدخال الكميات الإجمالية ─────────────────────────────────────────────
class TotalSpinCard(QFrame):
    def __init__(self, label, icon='', color='#58a6ff'):
        super().__init__()
        self.setObjectName('card')
        self.setMinimumWidth(130)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 10, 10, 10)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet('font-size: 26px; background: transparent;')

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f'color: {color}; font-size: 12px; font-weight: bold; background: transparent;'
        )

        self.spin = QSpinBox()
        self.spin.setRange(0, 99999)
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.setStyleSheet(
            f'font-size: 18px; font-weight: bold; color: {color}; min-height: 36px;'
        )

        layout.addWidget(icon_lbl)
        layout.addWidget(lbl)
        layout.addWidget(self.spin)

    def value(self):
        return self.spin.value()

    def reset(self):
        self.spin.setValue(0)


# ── بطاقة عرض نتيجة توزيع قسم واحد ───────────────────────────────────────────
class DeptResultCard(QFrame):
    ITEMS = [
        ('🍽', 'وجبات',  '#3fb950'),
        ('🌿', 'قات',    '#56d364'),
        ('🔥', 'ولاعات', '#f0883e'),
        ('🚬', 'دخان',   '#8b949e'),
        ('🟤', 'شمة',    '#bb8009'),
    ]

    def __init__(self, dept_name, present, total_emp, values):
        """
        dept_name  - اسم القسم
        present    - عدد الحاضرين
        total_emp  - إجمالي موظفي القسم
        values     - [food, qat, lighters, cigarettes, snuff]
        """
        super().__init__()
        self.setObjectName('card')
        self.setMinimumWidth(180)
        self.setMaximumWidth(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)

        # Department header
        dept_lbl = QLabel(f'🏢  {dept_name}')
        dept_lbl.setAlignment(Qt.AlignCenter)
        dept_lbl.setStyleSheet(
            'font-size: 15px; font-weight: bold; color: #58a6ff; background: transparent;'
        )
        layout.addWidget(dept_lbl)

        # Attendance line
        pct = int(present / total_emp * 100) if total_emp else 0
        att_lbl = QLabel(f'👥  {present} حاضر  /  {total_emp} إجمالي  ({pct}%)')
        att_lbl.setAlignment(Qt.AlignCenter)
        att_lbl.setStyleSheet(
            'font-size: 11px; color: #3fb950; background: transparent; padding-bottom: 4px;'
        )
        layout.addWidget(att_lbl)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('color: #30363d;')
        layout.addWidget(sep)

        # Values
        for (icon, label, color), val in zip(self.ITEMS, values):
            row = QHBoxLayout()
            row.setSpacing(6)

            icon_l = QLabel(f'{icon}  {label}')
            icon_l.setStyleSheet(
                f'font-size: 12px; color: {color}; background: transparent;'
            )

            val_l = QLabel(str(val))
            val_l.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            val_l.setStyleSheet(
                f'font-size: 16px; font-weight: bold; color: {color};'
                ' background: transparent;'
            )

            row.addWidget(icon_l, 1)
            row.addWidget(val_l)
            layout.addLayout(row)

        # If zero present → grey overlay message
        if present == 0:
            no_lbl = QLabel('⚠️ لا يوجد حاضرون')
            no_lbl.setAlignment(Qt.AlignCenter)
            no_lbl.setStyleSheet(
                'color: #f85149; font-size: 11px; font-weight: bold;'
                ' background: transparent; padding-top: 4px;'
            )
            layout.addWidget(no_lbl)


# ── التبويب الرئيسي ────────────────────────────────────────────────────────────
class DistributionTab(QWidget):
    data_changed = pyqtSignal()   # يُطلق بعد حفظ التوزيع

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._last_distribution = []   # [(dept, present, total, [v0..v4])]
        self._setup_ui()

    # ── بناء الواجهة ───────────────────────────────────────────────────────────
    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setSpacing(10)
        outer.setContentsMargins(10, 10, 10, 10)

        # ── العنوان ──
        title = QLabel('⚡ التوزيع الذكي للقات والتغذية')
        title.setObjectName('page_title')
        outer.addWidget(title)

        # ── قسم الإدخال ──
        input_frame = QFrame()
        input_frame.setObjectName('card')
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(10)
        input_layout.setContentsMargins(14, 12, 14, 12)

        # ─ صف التاريخ ─
        date_row = QHBoxLayout()
        date_lbl = QLabel('التاريخ:')
        date_lbl.setStyleSheet('font-size: 14px; font-weight: bold;')

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedWidth(150)
        self.date_edit.dateChanged.connect(self._on_date_changed)

        today_btn = QPushButton('📅 اليوم')
        today_btn.setObjectName('info')
        today_btn.setFixedWidth(80)
        today_btn.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))

        info_lbl = QLabel(
            'أدخل الكميات الإجمالية المتاحة، وسيقوم النظام بتوزيعها'
            ' تلقائياً حسب عدد الحاضرين في كل قسم.'
        )
        info_lbl.setStyleSheet('color: #8b949e; font-size: 11px;')
        info_lbl.setWordWrap(True)

        date_row.addWidget(date_lbl)
        date_row.addWidget(self.date_edit)
        date_row.addWidget(today_btn)
        date_row.addSpacing(20)
        date_row.addWidget(info_lbl, 1)
        input_layout.addLayout(date_row)

        # ─ بطاقات الكميات ─
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        self.food_card      = TotalSpinCard('الوجبات الغذائية', '🍽', '#3fb950')
        self.qat_card       = TotalSpinCard('القات',            '🌿', '#56d364')
        self.lighter_card   = TotalSpinCard('الولاعات',         '🔥', '#f0883e')
        self.cigarette_card = TotalSpinCard('الدخان',           '🚬', '#8b949e')
        self.snuff_card     = TotalSpinCard('الشمة',            '🟤', '#bb8009')

        for c in [self.food_card, self.qat_card, self.lighter_card,
                  self.cigarette_card, self.snuff_card]:
            cards_row.addWidget(c)
        input_layout.addLayout(cards_row)

        # ─ أزرار ─
        btn_row = QHBoxLayout()

        self.calc_btn = QPushButton('⚡ احسب التوزيع تلقائياً')
        self.calc_btn.setFixedHeight(42)
        self.calc_btn.setStyleSheet(
            'QPushButton { background: #1f6feb; color: #fff; border-radius: 8px;'
            ' font-size: 14px; font-weight: bold; padding: 0 18px; }'
            'QPushButton:hover { background: #388bfd; }'
        )
        self.calc_btn.clicked.connect(self._calculate)

        self.save_btn = QPushButton('💾 حفظ التوزيع')
        self.save_btn.setFixedHeight(42)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet(
            'QPushButton { background: #1a7f37; color: #fff; border-radius: 8px;'
            ' font-size: 14px; font-weight: bold; padding: 0 18px; }'
            'QPushButton:disabled { background: #21262d; color: #484f58; }'
            'QPushButton:hover:!disabled { background: #2ea043; }'
        )
        self.save_btn.clicked.connect(self._save_distribution)

        clear_btn = QPushButton('🗑 مسح')
        clear_btn.setObjectName('secondary')
        clear_btn.setFixedHeight(42)
        clear_btn.clicked.connect(self._clear)

        btn_row.addWidget(self.calc_btn)
        btn_row.addWidget(self.save_btn)
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        input_layout.addLayout(btn_row)

        outer.addWidget(input_frame)

        # ── لوحة النتائج ──
        self.summary_lbl = QLabel('')
        self.summary_lbl.setStyleSheet(
            'font-size: 14px; font-weight: bold; color: #e3b341;'
            ' padding: 6px 10px; background: #161b22; border-radius: 4px;'
        )
        self.summary_lbl.setVisible(False)
        outer.addWidget(self.summary_lbl)

        # منطقة قابلة للتمرير لبطاقات الأقسام
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet('QScrollArea { background: transparent; }')

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet('background: transparent;')
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setSpacing(12)
        self.cards_grid.setContentsMargins(4, 4, 4, 4)

        scroll.setWidget(self.cards_container)
        outer.addWidget(scroll, 1)

    # ── منطق الحساب ───────────────────────────────────────────────────────────
    def _on_date_changed(self):
        # إعادة ضبط النتائج عند تغيير التاريخ
        self._clear_results()

    def _clear(self):
        for c in [self.food_card, self.qat_card, self.lighter_card,
                  self.cigarette_card, self.snuff_card]:
            c.reset()
        self._clear_results()

    def _clear_results(self):
        self._last_distribution = []
        self.save_btn.setEnabled(False)
        self.summary_lbl.setVisible(False)
        # إزالة جميع البطاقات
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _calculate(self):
        date_str = self.date_edit.date().toString('yyyy-MM-dd')

        # جلب الحضور حسب القسم
        dept_data = self.db.get_attendance_by_dept(date_str)
        if not dept_data:
            QMessageBox.warning(self, 'تنبيه',
                                'لا يوجد موظفون مسجلون في النظام.\n'
                                'يرجى إضافة الموظفين أولاً.')
            return

        # الكميات الإجمالية
        totals = [
            self.food_card.value(),
            self.qat_card.value(),
            self.lighter_card.value(),
            self.cigarette_card.value(),
            self.snuff_card.value(),
        ]

        if all(v == 0 for v in totals):
            QMessageBox.warning(self, 'تنبيه',
                                'الرجاء إدخال كمية واحدة على الأقل.')
            return

        # حساب عدد الحاضرين لكل قسم
        dept_names   = list(dept_data.keys())
        dept_present = []
        dept_total   = []
        for dept, emps in dept_data.items():
            p = sum(1 for e in emps if e.get('status') == 'حاضر')
            dept_present.append(p)
            dept_total.append(len(emps))

        total_present = sum(dept_present)

        # توزيع كل بند بشكل مستقل
        distributed = []
        for total_val in totals:
            distributed.append(
                _proportional_distribute(total_val, dept_present)
            )
        # distributed[item_idx][dept_idx]

        # بناء النتائج
        self._last_distribution = []
        for di, dept in enumerate(dept_names):
            values = [distributed[item][di] for item in range(5)]
            self._last_distribution.append({
                'dept': dept,
                'present': dept_present[di],
                'total': dept_total[di],
                'values': values,
            })

        # ── عرض الملخص ──
        self.summary_lbl.setText(
            f'📊  إجمالي الحاضرين: {total_present} موظف  |  '
            f'عدد الأقسام: {len(dept_names)}  |  '
            f'تاريخ: {date_str}'
        )
        self.summary_lbl.setVisible(True)

        # ── رسم البطاقات ──
        self._clear_results_keep_data()
        COLS = 4
        for idx, entry in enumerate(self._last_distribution):
            card = DeptResultCard(
                entry['dept'], entry['present'],
                entry['total'], entry['values']
            )
            self.cards_grid.addWidget(card, idx // COLS, idx % COLS)

        self.save_btn.setEnabled(True)

        # إعادة إظهار الملخص (قد أزيل في _clear_results_keep_data)
        self.summary_lbl.setVisible(True)

    def _clear_results_keep_data(self):
        """تنظيف البطاقات فقط دون مسح البيانات المحسوبة."""
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── حفظ التوزيع ───────────────────────────────────────────────────────────
    def _save_distribution(self):
        if not self._last_distribution:
            return

        date_str = self.date_edit.date().toString('yyyy-MM-dd')

        # تحقق من وجود سجلات سابقة
        existing = self.db.get_nutrition_by_date(date_str)
        if existing:
            reply = QMessageBox.question(
                self, 'تنبيه',
                f'يوجد {len(existing)} سجل مسجّل مسبقاً لهذا اليوم ({date_str}).\n'
                'هل تريد إضافة التوزيع الجديد بجانب السجلات الموجودة؟',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        saved = 0
        for entry in self._last_distribution:
            if entry['present'] == 0:
                continue  # لا تسجل للأقسام التي ليس بها حاضرون
            vals = entry['values']
            data = {
                'date':            date_str,
                'department':      entry['dept'],
                'food_count':      vals[0],
                'qat_count':       vals[1],
                'lighter_count':   vals[2],
                'cigarette_count': vals[3],
                'snuff_count':     vals[4],
                'notes':           'توزيع تلقائي حسب الحضور',
            }
            self.db.add_nutrition(data)
            saved += 1

        QMessageBox.information(
            self, '✅ تم الحفظ',
            f'تم حفظ التوزيع لـ {saved} قسم بنجاح.\n'
            'يمكنك مراجعة التفاصيل في تبويب التغذية.'
        )
        self.save_btn.setEnabled(False)
        self.data_changed.emit()

    # ── refresh (يُستدعى عند تفعيل التبويب) ─────────────────────────────────
    def refresh(self):
        # أعد الحساب تلقائياً إذا كان هناك توزيع محسوب مسبقاً
        if self._last_distribution:
            self._calculate()
