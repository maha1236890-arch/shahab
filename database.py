"""
database.py - نظام الحضور والغياب
إدارة قاعدة البيانات SQLite
"""

import sqlite3
import hashlib
import os
import shutil
from datetime import datetime, date as _date, timedelta

def _default_db_path() -> str:
    """مسار قاعدة البيانات في مجلد قابل للكتابة"""
    import sys
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~/.config")
    d = os.path.join(base, "Shahab")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "attendance.db")

DB_PATH = os.environ.get("DB_PATH", _default_db_path())


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash_password(password: str, salt: str = None):
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return hashed, salt


def _verify_password(password: str, hashed: str, salt: str) -> bool:
    check, _ = _hash_password(password, salt)
    return check == hashed


def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            password_salt TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'employee',
            full_name     TEXT    NOT NULL,
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS employees (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code    TEXT    UNIQUE NOT NULL,
            full_name        TEXT    NOT NULL,
            department       TEXT,
            organization     TEXT,
            position         TEXT,
            phone            TEXT,
            email            TEXT,
            hire_date        TEXT,
            status           TEXT    DEFAULT 'active',
            max_absent_days  INTEGER DEFAULT 0,
            max_vacation_days INTEGER DEFAULT 0,
            max_sick_days     INTEGER DEFAULT 0,
            max_work_days     INTEGER DEFAULT 0,
            branch           TEXT
        );

        CREATE TABLE IF NOT EXISTS branches (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    UNIQUE NOT NULL,
            address    TEXT,
            manager    TEXT,
            is_active  INTEGER DEFAULT 1,
            created_at TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            date        TEXT    NOT NULL,
            status      TEXT    NOT NULL,
            check_in    TEXT,
            check_out   TEXT,
            exit_type   TEXT,
            notes       TEXT,
            recorded_by INTEGER REFERENCES users(id),
            recorded_at TEXT    DEFAULT (datetime('now')),
            UNIQUE(employee_id, date)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS holidays (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            date         TEXT    NOT NULL,
            is_recurring INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            username   TEXT,
            action     TEXT NOT NULL,
            details    TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    # إنشاء حساب أدمن افتراضي إن لم يوجد
    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cur.fetchone()[0] == 0:
        pw_hash, pw_salt = _hash_password("admin123")
        cur.execute(
            "INSERT INTO users (username, password_hash, password_salt, role, full_name) "
            "VALUES (?, ?, ?, 'admin', ?)",
            ("admin", pw_hash, pw_salt, "المدير")
        )
        # علّم بأنه أول تشغيل
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('first_run', '1')")

    # إعدادات افتراضية
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('app_version', '2.0.0')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('first_run', '0')")

    # ترحيل: إضافة الأعمدة الجديدة إن لم تكن موجودة (للقواعد القديمة)
    existing_emp_cols = {row[1] for row in cur.execute("PRAGMA table_info(employees)").fetchall()}
    if "organization" not in existing_emp_cols:
        cur.execute("ALTER TABLE employees ADD COLUMN organization TEXT")

    existing_att_cols = {row[1] for row in cur.execute("PRAGMA table_info(attendance)").fetchall()}
    if "exit_type" not in existing_att_cols:
        cur.execute("ALTER TABLE attendance ADD COLUMN exit_type TEXT")

    # ترحيل: is_active للمستخدمين
    existing_usr_cols = {row[1] for row in cur.execute("PRAGMA table_info(users)").fetchall()}
    if "is_active" not in existing_usr_cols:
        cur.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")

    # ترحيل: max_absent_days للموظفين
    existing_emp_cols2 = {row[1] for row in cur.execute("PRAGMA table_info(employees)").fetchall()}
    if "max_absent_days" not in existing_emp_cols2:
        cur.execute("ALTER TABLE employees ADD COLUMN max_absent_days INTEGER DEFAULT 0")
    if "max_vacation_days" not in existing_emp_cols2:
        cur.execute("ALTER TABLE employees ADD COLUMN max_vacation_days INTEGER DEFAULT 0")
    if "max_sick_days" not in existing_emp_cols2:
        cur.execute("ALTER TABLE employees ADD COLUMN max_sick_days INTEGER DEFAULT 0")
    if "max_work_days" not in existing_emp_cols2:
        cur.execute("ALTER TABLE employees ADD COLUMN max_work_days INTEGER DEFAULT 0")

    # ترحيل: annual_leave_days للموظفين (رصيد الإجازة السنوية)
    existing_emp_cols3 = {row[1] for row in cur.execute("PRAGMA table_info(employees)").fetchall()}
    if "annual_leave_days" not in existing_emp_cols3:
        cur.execute("ALTER TABLE employees ADD COLUMN annual_leave_days INTEGER DEFAULT 21")

    # ترحيل: branch للموظفين
    existing_emp_cols4 = {row[1] for row in cur.execute("PRAGMA table_info(employees)").fetchall()}
    if "branch" not in existing_emp_cols4:
        cur.execute("ALTER TABLE employees ADD COLUMN branch TEXT")

    # إعدادات افتراضية جديدة
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('work_days', '0,1,2,3,6')")

    conn.commit()
    conn.close()


# ─────────────────────────── الإعدادات ──────────────────────────────────

def get_setting(key: str, default: str = None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()


def is_first_run() -> bool:
    return get_setting("first_run", "0") == "1"


def clear_first_run():
    set_setting("first_run", "0")


# ────────────────────────── النسخ الاحتياطي ─────────────────────────────

def create_backup() -> str:
    """ينشئ نسخة احتياطية من قاعدة البيانات ويعيد مسارها"""
    backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"attendance_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    # احتفظ بآخر 10 نسخ فقط
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".db")],
        reverse=True
    )
    for old in backups[10:]:
        os.remove(os.path.join(backup_dir, old))
    set_setting("last_backup", datetime.now().strftime("%Y-%m-%d %H:%M"))
    return backup_path


