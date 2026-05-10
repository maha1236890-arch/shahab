"""
نظام طباعة التصاريح والفواتير
Printing Utilities
"""

from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime


def _print_html(parent, html, page_size=QPrinter.A5):
    """Helper: print HTML document"""
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(page_size)

    dialog = QPrintDialog(printer, parent)
    if dialog.exec_() != QPrintDialog.Accepted:
        return False

    doc = QTextDocument()
    doc.setHtml(html)
    doc.print_(printer)
    return True


def print_visit_permit(parent, employee, visit_type, entry_time, exit_time=None):
    """طباعة تصريح دخول/خروج"""
    permit_type = 'دخول وخروج' if exit_time else 'دخول'
    exit_row = f'<tr><td class="lbl">وقت الخروج</td><td>{exit_time}</td></tr>' if exit_time else ''

    html = f"""
    <html dir="rtl">
    <head><meta charset="utf-8">
    <style>
        body {{ font-family: Arial, Tahoma; font-size: 14pt; margin: 20px; color: #222; }}
        .header {{ text-align: center; border-bottom: 3px solid #1f6feb; padding-bottom: 12px; margin-bottom: 16px; }}
        .header h1 {{ color: #1f6feb; font-size: 20pt; margin: 0 0 6px 0; }}
        .header p {{ margin: 2px; color: #555; font-size: 11pt; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        td {{ padding: 9px 12px; border: 1px solid #ccc; font-size: 13pt; }}
        td.lbl {{ font-weight: bold; background-color: #f0f4ff; width: 38%; color: #1f6feb; }}
        .sigs {{ margin-top: 40px; overflow: hidden; }}
        .sig {{ width: 45%; float: right; text-align: center; }}
        .sig:first-child {{ float: left; }}
        .sig-line {{ border-top: 1px solid #555; padding-top: 6px; margin-top: 30px; }}
        .badge {{ display:inline-block; background:#1f6feb; color:white; padding:4px 14px;
                  border-radius:12px; font-size:13pt; margin-top:6px; }}
    </style>
    </head>
    <body>
    <div class="header">
        <h1>&#127959; تصريح {permit_type}</h1>
        <p>التاريخ: {datetime.now().strftime('%Y/%m/%d')}</p>
        <p>الوقت: {datetime.now().strftime('%H:%M')}</p>
    </div>
    <table>
        <tr><td class="lbl">الاسم الوظيفي</td><td>{employee.get('job_name','')}</td></tr>
        <tr><td class="lbl">الكود</td><td>{employee.get('code','')}</td></tr>
        <tr><td class="lbl">القسم</td><td>{employee.get('department','')}</td></tr>
        <tr><td class="lbl">المحافظة</td><td>{employee.get('governorate','')}</td></tr>
        <tr><td class="lbl">الحالة الاجتماعية</td><td>{employee.get('marital_status','')}</td></tr>
        <tr><td class="lbl">نوع الزيارة</td><td><span class="badge">{visit_type}</span></td></tr>
        <tr><td class="lbl">وقت الدخول</td><td>{entry_time or ''}</td></tr>
        {exit_row}
    </table>
    <div class="sigs">
        <div class="sig"><div class="sig-line">توقيع المسؤول</div></div>
        <div class="sig"><div class="sig-line">توقيع الموظف</div></div>
    </div>
    </body></html>
    """
    return _print_html(parent, html, QPrinter.A5)


