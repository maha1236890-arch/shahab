"""
أنماط التصميم العصري المتطور للنظام - Advanced Dark Theme
"""


def get_stylesheet():
    return """
    /* === Main Window === */
    QMainWindow, QDialog {
        background-color: #0d1117;
        color: #c9d1d9;
    }

    QWidget {
        font-family: 'Arial', 'Tahoma', sans-serif;
        font-size: 13px;
        color: #c9d1d9;
        background-color: #0d1117;
    }

    /* === Tab Widget === */
    QTabWidget::pane {
        border: 1px solid #21262d;
        background-color: #0d1117;
        border-radius: 0 0 10px 10px;
        margin-top: -1px;
    }

    QTabBar {
        background: transparent;
    }

    QTabBar::tab {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1c2128, stop:1 #161b22);
        color: #6e7681;
        padding: 10px 16px;
        margin: 0 1px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border: 1px solid #21262d;
        border-bottom: none;
        font-size: 12px;
        font-weight: bold;
        min-width: 80px;
    }

    QTabBar::tab:selected {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1f6feb, stop:1 #1658c7);
        color: #ffffff;
        border-color: #1f6feb;
    }

    QTabBar::tab:hover:!selected {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #2d333b, stop:1 #21262d);
        color: #e6edf3;
        border-color: #30363d;
    }

    /* === Buttons === */
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #2ea043, stop:1 #238636);
        color: #ffffff;
        border: 1px solid rgba(46,160,67,102);
        padding: 8px 18px;
        border-radius: 7px;
        font-size: 13px;
        font-weight: bold;
        min-height: 34px;
    }

    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #3fb950, stop:1 #2ea043);
        border-color: #3fb950;
    }

    QPushButton:pressed {
        background: #1a7f37;
        padding-top: 9px;
        padding-bottom: 7px;
    }

    QPushButton:disabled {
        background: #21262d;
        color: #484f58;
        border-color: #21262d;
    }

    QPushButton#danger {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #f85149, stop:1 #da3633);
        border-color: rgba(248,81,73,102);
    }

    QPushButton#danger:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #ff6b6b, stop:1 #f85149);
    }

    QPushButton#warning {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #bb8009, stop:1 #9e6a03);
        border-color: rgba(187,128,9,102);
    }

    QPushButton#warning:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #d4a017, stop:1 #bb8009);
    }

    QPushButton#info {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #388bfd, stop:1 #1f6feb);
        border-color: rgba(56,139,253,102);
    }

    QPushButton#info:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #58a6ff, stop:1 #388bfd);
    }

    QPushButton#secondary {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #2d333b, stop:1 #21262d);
        border: 1px solid #30363d;
        color: #c9d1d9;
    }

    QPushButton#secondary:hover {
        background: #30363d;
        border-color: rgba(88,166,255,68);
        color: #e6edf3;
    }

    QPushButton#print_btn {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #a371f7, stop:1 #8250df);
        border-color: rgba(163,113,247,102);
    }

    QPushButton#print_btn:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #bc8cfa, stop:1 #a371f7);
    }

    /* === Toast Notification === */
    QFrame#toast_success {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #002200, stop:1 #0a1f0a);
        border: 1px solid #3fb950;
        border-left: 4px solid #3fb950;
        border-radius: 10px;
    }
    QFrame#toast_error {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1f0000, stop:1 #1a0505);
        border: 1px solid #f85149;
        border-left: 4px solid #f85149;
        border-radius: 10px;
    }
    QFrame#toast_warning {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1f1500, stop:1 #1a1205);
        border: 1px solid #e3b341;
        border-left: 4px solid #e3b341;
        border-radius: 10px;
    }
    QFrame#toast_info {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #001a2a, stop:1 #051520);
        border: 1px solid #58a6ff;
        border-left: 4px solid #58a6ff;
        border-radius: 10px;
    }

    /* === Input Fields === */
    QLineEdit, QSpinBox, QDateEdit, QTimeEdit {
        background-color: #21262d;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 6px 10px;
        color: #c9d1d9;
        font-size: 13px;
        min-height: 32px;
        selection-background-color: #1f6feb;
    }

    QLineEdit:focus, QSpinBox:focus, QDateEdit:focus {
        border: 1px solid #1f6feb;
        background-color: #0d1117;
    }

    QLineEdit::placeholder {
        color: #484f58;
    }

    QComboBox {
        background-color: #21262d;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 6px 10px;
        color: #c9d1d9;
        font-size: 13px;
        min-height: 32px;
    }

    QComboBox:focus {
        border: 1px solid #1f6feb;
    }

    QComboBox::drop-down {
        border: none;
        padding-right: 8px;
    }

    QComboBox QAbstractItemView {
        background-color: #21262d;
        border: 1px solid #30363d;
        color: #c9d1d9;
        selection-background-color: #1f6feb;
        outline: none;
    }

    QTextEdit {
        background-color: #21262d;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 6px;
        color: #c9d1d9;
        font-size: 13px;
    }

    QTextEdit:focus {
        border: 1px solid #1f6feb;
    }

    /* === Tables === */
    QTableWidget {
        background-color: #161b22;
        alternate-background-color: #1c2128;
        border: 1px solid #30363d;
        border-radius: 8px;
        gridline-color: #21262d;
        color: #c9d1d9;
        font-size: 13px;
        outline: none;
    }

    QTableWidget::item {
        padding: 6px 8px;
        border: none;
        min-height: 32px;
    }

    QTableWidget::item:selected {
        background-color: #1f6feb;
        color: #ffffff;
    }

    QTableWidget::item:hover {
        background-color: #2d333b;
    }

    QHeaderView::section {
        background-color: #21262d;
        color: #8b949e;
        padding: 8px 6px;
        border: none;
        border-right: 1px solid #30363d;
        border-bottom: 2px solid #30363d;
        font-weight: bold;
        font-size: 12px;
    }

    QHeaderView::section:first {
        border-top-right-radius: 8px;
    }

    /* === Group Box === */
    QGroupBox {
        border: 1px solid #30363d;
        border-radius: 8px;
        margin-top: 14px;
        padding: 12px 8px 8px 8px;
        color: #58a6ff;
        font-weight: bold;
        font-size: 14px;
        background-color: #161b22;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top right;
        padding: 2px 10px;
        background-color: #0d1117;
        border-radius: 4px;
        color: #58a6ff;
    }

    /* === Labels === */
    QLabel {
        color: #c9d1d9;
        font-size: 13px;
        background: transparent;
    }

    QLabel#page_title {
        font-size: 20px;
        font-weight: bold;
        color: #58a6ff;
        padding: 4px 0;
    }

    QLabel#stat_value {
        font-size: 28px;
        font-weight: bold;
        padding: 2px;
    }

    QLabel#stat_title {
        font-size: 12px;
        color: #8b949e;
    }

    QLabel#info_label {
        font-size: 15px;
        font-weight: bold;
        color: #e6edf3;
        padding: 4px 8px;
        background-color: #21262d;
        border-radius: 4px;
        border: 1px solid #30363d;
    }

    QLabel#section_title {
        font-size: 15px;
        font-weight: bold;
        color: #3fb950;
        padding: 6px 10px;
        background-color: #1a3a1a;
        border-radius: 6px;
        border-right: 4px solid #3fb950;
    }

    /* === Frames / Cards === */
    QFrame#card {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #161b22, stop:1 #1c2128);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 8px;
    }

    QFrame#stat_card {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #1c2128, stop:1 #21262d);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 12px;
        min-width: 120px;
    }

    QFrame#header_frame {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #0d1117, stop:0.5 #162032, stop:1 #0d1117);
        border: none;
        border-bottom: 2px solid #1f6feb;
        border-radius: 0;
    }

    /* === Scroll Bars === */
    QScrollBar:vertical {
        background-color: #0d1117;
        width: 8px;
        border-radius: 4px;
        margin: 2px;
    }

    QScrollBar::handle:vertical {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1f6feb, stop:1 #388bfd);
        border-radius: 4px;
        min-height: 30px;
    }

    QScrollBar::handle:vertical:hover {
        background: #58a6ff;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        background-color: #0d1117;
        height: 8px;
        border-radius: 4px;
        margin: 2px;
    }

    QScrollBar::handle:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1f6feb, stop:1 #388bfd);
        border-radius: 4px;
    }

    QScrollBar::handle:horizontal:hover {
        background: #58a6ff;
    }

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    /* === Status Bar === */
    QStatusBar {
        background-color: #161b22;
        color: #8b949e;
        border-top: 1px solid #30363d;
        font-size: 12px;
    }

    /* === Splitter === */
    QSplitter::handle {
        background-color: #30363d;
        width: 2px;
    }

    /* === Check Box === */
    QCheckBox {
        color: #c9d1d9;
        spacing: 6px;
    }

    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #30363d;
        border-radius: 4px;
        background-color: #21262d;
    }

    QCheckBox::indicator:checked {
        background-color: #238636;
        border-color: #238636;
    }

    /* === Message Box === */
    QMessageBox {
        background-color: #161b22;
    }

    QMessageBox QLabel {
        color: #c9d1d9;
    }

    QMessageBox QPushButton {
        min-width: 80px;
    }

    /* === List Widget === */
    QListWidget {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        color: #c9d1d9;
        font-size: 13px;
        outline: none;
    }

    QListWidget::item {
        padding: 10px 12px;
        border-bottom: 1px solid #21262d;
    }

    QListWidget::item:selected {
        background-color: #1f6feb;
        color: white;
    }

    QListWidget::item:hover {
        background-color: #2d333b;
    }

    /* === Calendar === */
    QCalendarWidget {
        background-color: #161b22;
        color: #c9d1d9;
    }

    QCalendarWidget QTableView {
        background-color: #161b22;
        selection-background-color: #1f6feb;
    }

    /* === Spin Box arrows === */
    QSpinBox::up-button, QSpinBox::down-button {
        background-color: #30363d;
        border: none;
        border-radius: 3px;
        width: 20px;
    }

    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: #8b949e;
    }

    /* === Date Edit === */
    QDateEdit::drop-down {
        border: none;
        padding-right: 4px;
    }

    /* === Tool Tip === */
    QToolTip {
        background-color: #21262d;
        border: 1px solid #30363d;
        color: #c9d1d9;
        padding: 4px 8px;
        border-radius: 4px;
    }
    """