def list_backups():
    backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
    if not os.path.exists(backup_dir):
        return []
    files = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".db")],
        reverse=True
    )
    result = []
    for f in files:
        path = os.path.join(backup_dir, f)
        size = os.path.getsize(path)
        result.append({"name": f, "path": path, "size": f"{size//1024} KB"})
    return result


# ─────────────────────────────── المصادقة ───────────────────────────────

def authenticate(username: str, password: str):
    """التحقق من بيانات تسجيل الدخول"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    if user and _verify_password(password, user["password_hash"], user["password_salt"]):
        if not user["is_active"]:
            return "disabled"   # حساب معطّل
        return dict(user)
    return None


# ─────────────────────────────── الموظفون ───────────────────────────────

def get_all_employees(include_inactive=False):
    conn = get_connection()
    cur = conn.cursor()
    if include_inactive:
        cur.execute("SELECT * FROM employees ORDER BY full_name")
    else:
        cur.execute("SELECT * FROM employees WHERE status = 'active' ORDER BY full_name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_employee_by_id(emp_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_employee(employee_code, full_name, department, organization, position, phone, email, hire_date,
                 max_absent_days=0, max_vacation_days=0, max_sick_days=0, max_work_days=0,
                 annual_leave_days=21, branch=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO employees (employee_code, full_name, department, organization, position, phone, email, hire_date, "
        "max_absent_days, max_vacation_days, max_sick_days, max_work_days, annual_leave_days, branch) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (employee_code, full_name, department or None, organization or None,
         position or None, phone or None, email or None, hire_date or None,
         max_absent_days, max_vacation_days, max_sick_days, max_work_days, annual_leave_days,
         branch or None)
    )
    conn.commit()
    conn.close()


def update_employee(emp_id, employee_code, full_name, department, organization, position, phone, email, hire_date, status,
                    max_absent_days=0, max_vacation_days=0, max_sick_days=0, max_work_days=0,
                    annual_leave_days=21, branch=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE employees SET employee_code=?, full_name=?, department=?, organization=?, "
        "position=?, phone=?, email=?, hire_date=?, status=?, "
        "max_absent_days=?, max_vacation_days=?, max_sick_days=?, max_work_days=?, annual_leave_days=?, branch=? WHERE id=?",
        (employee_code, full_name, department or None, organization or None,
         position or None, phone or None, email or None, hire_date or None, status,
         max_absent_days, max_vacation_days, max_sick_days, max_work_days, annual_leave_days,
         branch or None, emp_id)
    )
    conn.commit()
    conn.close()


# ─────────────────────────────── الفروع ─────────────────────────────────

def get_all_branches():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM branches WHERE is_active=1 ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_branch(name, address=None, manager=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO branches (name, address, manager) VALUES (?,?,?)",
        (name.strip(), address or None, manager or None)
    )
    conn.commit()
    conn.close()


def update_branch(branch_id, name, address=None, manager=None):
    conn = get_connection()
    conn.execute(
        "UPDATE branches SET name=?, address=?, manager=? WHERE id=?",
        (name.strip(), address or None, manager or None, branch_id)
    )
    conn.commit()
    conn.close()


def delete_branch(branch_id):
    conn = get_connection()
    # ألغِ تعيين الموظفين المنتمين لهذا الفرع
    conn.execute("UPDATE employees SET branch=NULL WHERE branch=(SELECT name FROM branches WHERE id=?)",
                 (branch_id,))
    conn.execute("UPDATE branches SET is_active=0 WHERE id=?", (branch_id,))
    conn.commit()
    conn.close()


def update_absence_limit(emp_id, exit_type, num_days):
    """تحديث حد نوع غياب محدد لموظف بمجموع الأيام المسجّلة له"""
    col_map = {
        'vacation': 'max_vacation_days',
        'sick':     'max_sick_days',
        'work':     'max_work_days',
        '':         'max_absent_days',
        None:       'max_absent_days',
    }
    col = col_map.get(exit_type)
    if not col:
        return
    conn = get_connection()
    cur = conn.cursor()
    # أضف عدد الأيام للحد الحالي (إذا كان 0 يصبح الحد الجديد = عدد الأيام فقط)
    cur.execute(
        f"UPDATE employees SET {col} = {col} + ? WHERE id = ?",
        (num_days, emp_id)
    )
    conn.commit()
    conn.close()


# ─────────────────────────── العطل الرسمية ──────────────────────────────

def get_all_holidays():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM holidays ORDER BY date")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def add_holiday(name: str, date_str: str, is_recurring: int = 0):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO holidays (name, date, is_recurring) VALUES (?, ?, ?)",
        (name.strip(), date_str, is_recurring)
    )
    conn.commit()
    conn.close()


def delete_holiday(holiday_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM holidays WHERE id = ?", (holiday_id,))
    conn.commit()
    conn.close()


def get_holidays_for_year(year: int) -> set:
    """يُرجع مجموعة تواريخ العطل لسنة معينة (تُدمج المتكررة مع غير المتكررة)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT date, is_recurring FROM holidays")
    holidays = set()
    for row in cur.fetchall():
        d, recurring = row["date"], row["is_recurring"]
        if recurring:
            holidays.add(f"{year:04d}-{d[5:]}")
        else:
            holidays.add(d)
    conn.close()
    return holidays


