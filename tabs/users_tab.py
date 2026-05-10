"""
تبويب إدارة المستخدمين والصلاحيات - Users Management Tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox,
    QHeaderView, QAbstractItemView, QTabWidget, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

ROLES = {
    'admin':       'مدير النظام',
    'attendance':  'مسؤول الحضور',
    'data_entry':  'موظف إدخال بيانات',
    'viewer':      'مشاهد فقط',
}


class UserDialog(QDialog):
    def __init__(self, parent, db, user=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.setWindowTitle('تعديل مستخدم' if user else 'إضافة مستخدم')
        self.setFixedWidth(380)
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel('✏️ تعديل مستخدم' if self.user else '➕ مستخدم جديد')
        title.setStyleSheet('font-size: 16px; font-weight: bold; color: #58a6ff; padding: 4px;')
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.username_input = QLineEdit()
        self.fullname_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('اتركه فارغاً للإبقاء على الحالية' if self.user else 'مطلوب')

        self.role_combo = QComboBox()
        for role_key, role_name in ROLES.items():
            self.role_combo.addItem(role_name, role_key)

        self.active_chk = QCheckBox('الحساب نشط')
        self.active_chk.setChecked(True)

        form.addRow('اسم المستخدم:', self.username_input)
        form.addRow('الاسم الكامل:', self.fullname_input)
        form.addRow('كلمة المرور:', self.password_input)
        form.addRow('الصلاحية:', self.role_combo)
        form.addRow('', self.active_chk)
        layout.addLayout(form)

        if self.user:
            self.username_input.setText(self.user['username'])
            self.username_input.setReadOnly(True)
            self.fullname_input.setText(self.user['full_name'])
            idx = self.role_combo.findData(self.user['role'])
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)
            self.active_chk.setChecked(bool(self.user['is_active']))

        btn_row = QHBoxLayout()
        save_btn = QPushButton('حفظ')
        save_btn.setStyleSheet('background:#238636; color:white; font-weight:bold; padding:8px 20px; border-radius:6px;')
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton('إلغاء')
        cancel_btn.setStyleSheet('background:#21262d; color:#c9d1d9; padding:8px 20px; border-radius:6px;')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _save(self):
        username = self.username_input.text().strip()
        full_name = self.fullname_input.text().strip()
        password = self.password_input.text()
        role = self.role_combo.currentData()
        is_active = 1 if self.active_chk.isChecked() else 0

        if not username or not full_name:
            QMessageBox.warning(self, 'خطأ', 'اسم المستخدم والاسم الكامل مطلوبان')
            return
        if not self.user and not password:
            QMessageBox.warning(self, 'خطأ', 'كلمة المرور مطلوبة للمستخدم الجديد')
            return

        try:
            if self.user:
                self.db.update_user(self.user['id'], full_name, role, is_active,
                                    password if password else None)
            else:
                self.db.add_user(username, password, full_name, role)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, 'خطأ', f'اسم المستخدم موجود مسبقاً أو حدث خطأ:\n{e}')


class UsersTab(QWidget):
    def __init__(self, db, current_user):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        self.load_users()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        inner_tabs = QTabWidget()
        layout.addWidget(inner_tabs)

        # ─── Tab 1: Users ───
        users_widget = QWidget()
        users_layout = QVBoxLayout(users_widget)
        users_layout.setSpacing(8)

        toolbar = QHBoxLayout()
        title = QLabel('👤 إدارة المستخدمين')
        title.setObjectName('page_title')

        add_btn = QPushButton('➕ إضافة مستخدم')
        add_btn.setStyleSheet('background:#238636; color:white; font-weight:bold; padding:6px 14px; border-radius:6px;')
        add_btn.clicked.connect(self._add_user)

        edit_btn = QPushButton('✏️ تعديل')
        edit_btn.setObjectName('warning')
        edit_btn.clicked.connect(self._edit_user)

        delete_btn = QPushButton('🗑️ حذف')
        delete_btn.setObjectName('danger')
        delete_btn.clicked.connect(self._delete_user)

        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        users_layout.addLayout(toolbar)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            'الرقم', 'اسم المستخدم', 'الاسم الكامل', 'الصلاحية', 'الحالة', 'آخر دخول'
        ])
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.users_table.setShowGrid(False)
        self.users_table.verticalHeader().setDefaultSectionSize(38)
        self.users_table.doubleClicked.connect(self._edit_user)
        users_layout.addWidget(self.users_table)

        inner_tabs.addTab(users_widget, '👤  المستخدمون')

        # ─── Tab 2: Activity Log ───
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setSpacing(8)

        log_toolbar = QHBoxLayout()
        log_title = QLabel('📋 سجل النشاط')
        log_title.setObjectName('page_title')

        refresh_btn = QPushButton('🔄 تحديث')
        refresh_btn.setObjectName('secondary')
        refresh_btn.clicked.connect(self.load_log)

        clear_info = QLabel('آخر 200 عملية')
        clear_info.setStyleSheet('color: #8b949e; font-size: 12px;')

        log_toolbar.addWidget(log_title)
        log_toolbar.addStretch()
        log_toolbar.addWidget(clear_info)
        log_toolbar.addWidget(refresh_btn)
        log_layout.addLayout(log_toolbar)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(['التوقيت', 'المستخدم', 'العملية', 'التفاصيل'])
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.log_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.log_table.setShowGrid(False)
        self.log_table.verticalHeader().setDefaultSectionSize(36)
        log_layout.addWidget(self.log_table)

        inner_tabs.addTab(log_widget, '📋  سجل النشاط')

        # ─── Tab 3: Change Password ───
        pwd_widget = QWidget()
        pwd_layout = QVBoxLayout(pwd_widget)
        pwd_layout.setContentsMargins(40, 40, 40, 40)
        pwd_layout.setSpacing(14)

        pwd_title = QLabel('🔑 تغيير كلمة المرور')
        pwd_title.setStyleSheet('font-size: 18px; font-weight: bold; color: #58a6ff;')
        pwd_layout.addWidget(pwd_title)

        self.old_pass = QLineEdit()
        self.old_pass.setPlaceholderText('كلمة المرور الحالية')
        self.old_pass.setEchoMode(QLineEdit.Password)
        self.old_pass.setFixedHeight(42)

        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText('كلمة المرور الجديدة')
        self.new_pass.setEchoMode(QLineEdit.Password)
        self.new_pass.setFixedHeight(42)

        self.confirm_pass = QLineEdit()
        self.confirm_pass.setPlaceholderText('تأكيد كلمة المرور الجديدة')
        self.confirm_pass.setEchoMode(QLineEdit.Password)
        self.confirm_pass.setFixedHeight(42)

        change_btn = QPushButton('تغيير كلمة المرور')
        change_btn.setFixedHeight(44)
        change_btn.setStyleSheet('background:#238636; color:white; font-size:14px; font-weight:bold; border-radius:8px;')
        change_btn.clicked.connect(self._change_password)

        self.pwd_msg = QLabel('')
        self.pwd_msg.setAlignment(Qt.AlignCenter)

        pwd_layout.addWidget(QLabel('كلمة المرور الحالية:'))
        pwd_layout.addWidget(self.old_pass)
        pwd_layout.addWidget(QLabel('كلمة المرور الجديدة:'))
        pwd_layout.addWidget(self.new_pass)
        pwd_layout.addWidget(QLabel('تأكيد كلمة المرور:'))
        pwd_layout.addWidget(self.confirm_pass)
        pwd_layout.addWidget(change_btn)
        pwd_layout.addWidget(self.pwd_msg)
        pwd_layout.addStretch()

        inner_tabs.addTab(pwd_widget, '🔑  تغيير كلمة المرور')

    def load_users(self):
        users = self.db.get_all_users()
        self.users_table.setRowCount(len(users))
        for row, u in enumerate(users):
            role_name = ROLES.get(u['role'], u['role'])
            is_active = '✅ نشط' if u['is_active'] else '🔴 موقوف'
            last_login = u['last_login'] or 'لم يسجّل دخول بعد'
            values = [str(u['id']), u['username'], u['full_name'], role_name, is_active, last_login]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 0:
                    item.setData(Qt.UserRole, u['id'])
                self.users_table.setItem(row, col, item)
            # Color by active status
            color = '#1a3a1a' if u['is_active'] else '#2a1a1a'
            for col in range(6):
                it = self.users_table.item(row, col)
                if it:
                    it.setBackground(QColor(color))
            # Color role
            role_colors = {'admin': '#f0883e', 'attendance': '#58a6ff', 'data_entry': '#3fb950', 'viewer': '#8b949e'}
            role_item = self.users_table.item(row, 3)
            if role_item:
                role_item.setForeground(QColor(role_colors.get(u['role'], '#c9d1d9')))

    def load_log(self):
        logs = self.db.get_activity_log(limit=200)
        self.log_table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            values = [log['timestamp'], log['username'] or '', log['action'], log['details'] or '']
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.log_table.setItem(row, col, item)

    def _add_user(self):
        dlg = UserDialog(self, self.db)
        if dlg.exec_():
            self.db.log_action(self.current_user['id'], self.current_user['username'],
                               'إضافة مستخدم', f'اسم المستخدم: {dlg.username_input.text()}')
            self.load_users()

    def _edit_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            return
        user_id = self.users_table.item(row, 0).data(Qt.UserRole)
        users = self.db.get_all_users()
        user = next((u for u in users if u['id'] == user_id), None)
        if not user:
            return
        dlg = UserDialog(self, self.db, dict(user))
        if dlg.exec_():
            self.db.log_action(self.current_user['id'], self.current_user['username'],
                               'تعديل مستخدم', f'اسم المستخدم: {user["username"]}')
            self.load_users()

    def _delete_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            return
        user_id = self.users_table.item(row, 0).data(Qt.UserRole)
        username = self.users_table.item(row, 1).text()
        if username == self.current_user['username']:
            QMessageBox.warning(self, 'خطأ', 'لا يمكن حذف حسابك الخاص')
            return
        reply = QMessageBox.question(self, 'تأكيد الحذف',
                                     f'هل تريد حذف المستخدم: {username}؟',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_user(user_id)
            self.db.log_action(self.current_user['id'], self.current_user['username'],
                               'حذف مستخدم', f'اسم المستخدم: {username}')
            self.load_users()

    def _change_password(self):
        old = self.old_pass.text()
        new = self.new_pass.text()
        confirm = self.confirm_pass.text()

        if not old or not new:
            self.pwd_msg.setStyleSheet('color:#f85149;')
            self.pwd_msg.setText('⚠️ يرجى ملء جميع الحقول')
            return
        # Verify old password
        user = self.db.get_user_by_credentials(self.current_user['username'], old)
        if not user:
            self.pwd_msg.setStyleSheet('color:#f85149;')
            self.pwd_msg.setText('❌ كلمة المرور الحالية غير صحيحة')
            return
        if new != confirm:
            self.pwd_msg.setStyleSheet('color:#f85149;')
            self.pwd_msg.setText('❌ كلمة المرور الجديدة وتأكيدها غير متطابقتين')
            return
        self.db.change_password(self.current_user['id'], new)
        self.db.log_action(self.current_user['id'], self.current_user['username'],
                           'تغيير كلمة المرور', '')
        self.pwd_msg.setStyleSheet('color:#3fb950;')
        self.pwd_msg.setText('✅ تم تغيير كلمة المرور بنجاح')
        self.old_pass.clear()
        self.new_pass.clear()
        self.confirm_pass.clear()

    def refresh(self):
        self.load_users()
        self.load_log()
