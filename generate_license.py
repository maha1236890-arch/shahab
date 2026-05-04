#!/usr/bin/env python3
"""
generate_license.py – أداة المطور لتوليد مفاتيح الترخيص
الاستخدام: python3 generate_license.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from license import generate_license, verify_license

def main():
    print("=" * 55)
    print("  🔑  نظام الحضور والغياب — مولّد مفاتيح الترخيص")
    print("=" * 55)
    print()

    customer = input("اسم العميل / الجهة: ").strip()
    if not customer:
        print("❌ يجب إدخال اسم العميل")
        return

    print()
    print("نوع الترخيص:")
    print("  1) محدود بتاريخ")
    print("  2) مدى الحياة (Lifetime)")
    choice = input("اختر (1/2): ").strip()

    if choice == "2":
        expire = "lifetime"
    else:
        expire = input("تاريخ الانتهاء (YYYY-MM-DD، مثال: 2027-12-31): ").strip()
        # التحقق من الصيغة
        try:
            from datetime import date
            date.fromisoformat(expire)
        except ValueError:
            print("❌ صيغة التاريخ غير صحيحة. المطلوب: YYYY-MM-DD")
            return

    key = generate_license(customer, expire)

    print()
    print("=" * 55)
    print("✅  تم توليد المفتاح بنجاح")
    print("=" * 55)
    print(f"العميل : {customer}")
    print(f"ينتهي  : {expire}")
    print()
    print("المفتاح:")
    print()
    print(f"  {key}")
    print()

    # التحقق التلقائي
    result = verify_license(key)
    if result["valid"]:
        print(f"✅  التحقق: صالح — أيام متبقية: {result['days_left']}")
    else:
        print(f"❌  خطأ في التحقق: {result['reason']}")

    print("=" * 55)
    print()

    # حفظ في ملف سجل
    log_file = os.path.join(os.path.dirname(__file__), "licenses_issued.txt")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} | {customer} | {expire} | {key}\n")
        print(f"📝  تم حفظ السجل في: {log_file}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