def get_work_days() -> set:
    """يُرجع مجموعة أرقام أيام العمل (weekday: 0=Mon ... 6=Sun)"""
    val = get_setting("work_days", "0,1,2,3,6")
    return {int(x) for x in val.split(",") if x.strip().isdigit()}


def is_work_day(date_str: str) -> bool:
    """هل هذا التاريخ يوم عمل؟ (ليس عطلة رسمية ولا إجازة أسبوعية)"""
    d = _date.fromisoformat(date_str)
    if d.weekday() not in get_work_days():
        return False
    holidays = get_holidays_for_year(d.year)
    return date_str not in holidays


# ─────────────────────────── سجل التعديلات ──────────────────────────────

def log_action(user_id, username: str, action: str, details: str = ""):
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO audit_log (user_id, username, action, details) VALUES (?, ?, ?, ?)",
            (user_id, username, action, details or "")
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_audit_log(limit: int = 300):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ─────────────────────────── استيراد الموظفين ────────────────────────────

def import_employees_from_list(rows: list) -> tuple:
    """
    استيراد موظفين من قائمة.
    كل عنصر قاموس بالأعمدة: employee_code, full_name, department, organization,
                               position, phone, email, hire_date
    يُرجع (نجح، فشل، مكرر)
    """
    success, failed, duplicate = 0, 0, 0
    conn = get_connection()
    cur = conn.cursor()
    for r in rows:
        code = str(r.get("employee_code", "")).strip()
        name = str(r.get("full_name", "")).strip()
        if not code or not name:
            failed += 1
            continue
        # تحقق من التكرار
        cur.execute("SELECT id FROM employees WHERE employee_code = ?", (code,))
        if cur.fetchone():
            duplicate += 1
            continue
        try:
            cur.execute(
                "INSERT INTO employees "
                "(employee_code, full_name, department, organization, position, phone, email, hire_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (code, name,
                 str(r.get("department",   "")).strip() or None,
                 str(r.get("organization", "")).strip() or None,
                 str(r.get("position",     "")).strip() or None,
                 str(r.get("phone",        "")).strip() or None,
                 str(r.get("email",        "")).strip() or None,
                 str(r.get("hire_date",    "")).strip() or None)
            )
            success += 1
        except Exception:
            failed += 1
    conn.commit()
    conn.close()
    return success, failed, duplicate


