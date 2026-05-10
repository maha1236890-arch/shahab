"""
قاعدة بيانات نظام إدارة الموظفين
Employee Management System Database
"""

import sqlite3
from datetime import datetime
import os
import sys

# When running as a PyInstaller bundle on Windows, store the database in
# %APPDATA%\نظام_الموظفين\ so it is always writable even when the exe is
# installed in Program Files.  On Linux keep the old behaviour (next to the
# executable or the source file).
if getattr(sys, 'frozen', False):
    if sys.platform == 'win32':
        _appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        _BASE_DIR = os.path.join(_appdata, 'نظام_الموظفين')
    else:
        _BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(_BASE_DIR, exist_ok=True)
DB_PATH = os.path.join(_BASE_DIR, 'employee_system.db')


class Database:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.db_path = DB_PATH
        self.create_tables()
        self.insert_sample_data()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def create_tables(self):
        with self.get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    real_name TEXT NOT NULL,
                    job_name TEXT NOT NULL,
                    code TEXT NOT NULL UNIQUE,
                    marital_status TEXT NOT NULL DEFAULT 'أعزب',
                    governorate TEXT DEFAULT '',
                    department TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    time_in TEXT,
                    time_out TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                    UNIQUE(employee_id, date)
                );

                CREATE TABLE IF NOT EXISTS nutrition (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    food_count INTEGER DEFAULT 0,
                    qat_count INTEGER DEFAULT 0,
                    lighter_count INTEGER DEFAULT 0,
                    cigarette_count INTEGER DEFAULT 0,
                    snuff_count INTEGER DEFAULT 0,
                    notes TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    visit_type TEXT DEFAULT 'عادية',
                    entry_time TEXT,
                    exit_time TEXT,
                    date TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS qat_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    function_name TEXT DEFAULT '',
                    count INTEGER DEFAULT 0,
                    lighter_count INTEGER DEFAULT 0,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
                CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(date);
                CREATE INDEX IF NOT EXISTS idx_employees_code ON employees(code);
                CREATE INDEX IF NOT EXISTS idx_employees_dept ON employees(department);

                CREATE TABLE IF NOT EXISTS archived_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    report_date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    html_content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_reports_date ON archived_reports(report_date);
                CREATE INDEX IF NOT EXISTS idx_reports_type ON archived_reports(report_type);

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'data_entry',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                );

                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    action TEXT NOT NULL,
                    details TEXT DEFAULT '',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_log_timestamp ON activity_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_log_user ON activity_log(user_id);
            ''')
        # Migration: add department column to nutrition if it doesn't exist
        with self.get_connection() as conn:
            try:
                conn.execute("ALTER TABLE nutrition ADD COLUMN department TEXT NOT NULL DEFAULT ''")
            except Exception:
                pass  # Column already exists

        # Create default admin if no users exist
        self._ensure_default_admin()

    def _ensure_default_admin(self):
        with self.get_connection() as conn:
            count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            if count == 0:
                conn.execute('''
                    INSERT INTO users (username, password, full_name, role)
                    VALUES (?, ?, ?, ?)
                ''', ('admin', 'admin123', 'مدير النظام', 'admin'))

    def insert_sample_data(self):
        with self.get_connection() as conn:
            count = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
            if count == 0:
                sample_employees = [
                    ('أحمد محمد علي', 'مدير قسم', 'EMP001', 'متزوج', 'صنعاء', 'الإدارة', '777123456'),
                    ('محمد عبدالله حسن', 'محاسب', 'EMP002', 'أعزب', 'عدن', 'المالية', '777234567'),
                    ('علي أحمد سالم', 'مهندس', 'EMP003', 'متزوج', 'تعز', 'الهندسة', '777345678'),
                    ('خالد عمر يوسف', 'فني', 'EMP004', 'أعزب', 'إب', 'الهندسة', '777456789'),
                    ('سالم حسن محمد', 'مشرف', 'EMP005', 'متزوج', 'حضرموت', 'العمليات', '777567890'),
                    ('عمر يحيى علي', 'موظف إداري', 'EMP006', 'أعزب', 'المحويت', 'الإدارة', '777678901'),
                    ('حسن أحمد ناصر', 'محاسب مساعد', 'EMP007', 'متزوج', 'ذمار', 'المالية', '777789012'),
                    ('يوسف عبدالرحمن', 'مهندس مدني', 'EMP008', 'أعزب', 'صنعاء', 'الهندسة', '777890123'),
                    ('ناصر علي محمد', 'أمين مخزن', 'EMP009', 'متزوج', 'الحديدة', 'العمليات', '777901234'),
                    ('عبدالله سعيد', 'سكرتير', 'EMP010', 'أعزب', 'مأرب', 'الإدارة', '777012345'),
                ]
                conn.executemany('''
                    INSERT INTO employees (real_name, job_name, code, marital_status, governorate, department, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', sample_employees)

    # ===== EMPLOYEES =====
    def get_all_employees(self):
        with self.get_connection() as conn:
            return conn.execute('SELECT * FROM employees ORDER BY department, id').fetchall()

    def get_employee_by_code(self, code):
        with self.get_connection() as conn:
            return conn.execute('SELECT * FROM employees WHERE code=?', (code.strip(),)).fetchone()

    def get_employee_by_id(self, emp_id):
        with self.get_connection() as conn:
            return conn.execute('SELECT * FROM employees WHERE id=?', (emp_id,)).fetchone()

    def add_employee(self, data):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO employees (real_name, job_name, code, marital_status, governorate, department, phone)
                VALUES (:real_name, :job_name, :code, :marital_status, :governorate, :department, :phone)
            ''', data)

    def update_employee(self, emp_id, data):
        with self.get_connection() as conn:
            data['id'] = emp_id
            conn.execute('''
                UPDATE employees SET real_name=:real_name, job_name=:job_name, code=:code,
                marital_status=:marital_status, governorate=:governorate, department=:department,
                phone=:phone WHERE id=:id
            ''', data)

    def delete_employee(self, emp_id):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM employees WHERE id=?', (emp_id,))

    def search_employees(self, query):
        with self.get_connection() as conn:
            q = f'%{query}%'
            return conn.execute('''
                SELECT * FROM employees
                WHERE real_name LIKE ? OR job_name LIKE ? OR code LIKE ? OR department LIKE ? OR phone LIKE ?
                ORDER BY department, id
            ''', (q, q, q, q, q)).fetchall()

    # ===== ATTENDANCE =====
    def mark_attendance(self, employee_id, date, status, time_in=None):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO attendance (employee_id, date, status, time_in)
                VALUES (?, ?, ?, ?)
            ''', (employee_id, date, status, time_in or datetime.now().strftime('%H:%M')))

    def update_time_out(self, employee_id, date, time_out):
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE attendance SET time_out=? WHERE employee_id=? AND date=?',
                (time_out, employee_id, date)
            )

    def get_attendance_by_date(self, date):
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT a.*, e.real_name, e.job_name, e.code, e.department, e.phone, e.marital_status
                FROM attendance a JOIN employees e ON a.employee_id=e.id
                WHERE a.date=? ORDER BY e.department, e.id
            ''', (date,)).fetchall()

    def get_present_employees(self, date):
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT e.*, a.time_in, a.time_out
                FROM attendance a JOIN employees e ON a.employee_id=e.id
                WHERE a.date=? AND a.status='حاضر'
                ORDER BY e.department, e.id
            ''', (date,)).fetchall()

    def get_attendance_stats(self, date):
        with self.get_connection() as conn:
            present = conn.execute(
                "SELECT COUNT(*) FROM attendance WHERE date=? AND status='حاضر'", (date,)
            ).fetchone()[0]
            absent = conn.execute(
                "SELECT COUNT(*) FROM attendance WHERE date=? AND status='غائب'", (date,)
            ).fetchone()[0]
            total = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
            return present, absent, total

    # ===== NUTRITION =====
    def add_nutrition(self, data):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO nutrition (date, department, food_count, qat_count, lighter_count,
                                       cigarette_count, snuff_count, notes)
                VALUES (:date, :department, :food_count, :qat_count, :lighter_count,
                        :cigarette_count, :snuff_count, :notes)
            ''', data)

    def get_nutrition_by_date(self, date):
        with self.get_connection() as conn:
            return conn.execute(
                'SELECT * FROM nutrition WHERE date=? ORDER BY department, created_at DESC', (date,)
            ).fetchall()

    def get_nutrition_by_date_dept(self, date, department):
        with self.get_connection() as conn:
            return conn.execute(
                'SELECT * FROM nutrition WHERE date=? AND department=? ORDER BY created_at DESC',
                (date, department)
            ).fetchall()

    def update_nutrition(self, record_id, data):
        with self.get_connection() as conn:
            data['id'] = record_id
            conn.execute('''
                UPDATE nutrition SET food_count=:food_count, qat_count=:qat_count,
                lighter_count=:lighter_count, cigarette_count=:cigarette_count,
                snuff_count=:snuff_count, notes=:notes WHERE id=:id
            ''', data)

    def delete_nutrition(self, record_id):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM nutrition WHERE id=?', (record_id,))

    def get_nutrition_monthly(self, year, month):
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT date, SUM(food_count), SUM(qat_count), SUM(lighter_count),
                       SUM(cigarette_count), SUM(snuff_count)
                FROM nutrition WHERE date LIKE ?
                GROUP BY date ORDER BY date
            ''', (f'{year}-{month:02d}-%',)).fetchall()

    # ===== VISITS =====
    def add_visit(self, employee_id, visit_type, entry_time, date, notes=''):
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO visits (employee_id, visit_type, entry_time, date, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (employee_id, visit_type, entry_time, date, notes))
            return cursor.lastrowid

    def update_visit_exit(self, visit_id, exit_time):
        with self.get_connection() as conn:
            conn.execute('UPDATE visits SET exit_time=? WHERE id=?', (exit_time, visit_id))

    def get_visits_by_date(self, date):
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT v.*, e.real_name, e.job_name, e.code, e.department, e.governorate,
                       e.marital_status, e.phone
                FROM visits v JOIN employees e ON v.employee_id=e.id
                WHERE v.date=? ORDER BY v.entry_time DESC
            ''', (date,)).fetchall()

    def get_open_visits(self, date):
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT v.*, e.real_name, e.job_name, e.code, e.department
                FROM visits v JOIN employees e ON v.employee_id=e.id
                WHERE v.date=? AND (v.exit_time IS NULL OR v.exit_time='')
                ORDER BY v.entry_time DESC
            ''', (date,)).fetchall()

    # ===== QAT =====
    def add_qat_record(self, employee_id, date, function_name, count, lighter_count):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO qat_records (employee_id, date, function_name, count, lighter_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (employee_id, date, function_name, count, lighter_count))

    def get_qat_by_date(self, date):
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT q.*, e.job_name, e.code, e.department, e.real_name
                FROM qat_records q JOIN employees e ON q.employee_id=e.id
                WHERE q.date=? ORDER BY e.department, e.id
            ''', (date,)).fetchall()

    def get_qat_by_date_dept(self, date, department):
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT q.*, e.job_name, e.code, e.department, e.real_name
                FROM qat_records q JOIN employees e ON q.employee_id=e.id
                WHERE q.date=? AND e.department=?
                ORDER BY e.id
            ''', (date, department)).fetchall()

    def update_qat_record(self, record_id, function_name, count, lighter_count):
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE qat_records SET function_name=?, count=?, lighter_count=? WHERE id=?
            ''', (function_name, count, lighter_count, record_id))

    def delete_qat_record(self, record_id):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM qat_records WHERE id=?', (record_id,))

    # ===== DEPARTMENTS =====
    def get_departments(self):
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT DISTINCT department FROM employees
                WHERE department IS NOT NULL AND department != ''
                ORDER BY department
            ''').fetchall()
            return [r[0] for r in rows]

    def get_department_stats(self):
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT department, COUNT(*) as count
                FROM employees WHERE department IS NOT NULL AND department != ''
                GROUP BY department ORDER BY department
            ''').fetchall()

    def get_employees_by_department(self, department):
        with self.get_connection() as conn:
            return conn.execute(
                'SELECT * FROM employees WHERE department=? ORDER BY id', (department,)
            ).fetchall()

    # ===== REPORTS =====
    def get_monthly_attendance_report(self, year, month):
        with self.get_connection() as conn:
            return conn.execute('''
                SELECT e.id, e.real_name, e.job_name, e.code, e.department,
                       COUNT(CASE WHEN a.status='حاضر' THEN 1 END) as present_days,
                       COUNT(CASE WHEN a.status='غائب' THEN 1 END) as absent_days,
                       COUNT(a.id) as total_recorded
                FROM employees e
                LEFT JOIN attendance a ON e.id=a.employee_id AND a.date LIKE ?
                GROUP BY e.id ORDER BY e.department, e.id
            ''', (f'{year}-{month:02d}-%',)).fetchall()

    def get_daily_summary(self, date):
        with self.get_connection() as conn:
            stats = {}
            stats['present'] = conn.execute(
                "SELECT COUNT(*) FROM attendance WHERE date=? AND status='حاضر'", (date,)
            ).fetchone()[0]
            stats['absent'] = conn.execute(
                "SELECT COUNT(*) FROM attendance WHERE date=? AND status='غائب'", (date,)
            ).fetchone()[0]
            stats['total_employees'] = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
            stats['visits'] = conn.execute(
                'SELECT COUNT(*) FROM visits WHERE date=?', (date,)
            ).fetchone()[0]
            nutrition = conn.execute(
                'SELECT SUM(food_count), SUM(qat_count) FROM nutrition WHERE date=?', (date,)
            ).fetchone()
            stats['food'] = nutrition[0] or 0
            stats['qat_food'] = nutrition[1] or 0
            return stats

    # ===== ARCHIVED REPORTS =====
    def save_report(self, report_type, report_date, title, html_content):
        """أرشفة تقرير في قاعدة البيانات"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO archived_reports (report_type, report_date, title, html_content)
                VALUES (?, ?, ?, ?)
            ''', (report_type, report_date, title, html_content))
            return cursor.lastrowid

    def get_archived_reports(self, report_type=None, limit=100):
        """جلب التقارير المؤرشفة"""
        with self.get_connection() as conn:
            if report_type:
                return conn.execute('''
                    SELECT id, report_type, report_date, title, created_at
                    FROM archived_reports WHERE report_type=?
                    ORDER BY created_at DESC LIMIT ?
                ''', (report_type, limit)).fetchall()
            return conn.execute('''
                SELECT id, report_type, report_date, title, created_at
                FROM archived_reports ORDER BY created_at DESC LIMIT ?
            ''', (limit,)).fetchall()

    def get_report_html(self, report_id):
        """جلب محتوى تقرير مؤرشف"""
        with self.get_connection() as conn:
            row = conn.execute(
                'SELECT html_content FROM archived_reports WHERE id=?', (report_id,)
            ).fetchone()
            return row['html_content'] if row else None

    def delete_report(self, report_id):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM archived_reports WHERE id=?', (report_id,))

    def get_attendance_by_dept(self, date):
        """جلب الحضور مجمّعاً حسب القسم"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT e.department,
                       e.id AS emp_id, e.real_name, e.job_name, e.code,
                       a.status, a.time_in
                FROM employees e
                LEFT JOIN attendance a ON e.id=a.employee_id AND a.date=?
                ORDER BY e.department, e.id
            ''', (date,)).fetchall()
            # Group by department
            from collections import OrderedDict
            result = OrderedDict()
            for r in rows:
                dept = r['department'] or 'غير محدد'
                if dept not in result:
                    result[dept] = []
                result[dept].append(dict(r))
            return result

    # ===== USERS =====
    def get_user_by_credentials(self, username, password):
        with self.get_connection() as conn:
            return conn.execute(
                'SELECT * FROM users WHERE username=? AND password=? AND is_active=1',
                (username, password)
            ).fetchone()

    def update_last_login(self, user_id):
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE users SET last_login=? WHERE id=?',
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id)
            )

    def get_all_users(self):
        with self.get_connection() as conn:
            return conn.execute(
                'SELECT * FROM users ORDER BY role, username'
            ).fetchall()

    def add_user(self, username, password, full_name, role):
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO users (username, password, full_name, role) VALUES (?,?,?,?)',
                (username, password, full_name, role)
            )

    def update_user(self, user_id, full_name, role, is_active, password=None):
        with self.get_connection() as conn:
            if password:
                conn.execute(
                    'UPDATE users SET full_name=?, role=?, is_active=?, password=? WHERE id=?',
                    (full_name, role, is_active, password, user_id)
                )
            else:
                conn.execute(
                    'UPDATE users SET full_name=?, role=?, is_active=? WHERE id=?',
                    (full_name, role, is_active, user_id)
                )

    def delete_user(self, user_id):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM users WHERE id=?', (user_id,))

    def change_password(self, user_id, new_password):
        with self.get_connection() as conn:
            conn.execute('UPDATE users SET password=? WHERE id=?', (new_password, user_id))

    # ===== ACTIVITY LOG =====
    def log_action(self, user_id, username, action, details=''):
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO activity_log (user_id, username, action, details) VALUES (?,?,?,?)',
                (user_id, username, action, details)
            )

    def get_activity_log(self, limit=200, user_id=None):
        with self.get_connection() as conn:
            if user_id:
                return conn.execute(
                    'SELECT * FROM activity_log WHERE user_id=? ORDER BY timestamp DESC LIMIT ?',
                    (user_id, limit)
                ).fetchall()
            return conn.execute(
                'SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?',
                (limit,)
            ).fetchall()
