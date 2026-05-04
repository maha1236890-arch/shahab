"""
demo_data.py — بيانات تجريبية لنظام الحضور والغياب
يضيف: 3 فروع + 20 موظفاً + سجلات حضور لـ 3 أشهر + مستخدم تجريبي
الاستخدام:
    python3 demo_data.py          # إضافة البيانات
    python3 demo_data.py --reset  # حذف الكل ثم إعادة الإضافة
"""

import sys
import os
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

# ── ثوابت ─────────────────────────────────────────────────────────────────

BRANCHES = [
    {"name": "الإدارة المركزية",  "address": "الرياض — حي العليا",      "manager": "سعد القحطاني"},
    {"name": "فرع جدة",          "address": "جدة — طريق الملك فهد",     "manager": "محمد العمري"},
    {"name": "فرع الدمام",       "address": "الدمام — حي الشاطئ",       "manager": "فيصل الزهراني"},
]

EMPLOYEES = [
    # (كود، اسم، قسم، جهة، منصب، هاتف، فرع_index)
    ("EMP001", "أحمد محمد السعيد",    "الموارد البشرية",  "شركة النخبة للتقنية", "مدير الموارد البشرية",  "0501111111", 0),
    ("EMP002", "فاطمة علي الحربي",    "المالية",          "شركة النخبة للتقنية", "محاسبة أولى",           "0502222222", 0),
    ("EMP003", "خالد عبدالله الغامدي","تقنية المعلومات",  "شركة النخبة للتقنية", "مطور برمجيات",          "0503333333", 0),
    ("EMP004", "نورة سعد الشمري",     "التسويق",          "شركة النخبة للتقنية", "أخصائي تسويق",          "0504444444", 0),
    ("EMP005", "عمر يوسف القرني",     "المبيعات",         "شركة النخبة للتقنية", "مندوب مبيعات",          "0505555555", 0),
    ("EMP006", "ريم محمد الدوسري",    "خدمة العملاء",     "شركة النخبة للتقنية", "أخصائي خدمة عملاء",     "0506666666", 0),
    ("EMP007", "بندر سلطان الرشيدي", "الإدارة",          "شركة النخبة للتقنية", "سكرتير تنفيذي",         "0507777777", 0),
    ("EMP008", "هند علي الزهراني",    "القانون",          "شركة النخبة للتقنية", "مستشار قانوني",         "0508888888", 0),
    ("EMP009", "طارق حسن العتيبي",    "اللوجستيات",       "شركة النخبة للتقنية", "مشرف مستودع",           "0509999999", 0),
    ("EMP010", "منى خالد القحطاني",   "الموارد البشرية",  "شركة النخبة للتقنية", "أخصائي توظيف",          "0510101010", 0),
    # فرع جدة
    ("EMP011", "وليد محمد الجهني",    "المبيعات",         "شركة النخبة للتقنية", "مدير المبيعات",         "0511111111", 1),
    ("EMP012", "سارة أحمد البلوي",    "المالية",          "شركة النخبة للتقنية", "محاسبة",                "0512121212", 1),
    ("EMP013", "إبراهيم سعد الحارثي", "تقنية المعلومات",  "شركة النخبة للتقنية", "مهندس شبكات",           "0513131313", 1),
    ("EMP014", "لمياء عبدالرحمن",     "خدمة العملاء",     "شركة النخبة للتقنية", "مشرف خدمة عملاء",       "0514141414", 1),
    ("EMP015", "ناصر فهد الشهري",     "اللوجستيات",       "شركة النخبة للتقنية", "سائق توصيل",            "0515151515", 1),
    # فرع الدمام
    ("EMP016", "حمد سعيد الكثيري",    "الإدارة",          "شركة النخبة للتقنية", "مدير الفرع",            "0516161616", 2),
    ("EMP017", "دلال محمد العمري",     "المالية",          "شركة النخبة للتقنية", "مراجع مالي",            "0517171717", 2),
    ("EMP018", "يوسف علي المطيري",    "تقنية المعلومات",  "شركة النخبة للتقنية", "دعم تقني",              "0518181818", 2),
    ("EMP019", "شيماء خالد السبيعي",  "التسويق",          "شركة النخبة للتقنية", "مصمم جرافيك",           "0519191919", 2),
    ("EMP020", "جاسم محمد الدوسري",   "المبيعات",         "شركة النخبة للتقنية", "مستشار مبيعات",         "0520202020", 2),
]

