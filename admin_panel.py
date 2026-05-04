"""
admin_panel.py - نظام الحضور والغياب
النافذة الرئيسية مع تبويبات: لوحة التحكم، الموظفون، تسجيل الحضور، التقارير، المستخدمون
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime, date, timedelta
from collections import Counter

import database as db

# ──────────────────── ألوان ────────────────────
BG            = "#1a1a2e"
SECONDARY     = "#16213e"
CARD          = "#0f3460"
ACCENT        = "#e94560"
WHITE         = "#ffffff"
SUBTEXT       = "#a0a0c0"
PRESENT_CLR   = "#27ae60"
ABSENT_CLR    = "#e74c3c"
LATE_CLR      = "#f39c12"
LEAVE_CLR     = "#3498db"
ROW_EVEN      = "#141428"

STATUS_OPTIONS = [
    ("حاضر",  "present", PRESENT_CLR),
    ("غائب",  "absent",  ABSENT_CLR),
    ("متأخر", "late",    LATE_CLR),
    ("إجازة", "leave",   LEAVE_CLR),
]
STATUS_AR = {s[1]: s[0] for s in STATUS_OPTIONS}

EXIT_TYPE_OPTIONS = [
    ("—",          ""),
    ("في مهمة عمل", "work"),
    ("إجازة",       "vacation"),
    ("مرض",         "sick"),
]
EXIT_TYPE_AR = {e[1]: e[0] for e in EXIT_TYPE_OPTIONS if e[1]}


# ──────────────────── مساعدات UI ────────────────────

def btn(parent, text, cmd, color=ACCENT, fg=WHITE, **kw):
    return tk.Button(
        parent, text=text, command=cmd,
        bg=color, fg=fg, font=("Arial", 10, "bold"),
        relief="flat", cursor="hand2",
        activebackground=color, activeforeground=fg,
        padx=12, pady=6, **kw
    )


def lbl(parent, text, font_size=10, fg=WHITE, bold=False, bg=None, **kw):
    f = ("Arial", font_size, "bold") if bold else ("Arial", font_size)
    return tk.Label(parent, text=text, font=f,
                    bg=bg or BG, fg=fg, **kw)


def entry(parent, var, width=None, justify="right", show=""):
    kw = {"textvariable": var, "font": ("Arial", 11), "justify": justify,
          "bg": CARD, "fg": WHITE, "insertbackground": WHITE, "relief": "flat",
          "highlightthickness": 1, "highlightbackground": "#334466",
          "highlightcolor": ACCENT}
    if width:
        kw["width"] = width
    if show:
        kw["show"] = show
    return tk.Entry(parent, **kw)


def scrollable_frame(parent):
    """إنشاء إطار قابل للتمرير. يُرجع (outer, inner)"""
    outer   = tk.Frame(parent, bg=BG)
    canvas  = tk.Canvas(outer, bg=BG, highlightthickness=0)
    vsb     = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner   = tk.Frame(canvas, bg=BG)
    win_id  = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_inner_config(e):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_config(e):
        canvas.itemconfig(win_id, width=e.width)

    inner.bind("<Configure>", _on_inner_config)
    canvas.bind("<Configure>", _on_canvas_config)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # دعم عجلة الماوس (Linux + Windows)
    def _wheel(e):
        if e.delta:
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        elif e.num == 4:
            canvas.yview_scroll(-1, "units")
        elif e.num == 5:
            canvas.yview_scroll(1, "units")

    for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        canvas.bind(seq, _wheel)
        inner.bind(seq, _wheel)

    return outer, inner


def setup_treeview_tags(tree):
    tree.tag_configure("present", foreground=PRESENT_CLR)
    tree.tag_configure("absent",  foreground=ABSENT_CLR)
    tree.tag_configure("late",    foreground=LATE_CLR)
    tree.tag_configure("leave",   foreground=LEAVE_CLR)
    tree.tag_configure("even",    background=ROW_EVEN)


# ══════════════════════════════════════════════════════════
class AdminPanel:
    def __init__(self, user):
        self.user    = user
        self.rep_data = []

        self.root = tk.Tk()
        self.root.title(f"نظام الحضور والغياب  ─  {user['full_name']}")
        self.root.geometry("1280x760")
        self.root.configure(bg=BG)
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"1280x760+{(sw-1280)//2}+{(sh-760)//2}")

        self._setup_styles()
        self._build_ui()
        self.root.mainloop()

    # ── أنماط ttk ──
    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TNotebook",     background=BG,        borderwidth=0)
        s.configure("TNotebook.Tab", background=SECONDARY,  foreground=WHITE,
                    font=("Arial", 11, "bold"), padding=[18, 9])
        s.map("TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", WHITE)])

        s.configure("Treeview",
                    background=SECONDARY, foreground=WHITE,
                    fieldbackground=SECONDARY, font=("Arial", 10),
                    rowheight=28)
        s.configure("Treeview.Heading",
                    background=CARD, foreground=WHITE,
                    font=("Arial", 10, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", ACCENT)])

        s.configure("Vertical.TScrollbar",   background=CARD, troughcolor=BG, arrowcolor=WHITE)
        s.configure("Horizontal.TScrollbar", background=CARD, troughcolor=BG, arrowcolor=WHITE)
        s.configure("TCombobox", fieldbackground=CARD, background=CARD, foreground=WHITE,
                    selectbackground=ACCENT)
        s.map("TCombobox", fieldbackground=[("readonly", CARD)],
              foreground=[("readonly", WHITE)])

    # ── هيكل النافذة الرئيسية ──
    def _build_ui(self):
        # شريط الرأس
        top = tk.Frame(self.root, bg=SECONDARY, height=54)
        top.pack(fill="x")
        top.pack_propagate(False)
        lbl(top, "نظام الحضور والغياب", 15, bold=True, bg=SECONDARY
            ).pack(side="right", padx=20, pady=12)
        lbl(top, f"مرحباً، {self.user['full_name']}  |  {date.today().strftime('%Y-%m-%d')}",
            9, fg=SUBTEXT, bg=SECONDARY).pack(side="left", padx=20)

        # دفتر التبويبات
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=4, pady=4)
        self.nb = nb

        tabs = [
            ("tab_dash",  " لوحة التحكم "),
            ("tab_emp",   " الموظفون "),
            ("tab_att",   " تسجيل الحضور "),
            ("tab_rep",   " التقارير "),
        ]
        for attr, title in tabs:
            f = tk.Frame(nb, bg=BG)
            setattr(self, attr, f)
            nb.add(f, text=title)

        if self.user["role"] == "admin":
            self.tab_usr = tk.Frame(nb, bg=BG)
            nb.add(self.tab_usr, text=" المستخدمون ")
            self._build_users_tab()

        self._build_dashboard_tab()
        self._build_employees_tab()
        self._build_attendance_tab()
        self._build_reports_tab()

        nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _on_tab_change(self, event):
        idx = self.nb.index("current")
        if idx == 0:
            self._refresh_dashboard()

    # ════════════════ لوحة التحكم ════════════════
    def _build_dashboard_tab(self):
        f = self.tab_dash

        # شريط الاختيار
        ctrl = tk.Frame(f, bg=BG)
        ctrl.pack(fill="x", padx=20, pady=(14, 6))
        lbl(ctrl, "تاريخ:", 10, fg=SUBTEXT).pack(side="right", padx=(0, 6))
        self.dash_date = tk.StringVar(value=date.today().isoformat())
        entry(ctrl, self.dash_date, width=12, justify="center").pack(side="right", ipady=5)
        btn(ctrl, "تحديث", self._refresh_dashboard).pack(side="right", padx=8)

        # بطاقات الإحصائيات
        self.cards_frame = tk.Frame(f, bg=BG)
        self.cards_frame.pack(fill="x", padx=20, pady=6)

        # جدول آخر السجلات
        lbl(f, "سجلات اليوم", 12, bold=True).pack(anchor="e", padx=20, pady=(8, 4))
        tf = tk.Frame(f, bg=BG)
        tf.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        cols = ("name", "dept", "date", "status", "check_in", "check_out")
        self.dash_tree = ttk.Treeview(tf, columns=cols, show="headings")
        for col, heading, w in [
            ("name",      "اسم الموظف",    200),
            ("dept",      "القسم",          140),
            ("date",      "التاريخ",        100),
            ("status",    "الحالة",          90),
            ("check_in",  "وقت الدخول",     100),
            ("check_out", "وقت الخروج",     100),
        ]:
            self.dash_tree.heading(col, text=heading)
            self.dash_tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.dash_tree.yview)
        self.dash_tree.configure(yscrollcommand=vsb.set)
        self.dash_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        setup_treeview_tags(self.dash_tree)
        self._refresh_dashboard()

    def _refresh_dashboard(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        d     = self.dash_date.get()
        stats = db.get_dashboard_stats(d)
        cards = [
            ("إجمالي الموظفين", stats.get("total", 0),   "#546e7a"),
            ("حاضر",            stats.get("present", 0), PRESENT_CLR),
            ("غائب",            stats.get("absent",  0), ABSENT_CLR),
            ("متأخر",           stats.get("late",    0), LATE_CLR),
            ("إجازة",           stats.get("leave",   0), LEAVE_CLR),
        ]
        for title, val, clr in cards:
            card = tk.Frame(self.cards_frame, bg=clr, width=170, height=95)
            card.pack(side="right", padx=7, pady=4)
            card.pack_propagate(False)
            tk.Label(card, text=str(val), font=("Arial", 30, "bold"),
                     bg=clr, fg=WHITE).pack(expand=True)
            tk.Label(card, text=title, font=("Arial", 10),
                     bg=clr, fg=WHITE).pack(pady=(0, 8))

        for row in self.dash_tree.get_children():
            self.dash_tree.delete(row)
        for i, r in enumerate(db.get_attendance_for_date(d)):
            tag = r["status"] if r["status"] in STATUS_AR else ""
            if i % 2 == 0:
                tag = (tag, "even") if tag else ("even",)
            else:
                tag = (tag,) if tag else ()
            self.dash_tree.insert("", "end",
                values=(r["full_name"], r.get("department", "") or "",
                        r["date"], STATUS_AR.get(r["status"], r["status"]),
                        r["check_in"] or "", r["check_out"] or ""),
                tags=tag)

    # ════════════════ الموظفون ════════════════
    def _build_employees_tab(self):
        f = self.tab_emp

        # شريط الأدوات
        tb = tk.Frame(f, bg=BG)
        tb.pack(fill="x", padx=20, pady=14)
        btn(tb, "➕  إضافة موظف",     self._add_employee).pack(side="right", padx=4)
        btn(tb, "✏  تعديل",           self._edit_employee,   color=CARD).pack(side="right", padx=4)
        btn(tb, "🗑  حذف",            self._delete_employee, color=ABSENT_CLR).pack(side="right", padx=4)

        lbl(tb, "بحث:", 10, fg=SUBTEXT).pack(side="left", padx=(0, 5))
        self.emp_search = tk.StringVar()
        self.emp_search.trace_add("write", lambda *_: self._load_employees(self.emp_search.get()))
        e = entry(tb, self.emp_search, width=28, justify="right")
        e.pack(side="left", ipady=6)

        # جدول الموظفين
        tf = tk.Frame(f, bg=BG)
        tf.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        cols = ("code", "name", "organization", "department", "position", "phone", "hire_date", "status")
        self.emp_tree = ttk.Treeview(tf, columns=cols, show="headings")
        for col, heading, w in [
            ("code",         "الكود",           80),
            ("name",         "الاسم الكامل",   190),
            ("organization", "الجهة",           150),
            ("department",   "القسم",           130),
            ("position",     "المسمى الوظيفي", 140),
            ("phone",        "الهاتف",          110),
            ("hire_date",    "تاريخ التعيين",  110),
            ("status",       "الحالة",           80),
        ]:
            self.emp_tree.heading(col, text=heading)
            self.emp_tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.emp_tree.yview)
        self.emp_tree.configure(yscrollcommand=vsb.set)
        self.emp_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.emp_tree.tag_configure("active",   foreground=PRESENT_CLR)
        self.emp_tree.tag_configure("inactive", foreground=ABSENT_CLR)
        self.emp_tree.tag_configure("even",     background=ROW_EVEN)
        self._load_employees()

    def _load_employees(self, search=""):
        for row in self.emp_tree.get_children():
            self.emp_tree.delete(row)
        s = search.lower()
        for i, emp in enumerate(db.get_all_employees(include_inactive=True)):
            if s and s not in emp["full_name"].lower() \
                    and s not in (emp["employee_code"] or "").lower() \
                    and s not in (emp["department"] or "").lower():
                continue
            st     = emp.get("status", "active")
            st_ar  = "نشط" if st == "active" else "غير نشط"
            tags   = (st, "even") if i % 2 == 0 else (st,)
            self.emp_tree.insert("", "end", iid=str(emp["id"]),
                values=(emp["employee_code"], emp["full_name"],
                        emp.get("organization", "") or "",
                        emp.get("department",   "") or "",
                        emp.get("position",     "") or "",
                        emp.get("phone",        "") or "",
                        emp.get("hire_date",    "") or "",
                        st_ar),
                tags=tags)

    def _selected_emp_id(self):
        sel = self.emp_tree.selection()
        return int(sel[0]) if sel else None

    def _add_employee(self):
        EmployeeDialog(self.root, None, self._load_employees)

    def _edit_employee(self):
        eid = self._selected_emp_id()
        if eid is None:
            messagebox.showinfo("تنبيه", "يرجى اختيار موظف أولاً")
            return
        emp = db.get_employee_by_id(eid)
        if emp:
            EmployeeDialog(self.root, emp, self._load_employees)

    def _delete_employee(self):
        eid = self._selected_emp_id()
        if eid is None:
            messagebox.showinfo("تنبيه", "يرجى اختيار موظف أولاً")
            return
        if messagebox.askyesno("تأكيد الحذف",
                               "هل تريد حذف هذا الموظف وجميع سجلات حضوره؟"):
            db.delete_employee(eid)
            self._load_employees()

    # ════════════════ تسجيل الحضور ════════════════
    def _build_attendance_tab(self):
        f = self.tab_att

        # شريط التحكم
        ctrl = tk.Frame(f, bg=SECONDARY)
        ctrl.pack(fill="x")
        inner = tk.Frame(ctrl, bg=SECONDARY)
        inner.pack(padx=20, pady=10)

        lbl(inner, "تاريخ الحضور:", 12, bold=True, bg=SECONDARY).pack(side="right", padx=(0, 8))
        self.att_date = tk.StringVar(value=date.today().isoformat())
        entry(inner, self.att_date, width=12, justify="center").pack(side="right", ipady=6)
        btn(inner, "تحميل",          self._load_attendance_day).pack(side="right", padx=6)
        btn(inner, "✔ الكل حاضر",   self._mark_all_present,  color=PRESENT_CLR).pack(side="right", padx=4)
        btn(inner, "💾 حفظ الحضور", self._save_attendance,   color=ACCENT).pack(side="left",  padx=4)

        # رأس الجدول
        hdr = tk.Frame(f, bg=CARD)
        hdr.pack(fill="x", padx=0)
        for text, w in [("اسم الموظف", 18), ("الكود", 7), ("الجهة", 13), ("القسم", 12),
                        ("الحالة", 36), ("دخول", 8), ("خروج", 8), ("نوع الخروج", 14)]:
            tk.Label(hdr, text=text, font=("Arial", 10, "bold"),
                     bg=CARD, fg=WHITE, width=w, anchor="center",
                     pady=7).pack(side="right", padx=1)

        # منطقة التمرير
        outer, self.att_inner = scrollable_frame(f)
        outer.pack(fill="both", expand=True)

        self.att_status_vars    = {}
        self.att_checkin_vars   = {}
        self.att_checkout_vars  = {}
        self.att_exittype_vars  = {}
        self._load_attendance_day()

    def _load_attendance_day(self):
        for w in self.att_inner.winfo_children():
            w.destroy()
        self.att_status_vars.clear()
        self.att_checkin_vars.clear()
        self.att_checkout_vars.clear()
        self.att_exittype_vars.clear()

        d          = self.att_date.get()
        employees  = db.get_all_employees()
        existing   = {r["employee_id"]: r for r in db.get_attendance_for_date(d)}

        for idx, emp in enumerate(employees):
            bg_c  = BG if idx % 2 == 0 else ROW_EVEN
            rec   = existing.get(emp["id"], {})
            sv    = tk.StringVar(value=rec.get("status",    "present"))
            ci_v  = tk.StringVar(value=rec.get("check_in",  "") or "")
            co_v  = tk.StringVar(value=rec.get("check_out", "") or "")
            et_v  = tk.StringVar(value=rec.get("exit_type", "") or "")
            self.att_status_vars[emp["id"]]   = sv
            self.att_checkin_vars[emp["id"]]  = ci_v
            self.att_checkout_vars[emp["id"]] = co_v
            self.att_exittype_vars[emp["id"]] = et_v

            row = tk.Frame(self.att_inner, bg=bg_c, pady=4)
            row.pack(fill="x", padx=2)

            # اسم الموظف
            tk.Label(row, text=emp["full_name"], font=("Arial", 10),
                     bg=bg_c, fg=WHITE, width=18, anchor="e").pack(side="right", padx=5)
            # الكود
            tk.Label(row, text=emp["employee_code"], font=("Arial", 9),
                     bg=bg_c, fg=SUBTEXT, width=7, anchor="center").pack(side="right", padx=2)
            # الجهة
            tk.Label(row, text=emp.get("organization", "") or "", font=("Arial", 9),
                     bg=bg_c, fg=SUBTEXT, width=13, anchor="center").pack(side="right", padx=2)
            # القسم
            tk.Label(row, text=emp.get("department", "") or "", font=("Arial", 9),
                     bg=bg_c, fg=SUBTEXT, width=12, anchor="center").pack(side="right", padx=2)

            # أزرار الحالة
            rb_frame = tk.Frame(row, bg=bg_c)
            rb_frame.pack(side="right", padx=4)
            for ar_txt, en_val, clr in STATUS_OPTIONS:
                tk.Radiobutton(
                    rb_frame, text=ar_txt, variable=sv, value=en_val,
                    font=("Arial", 9, "bold"),
                    bg=bg_c, fg=clr, selectcolor=CARD,
                    activebackground=bg_c, activeforeground=clr,
                    indicatoron=0, width=6, relief="groove", padx=4, pady=3
                ).pack(side="right", padx=2)

            # وقت الدخول / الخروج
            tk.Entry(row, textvariable=ci_v, width=7, justify="center",
                     bg=CARD, fg=WHITE, insertbackground=WHITE,
                     relief="flat", font=("Arial", 9)).pack(side="left", padx=(6, 2), ipady=4)
            tk.Entry(row, textvariable=co_v, width=7, justify="center",
                     bg=CARD, fg=WHITE, insertbackground=WHITE,
                     relief="flat", font=("Arial", 9)).pack(side="left", padx=2, ipady=4)

            # نوع الخروج
            et_cb = ttk.Combobox(
                row, textvariable=et_v,
                values=[e[0] for e in EXIT_TYPE_OPTIONS],
                width=11, state="readonly", font=("Arial", 9)
            )
            et_cb.pack(side="left", padx=(4, 2))
            # ربط القيمة العربية بالإنجليزية
            _et_map_rev = {e[0]: e[1] for e in EXIT_TYPE_OPTIONS}
            _et_map_fwd = {e[1]: e[0] for e in EXIT_TYPE_OPTIONS}
            current_ar = _et_map_fwd.get(et_v.get(), "—")
            et_cb.set(current_ar)

            def _on_et_select(event, cb=et_cb, var=et_v, m=_et_map_rev):
                var.set(m.get(cb.get(), ""))
            et_cb.bind("<<ComboboxSelected>>", _on_et_select)

        if not employees:
            lbl(self.att_inner, "لا يوجد موظفون نشطون — أضف موظفين أولاً",
                11, fg=SUBTEXT).pack(pady=40)

    def _mark_all_present(self):
        for v in self.att_status_vars.values():
            v.set("present")

    def _save_attendance(self):
        d = self.att_date.get()
        if not d:
            messagebox.showwarning("تنبيه", "يرجى تحديد التاريخ")
            return
        if not self.att_status_vars:
            messagebox.showinfo("تنبيه", "لا يوجد موظفون لتسجيل حضورهم")
            return
        for emp_id, sv in self.att_status_vars.items():
            db.record_attendance(
                emp_id, d, sv.get(),
                self.att_checkin_vars[emp_id].get().strip()  or None,
                self.att_checkout_vars[emp_id].get().strip() or None,
                self.att_exittype_vars[emp_id].get().strip() or None,
                None, self.user["id"]
            )
        messagebox.showinfo("تم الحفظ", f"✔ تم حفظ حضور {len(self.att_status_vars)} موظف")
        self._load_attendance_day()

    # ════════════════ التقارير ════════════════
    def _build_reports_tab(self):
        f = self.tab_rep

        # فلتر
        flt = tk.Frame(f, bg=SECONDARY)
        flt.pack(fill="x")
        inner = tk.Frame(flt, bg=SECONDARY)
        inner.pack(padx=20, pady=12)

        lbl(inner, "من:", 10, bg=SECONDARY).grid(row=0, column=7, padx=(0, 4))
        self.rep_from = tk.StringVar(value=(date.today() - timedelta(days=30)).isoformat())
        entry(inner, self.rep_from, width=12, justify="center").grid(row=0, column=6, padx=4, ipady=5)

        lbl(inner, "إلى:", 10, bg=SECONDARY).grid(row=0, column=5, padx=(0, 4))
        self.rep_to = tk.StringVar(value=date.today().isoformat())
        entry(inner, self.rep_to, width=12, justify="center").grid(row=0, column=4, padx=4, ipady=5)

        lbl(inner, "القسم:", 10, bg=SECONDARY).grid(row=0, column=3, padx=(0, 4))
        self.rep_dept = tk.StringVar(value="الكل")
        self.rep_dept_cb = ttk.Combobox(inner, textvariable=self.rep_dept,
                                         values=["الكل"] + db.get_departments(),
                                         width=16, state="readonly")
        self.rep_dept_cb.grid(row=0, column=2, padx=4)

        lbl(inner, "الموظف:", 10, bg=SECONDARY).grid(row=0, column=1, padx=(0, 4))
        self.rep_emp = tk.StringVar(value="الكل")
        emp_names = ["الكل"] + [e["full_name"] for e in db.get_all_employees()]
        self.rep_emp_cb = ttk.Combobox(inner, textvariable=self.rep_emp,
                                        values=emp_names, width=22, state="readonly")
        self.rep_emp_cb.grid(row=0, column=0, padx=4)

        # أزرار
        brow = tk.Frame(flt, bg=SECONDARY)
        brow.pack(padx=20, pady=(0, 10))
        btn(brow, "📊 إنشاء التقرير",   self._generate_report).pack(side="right", padx=5)
        btn(brow, "📥 تصدير Excel",      self._export_excel, color=PRESENT_CLR).pack(side="right", padx=5)
        btn(brow, "📄 تصدير PDF",        self._export_pdf,   color=LATE_CLR).pack(side="right", padx=5)

        self.rep_summary = tk.StringVar(value="")
        lbl(f, "", 10, fg=SUBTEXT, textvariable=self.rep_summary,
            ).pack(anchor="e", padx=20, pady=4)

        # جدول النتائج
        tf = tk.Frame(f, bg=BG)
        tf.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        cols = ("code", "name", "organization", "department", "date",
                "status", "check_in", "check_out", "exit_type")
        self.rep_tree = ttk.Treeview(tf, columns=cols, show="headings")
        for col, heading, w in [
            ("code",         "الكود",           75),
            ("name",         "اسم الموظف",     180),
            ("organization", "الجهة",           140),
            ("department",   "القسم",           130),
            ("date",         "التاريخ",         100),
            ("status",       "الحالة",           85),
            ("check_in",     "وقت الدخول",       90),
            ("check_out",    "وقت الخروج",       90),
            ("exit_type",    "نوع الخروج",      110),
        ]:
            self.rep_tree.heading(col, text=heading)
            self.rep_tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self.rep_tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.rep_tree.xview)
        self.rep_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self.rep_tree.pack(side="left", fill="both", expand=True)
        setup_treeview_tags(self.rep_tree)
        self.rep_tree.tag_configure("even", background=ROW_EVEN)

    def _generate_report(self):
        # تحديث قوائم الفلتر
        self.rep_dept_cb["values"] = ["الكل"] + db.get_departments()
        emp_names = ["الكل"] + [e["full_name"] for e in db.get_all_employees()]
        self.rep_emp_cb["values"] = emp_names

        dept     = None if self.rep_dept.get() == "الكل" else self.rep_dept.get()
        emp_id   = None
        emp_name = self.rep_emp.get()
        if emp_name != "الكل":
            for e in db.get_all_employees():
                if e["full_name"] == emp_name:
                    emp_id = e["id"]
                    break

        self.rep_data = db.get_attendance_report(
            self.rep_from.get(), self.rep_to.get(), emp_id, dept)

        for row in self.rep_tree.get_children():
            self.rep_tree.delete(row)

        counts = Counter()
        for i, r in enumerate(self.rep_data):
            st  = r.get("status", "")
            counts[st] += 1
            tag = st if st in STATUS_AR else ""
            tags = (tag, "even") if i % 2 == 0 else (tag,)
            et = r.get("exit_type", "") or ""
            self.rep_tree.insert("", "end",
                values=(r["employee_code"], r["full_name"],
                        r.get("organization", "") or "",
                        r.get("department",   "") or "",
                        r["date"],
                        STATUS_AR.get(st, st),
                        r.get("check_in",  "") or "",
                        r.get("check_out", "") or "",
                        EXIT_TYPE_AR.get(et, et)),
                tags=tags)

        parts = [f"الإجمالي: {len(self.rep_data)}"] + \
                [f"{STATUS_AR[s]}: {c}" for s, c in counts.items() if s in STATUS_AR]
        self.rep_summary.set("  |  ".join(parts))

    def _export_excel(self):
        if not self.rep_data:
            messagebox.showinfo("تنبيه", "يرجى إنشاء التقرير أولاً")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("All files", "*.*")],
            title="حفظ ملف Excel")
        if path:
            try:
                import export_utils as eu
                eu.export_to_excel(self.rep_data, self.rep_from.get(),
                                   self.rep_to.get(), path)
                messagebox.showinfo("تم", f"تم تصدير الملف:\n{path}")
            except ImportError:
                messagebox.showerror("خطأ", "مكتبة openpyxl غير مثبتة.\nشغّل:  pip install openpyxl")
            except Exception as e:
                messagebox.showerror("خطأ", str(e))

    def _export_pdf(self):
        if not self.rep_data:
            messagebox.showinfo("تنبيه", "يرجى إنشاء التقرير أولاً")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("All files", "*.*")],
            title="حفظ ملف PDF")
        if path:
            try:
                import export_utils as eu
                eu.export_to_pdf(self.rep_data, self.rep_from.get(),
                                 self.rep_to.get(), path)
                messagebox.showinfo("تم", f"تم تصدير الملف:\n{path}")
            except ImportError:
                messagebox.showerror("خطأ", "مكتبة reportlab غير مثبتة.\nشغّل:  pip install reportlab")
            except Exception as e:
                messagebox.showerror("خطأ", str(e))

    # ════════════════ المستخدمون ════════════════
    def _build_users_tab(self):
        f = self.tab_usr

        tb = tk.Frame(f, bg=BG)
        tb.pack(fill="x", padx=20, pady=14)
        btn(tb, "➕  إضافة مستخدم",      self._add_user).pack(side="right", padx=4)
        btn(tb, "🔑  تغيير كلمة المرور", self._change_password, color=CARD).pack(side="right", padx=4)
        btn(tb, "🗑  حذف",               self._delete_user, color=ABSENT_CLR).pack(side="right", padx=4)

        tf = tk.Frame(f, bg=BG)
        tf.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        cols = ("id", "username", "role", "full_name", "created_at")
        self.usr_tree = ttk.Treeview(tf, columns=cols, show="headings")
        for col, heading, w in [
            ("id",         "#",              50),
            ("username",   "اسم المستخدم",  160),
            ("role",       "الدور",          100),
            ("full_name",  "الاسم الكامل",  220),
            ("created_at", "تاريخ الإنشاء", 160),
        ]:
            self.usr_tree.heading(col, text=heading)
            self.usr_tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.usr_tree.yview)
        self.usr_tree.configure(yscrollcommand=vsb.set)
        self.usr_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.usr_tree.tag_configure("even", background=ROW_EVEN)
        self._load_users()

    def _load_users(self):
        for row in self.usr_tree.get_children():
            self.usr_tree.delete(row)
        for i, u in enumerate(db.get_all_users()):
            role_ar = "مدير" if u["role"] == "admin" else "موظف"
            tags    = ("even",) if i % 2 == 0 else ()
            self.usr_tree.insert("", "end", iid=str(u["id"]),
                values=(u["id"], u["username"], role_ar,
                        u["full_name"], u["created_at"]),
                tags=tags)

    def _selected_user_id(self):
        sel = self.usr_tree.selection()
        return int(sel[0]) if sel else None

    def _add_user(self):
        UserDialog(self.root, self._load_users)

    def _change_password(self):
        uid = self._selected_user_id()
        if uid is None:
            messagebox.showinfo("تنبيه", "يرجى اختيار مستخدم")
            return
        new_pw = simpledialog.askstring("تغيير كلمة المرور",
                                        "أدخل كلمة المرور الجديدة:", show="*")
        if new_pw:
            if len(new_pw) < 6:
                messagebox.showwarning("تنبيه", "كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                return
            db.change_password(uid, new_pw)
            messagebox.showinfo("تم", "تم تغيير كلمة المرور بنجاح")

    def _delete_user(self):
        uid = self._selected_user_id()
        if uid is None:
            messagebox.showinfo("تنبيه", "يرجى اختيار مستخدم")
            return
        if uid == self.user["id"]:
            messagebox.showwarning("تنبيه", "لا يمكنك حذف حسابك الخاص")
            return
        if messagebox.askyesno("تأكيد الحذف", "هل تريد حذف هذا المستخدم؟"):
            db.delete_user(uid)
            self._load_users()


# ══════════════════════════════════════════════════════════
# نوافذ الحوار
# ══════════════════════════════════════════════════════════

class EmployeeDialog:
    def __init__(self, parent, emp_data, on_save):
        self.emp_data = emp_data
        self.on_save  = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("تعديل الموظف" if emp_data else "إضافة موظف جديد")
        self.win.geometry("460x640")
        self.win.configure(bg=BG)
        self.win.grab_set()
        self.win.resizable(False, False)
        self.win.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - 460) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 640) // 2
        self.win.geometry(f"460x640+{x}+{y}")
        self._build()

    def _build(self):
        lbl(self.win, "بيانات الموظف", 14, bold=True).pack(pady=14)
        frm = tk.Frame(self.win, bg=BG)
        frm.pack(fill="both", expand=True, padx=35)

        ed = self.emp_data or {}
        self.vars = {}
        fields = [
            ("كود الموظف *",     "employee_code", ed.get("employee_code", "")),
            ("الاسم الكامل *",   "full_name",     ed.get("full_name",     "")),
            ("الجهة التابع لها", "organization",  ed.get("organization",  "")),
            ("القسم",             "department",    ed.get("department",    "")),
            ("المسمى الوظيفي",   "position",      ed.get("position",      "")),
            ("رقم الهاتف",        "phone",         ed.get("phone",         "")),
            ("البريد الإلكتروني","email",          ed.get("email",         "")),
            ("تاريخ التعيين\n(YYYY-MM-DD)", "hire_date", ed.get("hire_date", "")),
        ]
        for label, key, val in fields:
            lbl(frm, label, 10, fg=SUBTEXT, anchor="e").pack(fill="x", pady=(7, 2))
            v = tk.StringVar(value=str(val) if val else "")
            entry(frm, v).pack(fill="x", ipady=7)
            self.vars[key] = v

        if self.emp_data:
            lbl(frm, "الحالة", 10, fg=SUBTEXT, anchor="e").pack(fill="x", pady=(7, 2))
            self.status_v = tk.StringVar(value=ed.get("status", "active"))
            ttk.Combobox(frm, textvariable=self.status_v,
                         values=["active", "inactive"],
                         state="readonly").pack(fill="x")

        row = tk.Frame(self.win, bg=BG)
        row.pack(pady=14)
        btn(row, "💾 حفظ",   self._save).pack(side="right", padx=6)
        btn(row, "إلغاء", self.win.destroy, color=CARD).pack(side="right", padx=6)

    def _save(self):
        code = self.vars["employee_code"].get().strip()
        name = self.vars["full_name"].get().strip()
        if not code or not name:
            messagebox.showwarning("تنبيه", "الكود والاسم مطلوبان", parent=self.win)
            return
        try:
            if self.emp_data:
                status = self.status_v.get() if hasattr(self, "status_v") else "active"
                db.update_employee(
                    self.emp_data["id"], code, name,
                    self.vars["department"].get(),
                    self.vars["organization"].get(),
                    self.vars["position"].get(),
                    self.vars["phone"].get(),
                    self.vars["email"].get(),
                    self.vars["hire_date"].get(),
                    status)
            else:
                db.add_employee(code, name,
                    self.vars["department"].get(),
                    self.vars["organization"].get(),
                    self.vars["position"].get(),
                    self.vars["phone"].get(),
                    self.vars["email"].get(),
                    self.vars["hire_date"].get())
            self.on_save()
            self.win.destroy()
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc), parent=self.win)


class UserDialog:
    def __init__(self, parent, on_save):
        self.on_save = on_save
        self.win = tk.Toplevel(parent)
        self.win.title("إضافة مستخدم جديد")
        self.win.geometry("420x440")
        self.win.configure(bg=BG)
        self.win.grab_set()
        self.win.resizable(False, False)
        self.win.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - 420) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 440) // 2
        self.win.geometry(f"420x440+{x}+{y}")
        self._build()

    def _build(self):
        lbl(self.win, "إضافة مستخدم جديد", 14, bold=True).pack(pady=14)
        frm = tk.Frame(self.win, bg=BG)
        frm.pack(fill="both", expand=True, padx=35)

        self.vars = {}
        fields = [
            ("الاسم الكامل *",           "full_name",        False),
            ("اسم المستخدم *",           "username",         False),
            ("كلمة المرور *",            "password",         True),
            ("تأكيد كلمة المرور *",      "confirm_password", True),
        ]
        for label, key, is_pw in fields:
            lbl(frm, label, 10, fg=SUBTEXT, anchor="e").pack(fill="x", pady=(7, 2))
            v = tk.StringVar()
            entry(frm, v, show="●" if is_pw else "").pack(fill="x", ipady=7)
            self.vars[key] = v

        lbl(frm, "الدور:", 10, fg=SUBTEXT, anchor="e").pack(fill="x", pady=(7, 2))
        self.role_v = tk.StringVar(value="employee")
        ttk.Combobox(frm, textvariable=self.role_v,
                     values=["employee", "admin"],
                     state="readonly").pack(fill="x")

        row = tk.Frame(self.win, bg=BG)
        row.pack(pady=14)
        btn(row, "💾 حفظ",   self._save).pack(side="right", padx=6)
        btn(row, "إلغاء", self.win.destroy, color=CARD).pack(side="right", padx=6)

    def _save(self):
        full  = self.vars["full_name"].get().strip()
        uname = self.vars["username"].get().strip()
        pw    = self.vars["password"].get()
        conf  = self.vars["confirm_password"].get()
        if not full or not uname or not pw:
            messagebox.showwarning("تنبيه", "يرجى ملء جميع الحقول المطلوبة", parent=self.win)
            return
        if pw != conf:
            messagebox.showwarning("تنبيه", "كلمة المرور وتأكيدها غير متطابقتين", parent=self.win)
            return
        if len(pw) < 6:
            messagebox.showwarning("تنبيه", "كلمة المرور يجب أن تكون 6 أحرف على الأقل", parent=self.win)
            return
        try:
            db.add_user(uname, pw, self.role_v.get(), full)
            self.on_save()
            self.win.destroy()
        except Exception as exc:
            messagebox.showerror("خطأ", f"حدث خطأ (ربما اسم المستخدم مكرر):\n{exc}", parent=self.win)
