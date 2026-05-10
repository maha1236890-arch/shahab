"""
نافذة تسجيل الدخول - Login Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class LoginDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_user = None
        self.setWindowTitle('تسجيل الدخول - نظام إدارة الموظفين')
        self.setFixedSize(420, 520)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet('''
            QFrame {
                background: #0d1117;
                border: 2px solid #1f6feb;
                border-radius: 16px;
            }
        ''')
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(18)

        # Logo + title
        logo = QLabel('🔐')
        logo.setStyleSheet('font-size: 52px; background: transparent;')
        logo.setAlignment(Qt.AlignCenter)

        title = QLabel('نظام إدارة الموظفين')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #58a6ff; background: transparent;')
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel('تسجيل الدخول')
        subtitle.setStyleSheet('font-size: 14px; color: #8b949e; background: transparent;')
        subtitle.setAlignment(Qt.AlignCenter)

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet('color: #21262d; background: #21262d; max-height: 1px;')
        layout.addWidget(div)

        # Username
        user_lbl = QLabel('اسم المستخدم')
        user_lbl.setStyleSheet('color: #c9d1d9; font-size: 13px; background: transparent;')
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('أدخل اسم المستخدم...')
        self.username_input.setFixedHeight(44)
        self.username_input.setStyleSheet('''
            QLineEdit {
                background: #161b22; color: #e6edf3;
                border: 1px solid #30363d; border-radius: 8px;
                padding: 0 12px; font-size: 14px;
            }
            QLineEdit:focus { border-color: #1f6feb; }
        ''')

        # Password
        pass_lbl = QLabel('كلمة المرور')
        pass_lbl.setStyleSheet('color: #c9d1d9; font-size: 13px; background: transparent;')
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('أدخل كلمة المرور...')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(44)
        self.password_input.setStyleSheet('''
            QLineEdit {
                background: #161b22; color: #e6edf3;
                border: 1px solid #30363d; border-radius: 8px;
                padding: 0 12px; font-size: 14px;
            }
            QLineEdit:focus { border-color: #1f6feb; }
        ''')
        self.password_input.returnPressed.connect(self._do_login)

        # Show password checkbox
        self.show_pass_chk = QCheckBox('إظهار كلمة المرور')
        self.show_pass_chk.setStyleSheet('color: #8b949e; font-size: 12px; background: transparent;')
        self.show_pass_chk.toggled.connect(
            lambda checked: self.password_input.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )

        layout.addWidget(user_lbl)
        layout.addWidget(self.username_input)
        layout.addWidget(pass_lbl)
        layout.addWidget(self.password_input)
        layout.addWidget(self.show_pass_chk)

        # Error label
        self.error_label = QLabel('')
        self.error_label.setStyleSheet(
            'color: #f85149; font-size: 12px; background: transparent; padding: 4px;'
        )
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        # Login button
        login_btn = QPushButton('دخول')
        login_btn.setFixedHeight(48)
        login_btn.setStyleSheet('''
            QPushButton {
                background: #1f6feb; color: white; font-size: 16px;
                font-weight: bold; border-radius: 8px; border: none;
            }
            QPushButton:hover { background: #388bfd; }
            QPushButton:pressed { background: #1158c7; }
        ''')
        login_btn.clicked.connect(self._do_login)
        layout.addWidget(login_btn)

        # Default hint
        hint = QLabel('المستخدم الافتراضي: admin  |  كلمة المرور: admin123')
        hint.setStyleSheet('color: #484f58; font-size: 11px; background: transparent;')
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        # Pre-fill for convenience (remove in production)
        self.username_input.setFocus()

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error('يرجى إدخال اسم المستخدم وكلمة المرور')
            return

        user = self.db.get_user_by_credentials(username, password)
        if user:
            self.db.update_last_login(user['id'])
            self.db.log_action(user['id'], user['username'], 'تسجيل دخول',
                               f'دخول من قبل: {user["full_name"]}')
            self.current_user = dict(user)
            self.accept()
        else:
            self._show_error('اسم المستخدم أو كلمة المرور غير صحيحة')
            self.password_input.clear()
            self.password_input.setFocus()

    def _show_error(self, msg):
        self.error_label.setText(f'⚠️  {msg}')
        self.error_label.show()
