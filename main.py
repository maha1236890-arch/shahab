"""
main.py - نظام الحضور والغياب
نافذة تسجيل الدخول
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database as db

BG        = "#1a1a2e"
SECONDARY = "#16213e"
CARD      = "#0f3460"
ACCENT    = "#e94560"
WHITE     = "#ffffff"
SUBTEXT   = "#a0a0c0"


class LoginWindow:
    def __init__(self):
        db.init_db()

        self.root = tk.Tk()
        self.root.title("نظام الحضور والغياب")
        self.root.geometry("420x480")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # توسيط النافذة
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"420x480+{(sw-420)//2}+{(sh-480)//2}")

        self._build_ui()
        self.root.mainloop()

    def _build_ui(self):
        # رأس الصفحة
        header = tk.Frame(self.root, bg=SECONDARY, height=130)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="👥",
            font=("Arial", 42), bg=SECONDARY, fg=WHITE
        ).pack(pady=(18, 4))

        tk.Label(
            header, text="نظام الحضور والغياب",
            font=("Arial", 15, "bold"), bg=SECONDARY, fg=WHITE
        ).pack()

        # نموذج تسجيل الدخول
        form = tk.Frame(self.root, bg=BG)
        form.pack(fill="both", expand=True, padx=45, pady=30)

        tk.Label(
            form, text="اسم المستخدم",
            font=("Arial", 10), bg=BG, fg=SUBTEXT, anchor="e"
        ).pack(fill="x", pady=(0, 3))

        self.username_var = tk.StringVar()
        self._username_entry = tk.Entry(
            form, textvariable=self.username_var,
            font=("Arial", 12), justify="right",
            bg=CARD, fg=WHITE, insertbackground=WHITE,
            relief="flat", highlightthickness=1,
            highlightbackground="#334466", highlightcolor=ACCENT
        )
        self._username_entry.pack(fill="x", ipady=9)

        tk.Label(
            form, text="كلمة المرور",
            font=("Arial", 10), bg=BG, fg=SUBTEXT, anchor="e"
        ).pack(fill="x", pady=(16, 3))

        self.password_var = tk.StringVar()
        pw_entry = tk.Entry(
            form, textvariable=self.password_var, show="●",
            font=("Arial", 12), justify="right",
            bg=CARD, fg=WHITE, insertbackground=WHITE,
            relief="flat", highlightthickness=1,
            highlightbackground="#334466", highlightcolor=ACCENT
        )
        pw_entry.pack(fill="x", ipady=9)
        pw_entry.bind("<Return>", lambda e: self._login())

        tk.Button(
            form, text="تسجيل الدخول",
            font=("Arial", 13, "bold"),
            bg=ACCENT, fg=WHITE, relief="flat",
            activebackground="#c73652", activeforeground=WHITE,
            cursor="hand2", command=self._login
        ).pack(fill="x", pady=(25, 0), ipady=11)

        tk.Label(
            form,
            text="بيانات الدخول الافتراضية:  admin / admin123",
            font=("Arial", 8), bg=BG, fg="#555577"
        ).pack(pady=(14, 0))

        self._username_entry.focus_set()

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المستخدم وكلمة المرور")
            return

        user = db.authenticate(username, password)
        if user:
            self.root.destroy()
            from admin_panel import AdminPanel
            AdminPanel(user)
        else:
            messagebox.showerror("خطأ في تسجيل الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة")


if __name__ == "__main__":
    LoginWindow()