HOLIDAYS_2026 = [
    ("اليوم الوطني",         "2026-09-23", 0),
    ("عيد الفطر - يوم 1",   "2026-03-30", 0),
    ("عيد الفطر - يوم 2",   "2026-03-31", 0),
    ("عيد الفطر - يوم 3",   "2026-04-01", 0),
    ("عيد الأضحى - يوم 1",  "2026-06-16", 0),
    ("عيد الأضحى - يوم 2",  "2026-06-17", 0),
    ("عيد الأضحى - يوم 3",  "2026-06-18", 0),
]

# وزن الحضور لكل موظف: بعضهم مواظب وبعضهم كثير الغياب (للديمو)
EMPLOYEE_PROFILES = {
    # emp_index: (present%, late%, leave%, absent%, sick%)
    0:  (85, 5, 5,  3,  2),   # مواظب جداً
    1:  (90, 3, 5,  2,  0),
    2:  (80, 8, 5,  5,  2),
    3:  (88, 4, 4,  3,  1),
    4:  (75, 5, 8,  7,  5),   # كثير الغياب
    5:  (92, 2, 4,  1,  1),
    6:  (82, 6, 6,  4,  2),
    7:  (95, 2, 2,  1,  0),   # مثالي
    8:  (78, 4, 8,  6,  4),
    9:  (87, 5, 4,  3,  1),
    10: (91, 3, 3,  2,  1),
    11: (83, 5, 6,  4,  2),
    12: (76, 4, 9,  7,  4),
    13: (89, 4, 4,  2,  1),
    14: (84, 6, 5,  3,  2),
    15: (94, 2, 2,  1,  1),
    16: (79, 5, 7,  6,  3),
    17: (86, 4, 5,  3,  2),
    18: (88, 5, 3,  3,  1),
    19: (81, 6, 6,  5,  2),
}


def random_status(idx: int) -> str:
    p = EMPLOYEE_PROFILES.get(idx, (85, 5, 5, 3, 2))
    r = random.randint(1, 100)
    if r <= p[0]:               return "present"
    if r <= p[0] + p[1]:        return "late"
    if r <= p[0]+p[1]+p[2]:     return "leave"
    if r <= p[0]+p[1]+p[2]+p[3]: return "absent"
    return "absent"  # sick → absent with exit_type sick


def random_check_in(status: str):
    if status == "present":
        return f"0{random.randint(7,8)}:{random.choice(['00','15','30','45'])}"
    if status == "late":
        h = random.randint(9, 10)
        return f"{h:02d}:{random.choice(['05','20','35','50'])}"
    return None


def random_check_out(status: str):
    if status in ("present", "late"):
        h = random.randint(16, 17)
        return f"{h:02d}:{random.choice(['00','15','30','45'])}"
    return None


def get_work_days_range(start: date, end: date) -> list:
    """أيام العمل فقط (الإثنين—الجمعة) في النطاق"""
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:  # 0=Mon … 4=Fri
            days.append(d)
        d += timedelta(days=1)
    return days


# ── منطق الإضافة ──────────────────────────────────────────────────────────

def reset_demo():
    """حذف البيانات التجريبية فقط (الموظفون ذوو الكود EMP*)"""
    conn = db.get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM employees WHERE employee_code LIKE 'EMP%'")
    ids = [r[0] for r in cur.fetchall()]
    for eid in ids:
        cur.execute("DELETE FROM attendance WHERE employee_id = ?", (eid,))
        cur.execute("DELETE FROM employees  WHERE id = ?", (eid,))
    # حذف الفروع التجريبية
    for b in BRANCHES:
        cur.execute("DELETE FROM branches WHERE name = ?", (b["name"],))
    # حذف العطل التجريبية
    for h in HOLIDAYS_2026:
        cur.execute("DELETE FROM holidays WHERE name = ?", (h[0],))
    conn.commit()
    conn.close()
    print("✓ حُذفت البيانات التجريبية السابقة")


