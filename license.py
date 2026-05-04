"""
license.py – نظام الترخيص لنظام الحضور والغياب
يعمل offline بالكامل — لا يحتاج إنترنت
"""

import hmac
import hashlib
import base64
import os
from datetime import date

# ── المفتاح السري (مخفي داخل الكود — لا يُغيَّر بعد البيع) ──────────────
_SECRET = b"@tt3nd@nc3_$y$_k3y_2025_#mgg#"

APP_VERSION = "2.0.0"


# ── توليد المفتاح (للمطور فقط) ───────────────────────────────────────────

def generate_license(customer_name: str, expire_date: str) -> str:
    """
    توليد مفتاح ترخيص.
    expire_date: تاريخ الانتهاء YYYY-MM-DD أو 'lifetime' للأبد
    مثال: generate_license("شركة النور", "2027-12-31")
    """
    data = f"{customer_name.strip()}|{expire_date}"
    sig = hmac.new(_SECRET, data.encode("utf-8"), hashlib.sha256).hexdigest()[:20]
    payload = f"{data}|{sig}"
    key = base64.b64encode(payload.encode("utf-8")).decode("utf-8")
    # قسّمه إلى مجموعات لتسهيل القراءة
    chunks = [key[i:i+6] for i in range(0, len(key), 6)]
    return "-".join(chunks)


# ── التحقق من المفتاح ────────────────────────────────────────────────────

def verify_license(key: str) -> dict:
    """
    يُرجع:
      {"valid": True,  "customer": "...", "expire": "...", "days_left": N}
      {"valid": False, "reason": "...", "expired": True/False}
    """
    if not key or not key.strip():
        return {"valid": False, "reason": "لم يُدخَل مفتاح ترخيص", "expired": False}
    try:
        # إزالة الشرطات وفك الترميز
        raw = key.replace("-", "").replace(" ", "")
        payload = base64.b64decode(raw.encode("utf-8")).decode("utf-8")
        parts = payload.split("|")
        if len(parts) != 3:
            return {"valid": False, "reason": "مفتاح غير صالح", "expired": False}

        customer, expire, sig = parts

        # التحقق من التوقيع
        data     = f"{customer}|{expire}"
        expected = hmac.new(_SECRET, data.encode("utf-8"), hashlib.sha256).hexdigest()[:20]
        if not hmac.compare_digest(sig, expected):
            return {"valid": False, "reason": "مفتاح غير صالح أو مُعدَّل", "expired": False}

        # التحقق من انتهاء الصلاحية
        if expire == "lifetime":
            return {"valid": True, "customer": customer,
                    "expire": "مدى الحياة", "days_left": 99999}

        exp_date  = date.fromisoformat(expire)
        today     = date.today()
        days_left = (exp_date - today).days

        if days_left < 0:
            return {
                "valid": False,
                "reason": f"انتهى الترخيص في {expire} (منذ {abs(days_left)} يوم)",
                "expired": True,
                "customer": customer,
                "expire": expire,
            }

        return {
            "valid": True,
            "customer": customer,
            "expire": expire,
            "days_left": days_left,
        }

    except Exception:
        return {"valid": False, "reason": "مفتاح غير صالح", "expired": False}


# ── حالة الترخيص من قاعدة البيانات ─────────────────────────────────────

def get_license_status() -> dict:
    """يجلب المفتاح المخزّن ويتحقق منه"""
    try:
        import database as db
        key = db.get_setting("license_key", "")
        if not key:
            return {"valid": False, "reason": "لا يوجد ترخيص", "expired": False}
        return verify_license(key)
    except Exception as e:
        return {"valid": False, "reason": str(e), "expired": False}


def save_license(key: str) -> dict:
    """يتحقق من المفتاح ثم يحفظه إن كان صالحاً"""
    result = verify_license(key)
    if result["valid"]:
        import database as db
        db.set_setting("license_key", key.replace(" ", ""))
    return result


def is_licensed() -> bool:
    """هل النظام مرخَّص حالياً؟"""
    return get_license_status().get("valid", False)


def days_until_expiry() -> int:
    status = get_license_status()
    return status.get("days_left", 0)
