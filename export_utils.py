"""
export_utils.py - نظام الحضور والغياب
تصدير التقارير إلى Excel و PDF
"""

import os
from datetime import datetime
from collections import Counter

STATUS_AR = {
    "present": "حاضر",
    "absent":  "غائب",
    "late":    "متأخر",
    "leave":   "إجازة",
}

EXIT_TYPE_AR = {
    "work":     "في مهمة عمل",
    "vacation": "إجازة",
    "sick":     "مرض",
}

STATUS_COLORS_HEX = {
    "present": "27AE60",
    "absent":  "E74C3C",
    "late":    "F39C12",
    "leave":   "3498DB",
}


def _find_arabic_font():
    """البحث عن خط يدعم العربية في النظام"""
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/noto-cjk/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        # Windows
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _process_arabic(text):
    """معالجة النص العربي للعرض الصحيح في PDF"""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        if not text:
            return ""
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except ImportError:
        return str(text) if text else ""


# ─────────────────────────────────────────────────────
# تصدير Excel
# ─────────────────────────────────────────────────────

def export_to_excel(data, from_date, to_date, filepath):
    """تصدير بيانات الحضور إلى ملف Excel"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "تقرير الحضور والغياب"
    ws.sheet_view.rightToLeft = True  # اتجاه RTL

    # ─── صف العنوان ───
    ws.merge_cells("A1:I1")
    c = ws["A1"]
    c.value = f"تقرير الحضور والغياب  —  من {from_date}  إلى {to_date}"
    c.font      = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    c.fill      = PatternFill(start_color="1a1a2e", end_color="1a1a2e", fill_type="solid")
    c.alignment = Alignment(horizontal="center", vertical="center", readingOrder=2)
    ws.row_dimensions[1].height = 38

    # ─── صف تاريخ الإنشاء ───
    ws.merge_cells("A2:I2")
    c = ws["A2"]
    c.value     = f"تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d  %H:%M')}"
    c.font      = Font(name="Arial", size=9, italic=True, color="888888")
    c.alignment = Alignment(horizontal="center", readingOrder=2)
    ws.row_dimensions[2].height = 18

    # ─── رؤوس الأعمدة ───
    headers = [
        "كود الموظف", "اسم الموظف", "الجهة",
        "القسم", "التاريخ", "الحالة",
        "وقت الدخول", "وقت الخروج", "نوع الخروج"
    ]
    col_widths = [13, 26, 20, 18, 13, 10, 13, 13, 16]

    for col, header in enumerate(headers, 1):
        c = ws.cell(row=3, column=col, value=header)
        c.font      = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        c.fill      = PatternFill(start_color="0f3460", end_color="0f3460", fill_type="solid")
        c.alignment = Alignment(horizontal="center", vertical="center", readingOrder=2)
    ws.row_dimensions[3].height = 28

    # ─── بيانات الصفوف ───
    for row_idx, row in enumerate(data, 4):
        status  = row.get("status", "")
        row_bg  = "F0F4FF" if row_idx % 2 == 0 else "FFFFFF"

        values = [
            row.get("employee_code", ""),
            row.get("full_name",     ""),
            row.get("organization",  "") or "",
            row.get("department",    "") or "",
            row.get("date",          ""),
            STATUS_AR.get(status, status),
            row.get("check_in",  "") or "",
            row.get("check_out", "") or "",
            EXIT_TYPE_AR.get(row.get("exit_type", "") or "", ""),
        ]

        for col, value in enumerate(values, 1):
            c = ws.cell(row=row_idx, column=col, value=value)
            c.alignment = Alignment(horizontal="center", vertical="center", readingOrder=2)
            c.fill      = PatternFill(start_color=row_bg, end_color=row_bg, fill_type="solid")
            if col == 6 and status:   # عمود الحالة
                clr = STATUS_COLORS_HEX.get(status, "000000")
                c.font = Font(name="Arial", size=10, bold=True, color=clr)
            else:
                c.font = Font(name="Arial", size=10)

        ws.row_dimensions[row_idx].height = 22

    # ─── عرض الأعمدة ───
    for col, width in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width

    # ─── صف الملخص ───
    if data:
        summary_row = len(data) + 4
        ws.merge_cells(f"A{summary_row}:I{summary_row}")
        counts  = Counter(r.get("status") for r in data)
        summary = "الملخص:  " + "   |   ".join(
            [f"{STATUS_AR.get(s, s)}: {c}" for s, c in counts.items() if s in STATUS_AR])
        c = ws.cell(row=summary_row, column=1, value=summary)
        c.font      = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        c.fill      = PatternFill(start_color="16213e", end_color="16213e", fill_type="solid")
        c.alignment = Alignment(horizontal="center", readingOrder=2)
        ws.row_dimensions[summary_row].height = 26

    wb.save(filepath)


# ─────────────────────────────────────────────────────
# تصدير PDF
# ─────────────────────────────────────────────────────

def export_to_pdf(data, from_date, to_date, filepath):
    """تصدير بيانات الحضور إلى ملف PDF مع دعم العربية"""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib          import colors
    from reportlab.lib.units    import cm
    from reportlab.lib.styles  import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus    import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer)
    from reportlab.pdfbase     import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # تسجيل الخط العربي
    font_name = "Helvetica"
    font_path = _find_arabic_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("ArabicFont", font_path))
            font_name = "ArabicFont"
        except Exception:
            font_name = "Helvetica"

    def ar(text):
        return _process_arabic(text) if font_name == "ArabicFont" else (str(text) if text else "")

    # ─── إعداد المستند ───
    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4),
        rightMargin=1.5 * cm, leftMargin=1.5 * cm,
        topMargin=1.5 * cm,   bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ATitle", parent=styles["Title"],
        fontName=font_name, fontSize=15,
        textColor=colors.HexColor("#1a1a2e"),
        alignment=1, spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "ASub", parent=styles["Normal"],
        fontName=font_name, fontSize=9,
        textColor=colors.grey,
        alignment=1, spaceAfter=3,
    )

    elements = []
    elements.append(Paragraph(ar("تقرير الحضور والغياب"), title_style))
    elements.append(Paragraph(ar(f"من {from_date}  إلى  {to_date}"), sub_style))
    elements.append(Paragraph(
        ar(f"تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d  %H:%M')}"), sub_style))
    elements.append(Spacer(1, 0.5 * cm))

    # ─── جدول البيانات ───
    col_labels = ["كود الموظف", "اسم الموظف", "الجهة", "القسم", "التاريخ",
                  "الحالة", "وقت الدخول", "وقت الخروج", "نوع الخروج"]
    col_widths  = [2.2*cm, 5*cm, 3.8*cm, 3.5*cm, 2.8*cm, 2.3*cm, 2.3*cm, 2.3*cm, 3*cm]

    table_data = [[ar(h) for h in col_labels]]
    status_row_colors = {}

    for row in data:
        status = row.get("status", "")
        status_row_colors[len(table_data)] = status
        table_data.append([
            ar(row.get("employee_code", "")),
            ar(row.get("full_name",     "")),
            ar(row.get("organization",  "") or ""),
            ar(row.get("department",    "") or ""),
            row.get("date", ""),
            ar(STATUS_AR.get(status, status)),
            row.get("check_in",  "") or "",
            row.get("check_out", "") or "",
            ar(EXIT_TYPE_AR.get(row.get("exit_type", "") or "", "")),
        ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    status_color_map = {
        "present": colors.HexColor("#27AE60"),
        "absent":  colors.HexColor("#E74C3C"),
        "late":    colors.HexColor("#F39C12"),
        "leave":   colors.HexColor("#3498DB"),
    }

    tbl_style = TableStyle([
        # رأس الجدول
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, -1), font_name),
        ("FONTSIZE",    (0, 0), (-1,  0), 10),
        ("FONTSIZE",    (0, 1), (-1, -1),  9),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f0f4ff")]),
    ])

    # تلوين عمود الحالة لكل صف
    for row_idx, status in status_row_colors.items():
        clr = status_color_map.get(status)
        if clr:
            tbl_style.add("TEXTCOLOR", (4, row_idx), (4, row_idx), clr)
            tbl_style.add("FONTNAME",  (4, row_idx), (4, row_idx), font_name)

    table.setStyle(tbl_style)
    elements.append(table)

    # ─── ملخص ───
    if data:
        elements.append(Spacer(1, 0.4 * cm))
        counts  = Counter(r.get("status") for r in data)
        summary = ar("الملخص:  ") + "   |   ".join(
            [ar(f"{STATUS_AR.get(s, s)}: {c}") for s, c in counts.items() if s in STATUS_AR])
        elements.append(Paragraph(summary, sub_style))

    doc.build(elements)


# ─────────────────────────────────────────────────────
# تصدير تقرير الموظف الفردي إلى PDF
# ─────────────────────────────────────────────────────

def export_employee_report_pdf(emp, records, year_stats, year, month, filepath):
    """
    تصدير تقرير موظف فردي (شهري + سنوي) إلى PDF
    emp: قاموس بيانات الموظف
    records: سجلات الشهر المختار
    year_stats: إحصائيات 12 شهر
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib          import colors
    from reportlab.lib.units    import cm
    from reportlab.lib.styles  import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus    import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer, HRFlowable)
    from reportlab.pdfbase     import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # تسجيل الخط العربي
    font_name = "Helvetica"
    font_path = _find_arabic_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("ArabicFont", font_path))
            font_name = "ArabicFont"
        except Exception:
            font_name = "Helvetica"

    def ar(text):
        return _process_arabic(text) if font_name == "ArabicFont" else (str(text) if text else "")

    MONTH_NAMES = ["","يناير","فبراير","مارس","أبريل","مايو","يونيو",
                   "يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm,   bottomMargin=1.5*cm,
    )

    styles = getSampleStyleSheet()
    def style(name, **kw):
        kw.setdefault("fontName", font_name)
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    title_st = style("T", fontSize=16, textColor=colors.HexColor("#1976D2"),
                     alignment=1, spaceAfter=4)
    sub_st   = style("S", fontSize=10, textColor=colors.grey,
                     alignment=1, spaceAfter=2)
    sec_st   = style("Sec", fontSize=12, textColor=colors.HexColor("#0f3460"),
                     spaceBefore=8, spaceAfter=4)

    elements = []

    # ── عنوان ──
    elements.append(Paragraph(ar("تقرير الموظف الفردي"), title_st))
    elements.append(Paragraph(
        ar(f"نظام الحضور والغياب  —  إنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), sub_st))
    elements.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#1976D2"), spaceAfter=8))

    # ── بيانات الموظف ──
    elements.append(Paragraph(ar("بيانات الموظف"), sec_st))
    emp_data = [
        [ar("الاسم"),       ar(emp.get("full_name","") or ""),
         ar("الكود"),       ar(emp.get("employee_code","") or "")],
        [ar("القسم"),       ar(emp.get("department","") or "—"),
         ar("الجهة"),       ar(emp.get("organization","") or "—")],
        [ar("المنصب"),      ar(emp.get("position","") or "—"),
         ar("تاريخ التعيين"), ar(emp.get("hire_date","") or "—")],
        [ar("رصيد الإجازة السنوية"),
         ar(f"{emp.get('annual_leave_days', 21)} يوم"),
         ar("الفرع"), ar(emp.get("branch","") or "—")],
    ]
    emp_table = Table(emp_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    emp_table.setStyle(TableStyle([
        ("FONTNAME",   (0,0),(-1,-1), font_name),
        ("FONTSIZE",   (0,0),(-1,-1), 10),
        ("BACKGROUND", (0,0),(0,-1),  colors.HexColor("#e3f2fd")),
        ("BACKGROUND", (2,0),(2,-1),  colors.HexColor("#e3f2fd")),
        ("FONTNAME",   (0,0),(0,-1),  font_name),
        ("ALIGN",      (0,0),(-1,-1), "CENTER"),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("GRID",       (0,0),(-1,-1), 0.5, colors.HexColor("#bbdefb")),
        ("TOPPADDING", (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 0.4*cm))

    # ── ملخص السنة ──
    if year_stats:
        elements.append(Paragraph(ar(f"ملخص سنة {year}"), sec_st))
        yr_headers = [ar("الشهر"), ar("حاضر"), ar("غائب"), ar("متأخر"), ar("إجازة"), ar("أيام العمل")]
        yr_data = [yr_headers]
        for s in year_stats:
            m = s.get("month", 0)
            yr_data.append([
                ar(MONTH_NAMES[m] if 1 <= m <= 12 else str(m)),
                str(s.get("present", 0)),
                str(s.get("absent",  0)),
                str(s.get("late",    0)),
                str(s.get("leave",   0)),
                str(s.get("work_days", 0)),
            ])
        yr_table = Table(yr_data, colWidths=[3*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2.5*cm], repeatRows=1)
        yr_table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0),(-1,0), colors.HexColor("#0f3460")),
            ("TEXTCOLOR",   (0,0),(-1,0), colors.white),
            ("FONTNAME",    (0,0),(-1,-1), font_name),
            ("FONTSIZE",    (0,0),(-1,-1), 9),
            ("ALIGN",       (0,0),(-1,-1), "CENTER"),
            ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
            ("GRID",        (0,0),(-1,-1), 0.4, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f0f4ff")]),
            ("TOPPADDING",  (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ]))
        elements.append(yr_table)
        elements.append(Spacer(1, 0.4*cm))

    # ── سجلات الشهر ──
    if records:
        elements.append(Paragraph(
            ar(f"سجلات {MONTH_NAMES[month] if 1<=month<=12 else month} {year}"), sec_st))
        rec_headers = [ar("التاريخ"), ar("الحالة"), ar("دخول"), ar("خروج"), ar("نوع الخروج"), ar("ملاحظات")]
        rec_data = [rec_headers]
        rec_colors = {}
        sc_map = {
            "present": colors.HexColor("#27AE60"),
            "absent":  colors.HexColor("#E74C3C"),
            "late":    colors.HexColor("#F39C12"),
            "leave":   colors.HexColor("#3498DB"),
        }
        for r in records:
            status = r.get("status","")
            rec_colors[len(rec_data)] = sc_map.get(status)
            rec_data.append([
                r.get("date",""),
                ar(STATUS_AR.get(status, status)),
                r.get("check_in","") or "—",
                r.get("check_out","") or "—",
                ar(EXIT_TYPE_AR.get(r.get("exit_type","") or "", "")),
                ar(r.get("notes","") or ""),
            ])
        rec_table = Table(rec_data,
                          colWidths=[2.8*cm, 2.2*cm, 2.3*cm, 2.3*cm, 3*cm, 5.5*cm],
                          repeatRows=1)
        rec_style = TableStyle([
            ("BACKGROUND",  (0,0),(-1,0), colors.HexColor("#0f3460")),
            ("TEXTCOLOR",   (0,0),(-1,0), colors.white),
            ("FONTNAME",    (0,0),(-1,-1), font_name),
            ("FONTSIZE",    (0,0),(-1,-1), 9),
            ("ALIGN",       (0,0),(-1,-1), "CENTER"),
            ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
            ("GRID",        (0,0),(-1,-1), 0.4, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f0f4ff")]),
            ("TOPPADDING",  (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ])
        for row_idx, clr in rec_colors.items():
            if clr:
                rec_style.add("TEXTCOLOR", (1, row_idx), (1, row_idx), clr)
        rec_table.setStyle(rec_style)
        elements.append(rec_table)

    doc.build(elements)


# ─────────────────────────────────────────────────────
# بطاقة هوية الموظف (CR80 - حجم بطاقة الائتمان)
# ─────────────────────────────────────────────────────

def export_employee_id_card(emp, filepath):
    """
    تصدير بطاقة هوية الموظف بحجم بطاقة ائتمان (85.6 × 54 mm)
    تحتوي على: اسم، كود، قسم، جهة، باركود
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    CARD_W = 85.6 * mm
    CARD_H = 54.0 * mm

    font_name = "Helvetica"
    font_path = _find_arabic_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("IDFont", font_path))
            font_name = "IDFont"
        except Exception:
            font_name = "Helvetica"

    def ar(text):
        return _process_arabic(text) if font_name == "IDFont" else (str(text) if text else "")

    c = rl_canvas.Canvas(filepath, pagesize=(CARD_W, CARD_H))

    # ── خلفية داكنة ──────────────────────────────────
    c.setFillColor(colors.HexColor("#0f3460"))
    c.rect(0, 0, CARD_W, CARD_H, fill=1, stroke=0)

    # ── شريط علوي أحمر (12mm) ─────────────────────────
    HEADER_H = 12 * mm
    c.setFillColor(colors.HexColor("#e94560"))
    c.rect(0, CARD_H - HEADER_H, CARD_W, HEADER_H, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont(font_name, 7.5)
    c.drawCentredString(CARD_W / 2, CARD_H - 7.5 * mm,
                        ar("نظام الحضور والغياب  —  بطاقة هوية"))

    # ── منطقة بيضاء للمعلومات ────────────────────────
    INFO_BOTTOM = 11 * mm
    INFO_TOP    = CARD_H - HEADER_H
    INFO_H      = INFO_TOP - INFO_BOTTOM

    c.setFillColor(colors.white)
    c.rect(0, INFO_BOTTOM, CARD_W, INFO_H, fill=1, stroke=0)

    # اسم الموظف
    name = ar(emp.get("full_name", "") or "")
    c.setFillColor(colors.HexColor("#0f3460"))
    c.setFont(font_name, 11)
    if c.stringWidth(name, font_name, 11) > CARD_W - 8 * mm:
        c.setFont(font_name, 9)
    c.drawCentredString(CARD_W / 2, INFO_BOTTOM + INFO_H - 7 * mm, name)

    # كود الموظف (أحمر)
    code = emp.get("employee_code", "") or ""
    c.setFillColor(colors.HexColor("#e94560"))
    c.setFont(font_name, 8.5)
    c.drawCentredString(CARD_W / 2, INFO_BOTTOM + INFO_H - 13 * mm,
                        ar(f"الكود: {code}"))

    # فاصل أفقي خفيف
    c.setStrokeColor(colors.HexColor("#dddddd"))
    c.setLineWidth(0.3)
    c.line(6 * mm, INFO_BOTTOM + INFO_H - 15 * mm,
           CARD_W - 6 * mm, INFO_BOTTOM + INFO_H - 15 * mm)

    # القسم والجهة والمنصب
    dept = (emp.get("department", "") or "")
    org  = (emp.get("organization", "") or "")
    pos  = (emp.get("position", "") or "")
    c.setFillColor(colors.HexColor("#333333"))
    c.setFont(font_name, 7.5)
    y_info = INFO_BOTTOM + INFO_H - 20 * mm
    if dept:
        c.drawCentredString(CARD_W / 2, y_info, ar(f"القسم: {dept}"))
        y_info -= 4.5 * mm
    if org:
        c.drawCentredString(CARD_W / 2, y_info, ar(org))
        y_info -= 4.5 * mm
    if pos:
        c.setFont(font_name, 7)
        c.setFillColor(colors.HexColor("#666666"))
        c.drawCentredString(CARD_W / 2, y_info, ar(pos))

    # ── باركود Code128 في القاع ───────────────────────
    try:
        from reportlab.graphics.barcode import code128
        bc = code128.Code128(
            code or "EMP",
            barWidth=0.45 * mm,
            barHeight=7 * mm,
            humanReadable=True,
            fontSize=5,
        )
        bc.drawOn(c, (CARD_W - bc.width) / 2, 2 * mm)
    except Exception:
        c.setFillColor(colors.HexColor("#333333"))
        c.setFont("Helvetica", 7)
        c.drawCentredString(CARD_W / 2, 4 * mm, code)

    c.save()