# ─────────────────────────── تقرير الفرد ────────────────────────────────

def get_employee_full_report(emp_id: int, year: int, month: int):
    """
    تقرير تفصيلي لموظف في شهر محدد + ملخص سنوي.
    يُرجع (records_list, year_stats_list, emp_dict)
    """
    from_date = f"{year:04d}-{month:02d}-01"
    to_date   = f"{year:04d}-{month:02d}-31"
    conn = get_connection()
    cur = conn.cursor()

    # سجلات الشهر
    cur.execute("""
        SELECT a.date, a.status, a.check_in, a.check_out, a.exit_type, a.notes,
               u.full_name AS recorded_by_name, a.recorded_at
        FROM attendance a
        LEFT JOIN users u ON a.recorded_by = u.id
        WHERE a.employee_id = ? AND a.date BETWEEN ? AND ?
        ORDER BY a.date
    """, (emp_id, from_date, to_date))
    records = [dict(r) for r in cur.fetchall()]

    # ملخص 12 شهر للسنة
    year_stats = []
    for m in range(1, 13):
        fm = f"{year:04d}-{m:02d}-01"
        tm = f"{year:04d}-{m:02d}-31"
        cur.execute("""
            SELECT
                SUM(CASE WHEN status='present' THEN 1 ELSE 0 END)                          AS present_days,
                SUM(CASE WHEN status='absent' AND (exit_type IS NULL OR exit_type='') THEN 1 ELSE 0 END) AS absent_days,
                SUM(CASE WHEN exit_type='vacation' THEN 1 ELSE 0 END)                      AS vacation_days,
                SUM(CASE WHEN exit_type='sick'     THEN 1 ELSE 0 END)                      AS sick_days,
                SUM(CASE WHEN exit_type='work'     THEN 1 ELSE 0 END)                      AS work_days,
                COUNT(id)                                                                    AS total_days
            FROM attendance
            WHERE employee_id = ? AND date BETWEEN ? AND ?
        """, (emp_id, fm, tm))
        row = cur.fetchone()
        year_stats.append({
            "month":         m,
            "present_days":  row["present_days"]  or 0,
            "absent_days":   row["absent_days"]   or 0,
            "vacation_days": row["vacation_days"] or 0,
            "sick_days":     row["sick_days"]     or 0,
            "work_days":     row["work_days"]     or 0,
            "total_days":    row["total_days"]    or 0,
        })

    # إجمالي الإجازة في السنة
    cur.execute("""
        SELECT SUM(CASE WHEN exit_type='vacation' THEN 1 ELSE 0 END) AS vacation_year
        FROM attendance
        WHERE employee_id = ? AND date BETWEEN ? AND ?
    """, (emp_id, f"{year:04d}-01-01", f"{year:04d}-12-31"))
    r = cur.fetchone()
    vacation_year = r["vacation_year"] or 0

    cur.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    emp_row = cur.fetchone()
    emp = dict(emp_row) if emp_row else {}

    conn.close()
    emp["vacation_year"]    = vacation_year
    emp["leave_balance"]    = max(0, (emp.get("annual_leave_days") or 21) - vacation_year)
    return records, year_stats, emp