def insert_demo():
    random.seed(42)  # نتائج ثابتة في كل تشغيل

    # ── 1. الفروع ──────────────────────────────────────────────────────
    branch_ids = []
    existing_branches = {b["name"]: b["id"] for b in db.get_all_branches()}
    for br in BRANCHES:
        if br["name"] not in existing_branches:
            db.add_branch(br["name"], br["address"], br["manager"])
        # جلب الـ ID
        conn_b = db.get_connection()
        cur_b  = conn_b.cursor()
        cur_b.execute("SELECT id FROM branches WHERE name=?", (br["name"],))
        row_b = cur_b.fetchone()
        conn_b.close()
        branch_ids.append(row_b[0] if row_b else None)
    print(f"✓ الفروع ({len(branch_ids)}): {[b['name'] for b in BRANCHES]}")

    # ── 2. الموظفون ────────────────────────────────────────────────────
    existing_codes = {e["employee_code"] for e in db.get_all_employees(include_inactive=True)}
    emp_ids = []
    hire_start = date(2022, 1, 1)
    for i, (code, name, dept, org, pos, phone, br_idx) in enumerate(EMPLOYEES):
        # إضافة الموظف إن لم يكن موجوداً
        if code not in existing_codes:
            hire_date = hire_start + timedelta(days=random.randint(0, 365*3))
            db.add_employee(
                employee_code    = code,
                full_name        = name,
                department       = dept,
                organization     = org,
                position         = pos,
                phone            = phone,
                email            = f"{code.lower()}@demo.com",
                hire_date        = hire_date.isoformat(),
                max_absent_days  = random.choice([3, 4, 5]),
                max_vacation_days= random.choice([15, 21]),
                max_sick_days    = random.choice([7, 10]),
                max_work_days    = 0,
                annual_leave_days= random.choice([21, 25, 30]),
                branch           = BRANCHES[br_idx]["name"],
            )
        # جلب الـ ID بعد الإضافة أو إن كان موجوداً
        conn_tmp = db.get_connection()
        cur_tmp  = conn_tmp.cursor()
        cur_tmp.execute("SELECT id FROM employees WHERE employee_code=?", (code,))
        row = cur_tmp.fetchone()
        conn_tmp.close()
        emp_ids.append(row[0] if row else None)
    print(f"✓ الموظفون ({len([x for x in emp_ids if x])}): أُضيفوا/حُدِّثوا")

    # ── 3. سجلات الحضور (3 أشهر: فبراير – أبريل 2026) ─────────────
    # استخدام admin user id = 1
    try:
        conn = db.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
        row = cur.fetchone()
        admin_id = row[0] if row else 1
        conn.close()
    except Exception:
        admin_id = 1

    months = [(2026, 2), (2026, 3), (2026, 4)]
    total_records = 0

    for year, month in months:
        start = date(year, month, 1)
        # نهاية الشهر
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)

        # لا نكتب سجلات مستقبلية
        today = date.today()
        if start > today:
            continue
        if end > today:
            end = today

        work_days = get_work_days_range(start, end)

        for d in work_days:
            d_str = d.isoformat()
            for idx, eid in enumerate(emp_ids):
                if eid is None:
                    continue
                # تحقق إذا السجل موجود مسبقاً
                conn2 = db.get_connection()
                cur2  = conn2.cursor()
                cur2.execute(
                    "SELECT id FROM attendance WHERE employee_id=? AND date=?",
                    (eid, d_str)
                )
                exists = cur2.fetchone()
                conn2.close()
                if exists:
                    continue

                status    = random_status(idx)
                check_in  = random_check_in(status)
                check_out = random_check_out(status)
                exit_type = None
                notes     = None

                # بعض الحالات الخاصة
                if status == "leave":
                    exit_type = random.choice(["vacation", "sick"])
                    if exit_type == "sick":
                        status    = "absent"
                        exit_type = "sick"
                        notes     = "إجازة مرضية"
                elif status == "late":
                    notes = "تأخر عن موعد الدوام"

                db.record_attendance(
                    employee_id = eid,
                    date        = d_str,
                    status      = status,
                    check_in    = check_in,
                    check_out   = check_out,
                    exit_type   = exit_type,
                    notes       = notes,
                    recorded_by = admin_id,
                )
                total_records += 1

    print(f"✓ سجلات الحضور ({total_records:,} سجل) لـ {len(months)} أشهر")

    # ── 4. العطل الرسمية ───────────────────────────────────────────────
    existing_h = {h["name"] for h in db.get_all_holidays()}
    added_h = 0
    for name, date_str, recurring in HOLIDAYS_2026:
        if name not in existing_h:
            db.add_holiday(name, date_str, recurring)
            added_h += 1
    print(f"✓ العطل الرسمية ({added_h} مضافة)")

    # ── 5. ملخص ────────────────────────────────────────────────────────
    print()
    print("=" * 48)
    print("  ✅ البيانات التجريبية جاهزة!")
    print("=" * 48)
    print(f"  الفروع    : {len(BRANCHES)}")
    print(f"  الموظفون  : {len(EMPLOYEES)}")
    print(f"  سجلات     : {total_records:,}")
    print(f"  الفترة    : فبراير — أبريل 2026")
    print()
    print("  🔑 بيانات الدخول:")
    print("     المستخدم : admin")
    print("     كلمة السر: admin123")
    print("=" * 48)


# ── نقطة الدخول ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_demo()
    insert_demo()