def print_nutrition_invoice(parent, date, data):
    """طباعة فاتورة التغذية"""
    total = (data.get('food_count', 0) + data.get('qat_count', 0) +
             data.get('lighter_count', 0) + data.get('cigarette_count', 0) +
             data.get('snuff_count', 0))

    html = f"""
    <html dir="rtl">
    <head><meta charset="utf-8">
    <style>
        body {{ font-family: Arial, Tahoma; font-size: 13pt; margin: 20px; color: #222; }}
        .header {{ text-align: center; border-bottom: 3px solid #238636; padding-bottom: 10px; margin-bottom: 14px; }}
        .header h1 {{ color: #238636; font-size: 20pt; margin: 0 0 4px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background-color: #238636; color: white; padding: 9px; text-align: center; font-size: 13pt; }}
        td {{ padding: 8px 12px; border: 1px solid #ccc; text-align: center; font-size: 13pt; }}
        .total-row {{ background-color: #f0fff4; font-weight: bold; font-size: 14pt; color: #238636; }}
        .notes {{ margin-top: 16px; padding: 10px; background: #f8f8f8; border-radius: 6px; }}
        .sig {{ text-align: center; margin-top: 40px; }}
        .sig-line {{ border-top: 1px solid #555; width: 50%; margin: 30px auto 0; padding-top: 6px; }}
    </style>
    </head>
    <body>
    <div class="header">
        <h1>&#127869; فاتورة التغذية</h1>
        <p>التاريخ: {date}</p>
        <p>وقت الطباعة: {datetime.now().strftime('%H:%M')}</p>
    </div>
    <table>
        <tr><th>البند</th><th>العدد</th></tr>
        <tr><td>&#127869; الوجبات الغذائية</td><td>{data.get('food_count', 0)}</td></tr>
        <tr><td>&#127807; القات</td><td>{data.get('qat_count', 0)}</td></tr>
        <tr><td>&#128293; الولاعات</td><td>{data.get('lighter_count', 0)}</td></tr>
        <tr><td>&#128684; الدخان</td><td>{data.get('cigarette_count', 0)}</td></tr>
        <tr><td>الشمة</td><td>{data.get('snuff_count', 0)}</td></tr>
        <tr class="total-row"><td>الإجمالي</td><td>{total}</td></tr>
    </table>
    {"<div class='notes'>ملاحظات: " + data.get('notes', '') + "</div>" if data.get('notes') else ''}
    <div class="sig"><div class="sig-line">توقيع المسؤول</div></div>
    </body></html>
    """
    return _print_html(parent, html, QPrinter.A5)


def print_attendance_report(parent, date, employees_data):
    """طباعة تقرير الحضور اليومي"""
    rows_html = ''
    present_count = 0
    absent_count = 0

    for emp in employees_data:
        status = emp.get('status', 'غير مسجل')
        if status == 'حاضر':
            color = '#28a745'
            present_count += 1
        elif status == 'غائب':
            color = '#dc3545'
            absent_count += 1
        else:
            color = '#888'
        rows_html += f"""
        <tr>
            <td>{emp.get('id','')}</td>
            <td>{emp.get('code','')}</td>
            <td>{emp.get('real_name','')}</td>
            <td>{emp.get('job_name','')}</td>
            <td>{emp.get('department','')}</td>
            <td style="color:{color}; font-weight:bold;">{status}</td>
            <td>{emp.get('time_in','') or ''}</td>
        </tr>
        """

    html = f"""
    <html dir="rtl">
    <head><meta charset="utf-8">
    <style>
        body {{ font-family: Arial, Tahoma; font-size: 11pt; margin: 15px; }}
        .header {{ text-align: center; border-bottom: 3px solid #1f6feb; padding-bottom: 10px; margin-bottom: 14px; }}
        .header h1 {{ color: #1f6feb; font-size: 18pt; margin: 0; }}
        .stats {{ margin: 10px 0; padding: 8px; background:#f0f4ff; border-radius:6px; text-align:center; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #1f6feb; color: white; padding: 7px; text-align: right; font-size: 11pt; }}
        td {{ padding: 6px 8px; border: 1px solid #ddd; font-size: 11pt; text-align: right; }}
        tr:nth-child(even) {{ background: #f5f5f5; }}
    </style>
    </head>
    <body>
    <div class="header">
        <h1>&#128203; تقرير الحضور اليومي</h1>
        <p>التاريخ: {date} &nbsp;&nbsp; طُبع في: {datetime.now().strftime('%H:%M')}</p>
    </div>
    <div class="stats">
        <b>الحاضرون: {present_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>الغائبون: {absent_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>الإجمالي: {len(employees_data)}</b>
    </div>
    <table>
        <tr><th>#</th><th>الكود</th><th>الاسم</th><th>الاسم الوظيفي</th><th>القسم</th><th>الحالة</th><th>وقت الحضور</th></tr>
        {rows_html}
    </table>
    </body></html>
    """
    return _print_html(parent, html, QPrinter.A4)