def auto_fill_overdue_absences(today_str: str) -> int:
    """
    لكل موظف تجاوز حده: سجّل اليوم غياباً تلقائياً إن لم يُسجَّل بعد.
    يتخطى العطل الرسمية وأيام الراحة الأسبوعية.
    يُعيد عدد السجلات الجديدة.
    """
    # تخطَّ أيام الراحة والعطل
    if not is_work_day(today_str):
        return 0

    d          = _date.fromisoformat(today_str)
    year, month = d.year, d.month
    from_date  = f"{year:04d}-{month:02d}-01"

    conn = get_connection()
    cur  = conn.cursor()

    # احسب غياب كل موظف حتى أمس (قبل اليوم الحالي)
    cur.execute("""
        SELECT e.id,
               e.max_absent_days, e.max_vacation_days, e.max_sick_days, e.max_work_days,
               SUM(CASE WHEN a.status='absent' AND (a.exit_type IS NULL OR a.exit_type='') THEN 1 ELSE 0 END),
               SUM(CASE WHEN a.exit_type='vacation' THEN 1 ELSE 0 END),
               SUM(CASE WHEN a.exit_type='sick'     THEN 1 ELSE 0 END),
               SUM(CASE WHEN a.exit_type='work'     THEN 1 ELSE 0 END)
        FROM employees e
        LEFT JOIN attendance a
               ON a.employee_id = e.id
              AND a.date >= ?
              AND a.date <  ?
        WHERE e.status = 'active'
        GROUP BY e.id
    """, (from_date, today_str))
    rows = cur.fetchall()

    # الموظفون الذين لديهم سجل اليوم بالفعل
    cur.execute("SELECT employee_id FROM attendance WHERE date = ?", (today_str,))
    has_record = {r[0] for r in cur.fetchall()}

    filled = 0
    for (emp_id,
         max_absent, max_vacation, max_sick, max_work,
         absent_days, vacation_days, sick_days, work_days) in rows:

        overdue = (
            (max_absent   > 0 and (absent_days   or 0) >= max_absent)   or
            (max_vacation > 0 and (vacation_days or 0) >= max_vacation) or
            (max_sick     > 0 and (sick_days     or 0) >= max_sick)     or
            (max_work     > 0 and (work_days     or 0) >= max_work)
        )
        if overdue and emp_id not in has_record:
            cur.execute("""
                INSERT INTO attendance (employee_id, date, status, notes, recorded_by)
                VALUES (?, ?, 'absent', 'غياب تلقائي — تجاوز حد الإجازة', 1)
                ON CONFLICT(employee_id, date) DO NOTHING
            """, (emp_id, today_str))
            filled += 1

    conn.commit()
    conn.close()
    return filled


def delete_employee(emp_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
    conn.commit()
    conn.close()


def get_departments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT department FROM employees "
        "WHERE department IS NOT NULL AND department != '' ORDER BY department"
    )
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


# ─────────────────────────────── الحضور ───────────────────────────────

def get_employees_last_status(before_date):
    """
    آخر حالة مسجّلة لكل موظف قبل تاريخ معيّن.
    يُرجع: {employee_id: {"status", "check_in", "check_out", "exit_type", "date"}}
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT a.employee_id,
               a.status, a.check_in, a.check_out, a.exit_type, a.date
        FROM attendance a
        INNER JOIN (
            SELECT employee_id, MAX(date) AS last_date
            FROM attendance
            WHERE date < ?
            GROUP BY employee_id
        ) mx ON a.employee_id = mx.employee_id AND a.date = mx.last_date
    """, (before_date,))
    result = {r["employee_id"]: dict(r) for r in cur.fetchall()}
    conn.close()
    return result


def auto_fill_attendance(target_date, recorded_by):
    """
    ملء تلقائي ليوم واحد:
    لكل موظف نشط لا يملك سجلاً في target_date،
    انسخ آخر حالة مسجّلة له (مهما كانت).
    يتخطى العطل الرسمية وأيام الراحة.
    يُرجع عدد السجلات التي أُضيفت.
    """
    if not is_work_day(target_date):
        return 0
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM employees WHERE status = 'active'")
    emp_ids = [r[0] for r in cur.fetchall()]

    filled = 0
    for eid in emp_ids:
        cur.execute("SELECT id FROM attendance WHERE employee_id=? AND date=?",
                    (eid, target_date))
        if cur.fetchone():
            continue
        cur.execute("""
            SELECT status, check_in, check_out, exit_type, notes
            FROM attendance
            WHERE employee_id=? AND date < ?
            ORDER BY date DESC LIMIT 1
        """, (eid, target_date))
        last = cur.fetchone()
        if last:
            # تطبيع الحالة: late → present, leave → absent
            st = last["status"]
            if st == "late":   st = "present"
            if st == "leave":  st = "absent"
            cur.execute("""
                INSERT INTO attendance
                    (employee_id, date, status, check_in, check_out,
                     exit_type, notes, recorded_by)
                VALUES (?,?,?,?,?,?,?,?)
            """, (eid, target_date,
                  st, last["check_in"], last["check_out"],
                  last["exit_type"], last["notes"], recorded_by))
            filled += 1

    conn.commit()
    conn.close()
    return filled


def fill_missing_range(from_date, to_date, recorded_by):
    """
    ملء جميع الأيام المفقودة بين from_date و to_date
    بنقل الحالة الأخيرة تلقائياً (carry-forward).
    يُرجع إجمالي السجلات المضافة.
    """
    from datetime import date as _date, timedelta
    start = _date.fromisoformat(from_date)
    end   = _date.fromisoformat(to_date)
    total = 0
    d = start
    while d <= end:
        total += auto_fill_attendance(d.isoformat(), recorded_by)
        d += timedelta(days=1)
    return total