def print_monthly_report(parent, year, month, report_data):
    """طباعة التقرير الشهري"""
    months_ar = ['', 'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
    month_name = months_ar[month] if 1 <= month <= 12 else str(month)

    rows_html = ''
    for emp in report_data:
        rows_html += f"""
        <tr>
            <td>{emp['id']}</td>
            <td>{emp['code']}</td>
            <td>{emp['real_name']}</td>
            <td>{emp['job_name']}</td>
            <td>{emp['department']}</td>
            <td style="color:#28a745; font-weight:bold;">{emp['present_days'] or 0}</td>
            <td style="color:#dc3545; font-weight:bold;">{emp['absent_days'] or 0}</td>
        </tr>
        """

    html = f"""
    <html dir="rtl">
    <head><meta charset="utf-8">
    <style>
        body {{ font-family: Arial, Tahoma; font-size: 11pt; margin: 15px; }}
        .header {{ text-align: center; border-bottom: 3px solid #8250df; padding-bottom: 10px; margin-bottom: 14px; }}
        .header h1 {{ color: #8250df; font-size: 18pt; margin: 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #8250df; color: white; padding: 7px; text-align: right; }}
        td {{ padding: 6px 8px; border: 1px solid #ddd; text-align: right; }}
        tr:nth-child(even) {{ background: #f5f5f5; }}
    </style>
    </head>
    <body>
    <div class="header">
        <h1>&#128202; التقرير الشهري للحضور</h1>
        <p>شهر {month_name} {year}</p>
    </div>
    <table>
        <tr><th>#</th><th>الكود</th><th>الاسم</th><th>الوظيفة</th><th>القسم</th><th>أيام الحضور</th><th>أيام الغياب</th></tr>
        {rows_html}
    </table>
    </body></html>
    """
    return _print_html(parent, html, QPrinter.A4)


# ── Daily attendance grouped by department ───────────────────────────────────

DEPT_COLORS_PRINT = [
    '#1f6feb', '#238636', '#9e6a03', '#8250df',
    '#da3633', '#0ca4a5', '#e3b341', '#f78166',
]


def build_daily_attendance_html(date: str, dept_data: dict, summary: dict) -> str:
    """
    بناء HTML لتقرير الحضور اليومي مقسَّم حسب الأقسام.
    dept_data: OrderedDict  {dept_name: [emp_dict, ...]}
    summary:   dict  {present, absent, total_employees}
    إرجاع: html str
    """
    present_total = summary.get('present', 0)
    absent_total  = summary.get('absent', 0)
    total_emps    = summary.get('total_employees', 0)
    unrecorded    = total_emps - present_total - absent_total

    dept_sections = ''
    for idx, (dept_name, employees) in enumerate(dept_data.items()):
        color = DEPT_COLORS_PRINT[idx % len(DEPT_COLORS_PRINT)]

        dept_present = sum(1 for e in employees if e.get('status') == 'حاضر')
        dept_absent  = sum(1 for e in employees if e.get('status') == 'غائب')

        rows = ''
        for i, emp in enumerate(employees, 1):
            status  = emp.get('status') or 'غير مسجل'
            time_in = emp.get('time_in') or '—'
            if status == 'حاضر':
                status_style = 'color:#1a7f37; font-weight:bold;'
                row_bg       = '#f0fff4'
            elif status == 'غائب':
                status_style = 'color:#cf222e; font-weight:bold;'
                row_bg       = '#fff5f5'
            else:
                status_style = 'color:#7d6e00;'
                row_bg       = '#fffbea'

            rows += (
                f'<tr style="background:{row_bg}">'
                f'<td style="text-align:center;color:#666;">{i}</td>'
                f'<td><b>{emp.get("job_name","")}</b></td>'
                f'<td style="text-align:center;color:{color};font-weight:bold;">'
                f'{emp.get("code","")}</td>'
                f'<td style="{status_style}">{status}</td>'
                f'<td style="text-align:center;color:#555;">{time_in}</td>'
                f'</tr>'
            )

        dept_sections += (
            f'<div class="dept-block">'
            f'<div class="dept-header" style="background:{color};color:#fff;">'
            f'<span class="dept-name">&#127970; {dept_name}</span>'
            f'<span class="dept-stats">'
            f'&#9989; {dept_present} حاضر &nbsp;|&nbsp; '
            f'&#10060; {dept_absent} غائب &nbsp;|&nbsp; '
            f'&#128101; {len(employees)} موظف'
            f'</span></div>'
            f'<table><thead><tr>'
            f'<th style="width:4%">#</th>'
            f'<th>الاسم الوظيفي</th>'
            f'<th style="width:12%">الكود</th>'
            f'<th style="width:14%">الحالة</th>'
            f'<th style="width:14%">وقت الحضور</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>'
        )

    html = f"""<!DOCTYPE html>
<html dir="rtl">
<head>
<meta charset="utf-8">
<style>
  body {{font-family:Arial,Tahoma,sans-serif;font-size:11pt;color:#1a1a1a;margin:15px;background:#fff;}}
  .main-header {{text-align:center;border-bottom:4px solid #1f6feb;padding-bottom:12px;margin-bottom:16px;}}
  .main-header h1 {{color:#1f6feb;font-size:20pt;margin:0 0 6px;}}
  .main-header p  {{margin:3px;color:#555;font-size:11pt;}}
  .summary-bar {{background:#f0f4ff;border:1px solid #c8d8f8;border-radius:8px;
                 padding:10px 16px;margin-bottom:18px;text-align:center;}}
  .summary-bar span {{font-size:12pt;margin:0 16px;}}
  .summary-bar b    {{font-size:15pt;}}
  .dept-block  {{margin-bottom:20px;page-break-inside:avoid;}}
  .dept-header {{padding:8px 14px;border-radius:6px 6px 0 0;
                 display:flex;justify-content:space-between;font-size:13pt;}}
  .dept-name   {{font-weight:bold;}}
  .dept-stats  {{font-size:10.5pt;opacity:0.92;}}
  table  {{width:100%;border-collapse:collapse;border:1px solid #dde;}}
  thead tr {{background:#f4f7fb;}}
  th {{padding:7px 8px;text-align:right;font-size:10.5pt;color:#333;border-bottom:2px solid #c8d8f8;}}
  td {{padding:6px 8px;border-bottom:1px solid #eef;font-size:11pt;}}
  .footer {{text-align:center;color:#888;font-size:9pt;
            margin-top:20px;border-top:1px solid #ddd;padding-top:8px;}}
</style>
</head>
<body>
<div class="main-header">
  <h1>&#128203; تقرير الحضور اليومي</h1>
  <p>التاريخ: <b>{date}</b> &nbsp;&nbsp; وقت الطباعة: {datetime.now().strftime('%H:%M')}</p>
</div>
<div class="summary-bar">
  <span>&#9989; الحاضرون: <b style="color:#1a7f37">{present_total}</b></span>
  <span>&#10060; الغائبون: <b style="color:#cf222e">{absent_total}</b></span>
  <span>&#8987; غير مسجل: <b style="color:#7d6e00">{unrecorded}</b></span>
  <span>&#128101; الإجمالي: <b style="color:#1f6feb">{total_emps}</b></span>
</div>
{dept_sections}
<div class="footer">نظام إدارة الموظفين — طُبع في {datetime.now().strftime('%Y/%m/%d  %H:%M')}</div>
</body>
</html>"""
    return html


def print_daily_by_dept(parent, date: str, dept_data: dict, summary: dict) -> bool:
    """طباعة تقرير الحضور اليومي مقسَّم حسب الأقسام مباشرةً للطابعة"""
    html = build_daily_attendance_html(date, dept_data, summary)
    return _print_html(parent, html, QPrinter.A4)