def record_attendance(employee_id, date, status, check_in, check_out, exit_type, notes, recorded_by):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO attendance (employee_id, date, status, check_in, check_out, exit_type, notes, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(employee_id, date) DO UPDATE SET
            status      = excluded.status,
            check_in    = excluded.check_in,
            check_out   = excluded.check_out,
            exit_type   = excluded.exit_type,
            notes       = excluded.notes,
            recorded_by = excluded.recorded_by,
            recorded_at = datetime('now')
    """, (employee_id, date, status, check_in or None, check_out or None,
          exit_type or None, notes or None, recorded_by))
    conn.commit()
    conn.close()


def get_attendance_for_date(date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.*, e.full_name, e.employee_code, e.department, e.organization
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.date = ?
        ORDER BY e.full_name
    """, (date,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_attendance_report(from_date, to_date, employee_id=None, department=None, branch=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT a.*, e.full_name, e.employee_code, e.department, e.organization, e.position, e.branch
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.date BETWEEN ? AND ?
    """
    params = [from_date, to_date]
    if employee_id:
        query += " AND a.employee_id = ?"
        params.append(employee_id)
    if department:
        query += " AND e.department = ?"
        params.append(department)
    if branch:
        query += " AND e.branch = ?"
        params.append(branch)
    query += " ORDER BY a.date, e.full_name"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_dashboard_stats(date):
    """إحصائيات لوحة التحكم ليوم معين"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT status, COUNT(*) as cnt
        FROM attendance
        WHERE date = ?
        GROUP BY status
    """, (date,))
    stats = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT COUNT(*) FROM employees WHERE status = 'active'")
    stats["total"] = cur.fetchone()[0]
    conn.close()
    return stats


def get_attendance_summary(from_date, to_date, group_by="day"):
    """
    إجماليات الحضور مجمّعة حسب: day | week | month
    يُرجع قائمة من القواميس:
      [{"period": "...", "present": N, "absent": N, "late": N, "leave": N, "total": N, "rate": N}, ...]
    """
    if group_by == "week":
        fmt = "%Y-W%W"
    elif group_by == "month":
        fmt = "%Y-%m"
    else:
        fmt = "%Y-%m-%d"

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        SELECT strftime('{fmt}', date) AS period,
               status,
               COUNT(*) AS cnt
        FROM attendance
        WHERE date BETWEEN ? AND ?
        GROUP BY period, status
        ORDER BY period
    """, (from_date, to_date))
    rows = cur.fetchall()

    # إجمالي الموظفين النشطين لحساب النسبة
    cur.execute("SELECT COUNT(*) FROM employees WHERE status = 'active'")
    total_emp = cur.fetchone()[0] or 1
    conn.close()

    # تجميع في dict مؤقت
    periods = {}
    for row in rows:
        p, st, cnt = row["period"], row["status"], row["cnt"]
        if p not in periods:
            periods[p] = {"period": p, "present": 0, "absent": 0, "late": 0, "leave": 0}
        if st in ("present", "absent", "late", "leave"):
            periods[p][st] += cnt

    result = []
    for p, d in sorted(periods.items()):
        total = d["present"] + d["absent"] + d["late"] + d["leave"]
        # نسبة الحضور = (حاضر + متأخر) / إجمالي المسجلين
        rate  = round((d["present"] + d["late"]) / total * 100, 1) if total else 0
        result.append({**d, "total": total, "rate": rate, "total_emp": total_emp})
    return result


def get_employee_attendance_stats(year: int, month: int):
    """عدد أيام الحضور والغياب لكل موظف في شهر معين"""
    from_date = f"{year:04d}-{month:02d}-01"
    to_date   = f"{year:04d}-{month:02d}-31"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id, e.full_name, e.department,
               e.max_absent_days, e.max_vacation_days, e.max_sick_days, e.max_work_days,
               SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) AS present_days,
               SUM(CASE WHEN a.status='absent' AND (a.exit_type IS NULL OR a.exit_type='') THEN 1 ELSE 0 END) AS absent_days,
               SUM(CASE WHEN a.exit_type='vacation' THEN 1 ELSE 0 END) AS vacation_days,
               SUM(CASE WHEN a.exit_type='sick'     THEN 1 ELSE 0 END) AS sick_days,
               SUM(CASE WHEN a.exit_type='work'     THEN 1 ELSE 0 END) AS work_days,
               COUNT(a.id) AS total_days
        FROM employees e
        LEFT JOIN attendance a ON a.employee_id=e.id AND a.date BETWEEN ? AND ?
        WHERE e.status='active'
        GROUP BY e.id
        ORDER BY absent_days DESC, e.full_name
    """, (from_date, to_date))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_absent_alerts(year: int, month: int):
    """الموظفون الذين تجاوزوا أي حد مسموح به في الشهر"""
    stats = get_employee_attendance_stats(year, month)
    alerts = []
    for r in stats:
        reasons = []
        if r["max_absent_days"]   > 0 and r["absent_days"]   > r["max_absent_days"]:
            reasons.append(("غياب",    r["absent_days"],   r["max_absent_days"]))
        if r["max_vacation_days"] > 0 and r["vacation_days"] > r["max_vacation_days"]:
            reasons.append(("إجازة",   r["vacation_days"], r["max_vacation_days"]))
        if r["max_sick_days"]     > 0 and r["sick_days"]     > r["max_sick_days"]:
            reasons.append(("مرض",     r["sick_days"],     r["max_sick_days"]))
        if r["max_work_days"]     > 0 and r["work_days"]     > r["max_work_days"]:
            reasons.append(("عمل خارجي", r["work_days"],     r["max_work_days"]))
        if reasons:
            r["reasons"] = reasons
            alerts.append(r)
    return alerts


def get_employee_month_summary(employee_id, year, month):
    from_date = f"{year:04d}-{month:02d}-01"
    to_date   = f"{year:04d}-{month:02d}-31"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT status, COUNT(*) as cnt
        FROM attendance
        WHERE employee_id = ? AND date BETWEEN ? AND ?
        GROUP BY status
    """, (employee_id, from_date, to_date))
    result = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()
    return result


# ─────────────────────────────── المستخدمون ───────────────────────────────

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, full_name, is_active, created_at FROM users ORDER BY full_name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def toggle_user_active(user_id: int):
    """تعطيل أو تفعيل حساب مستخدم"""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?",
        (user_id,)
    )
    conn.commit()
    conn.close()


def add_user(username, password, role, full_name):
    pw_hash, pw_salt = _hash_password(password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, password_salt, role, full_name) "
        "VALUES (?, ?, ?, ?, ?)",
        (username, pw_hash, pw_salt, role, full_name)
    )
    conn.commit()
    conn.close()


def change_password(user_id, new_password):
    pw_hash, pw_salt = _hash_password(new_password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password_hash=?, password_salt=? WHERE id=?",
        (pw_hash, pw_salt, user_id)
    )
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
