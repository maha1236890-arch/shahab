# ================================================================
#  Docker image لنظام الحضور والغياب
#  يعمل على: Windows / macOS / Linux / أي خادم
#  المتصفح: http://localhost:5000
# ================================================================

FROM python:3.11-slim

# تثبيت المتطلبات الضرورية لـ reportlab (معالجة الخطوط/PDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libfreetype6 \
        libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات أولاً (للاستفادة من cache)
COPY requirements.txt .

# تثبيت مكتبات Python (بدون PyQt5)
RUN pip install --no-cache-dir \
        flask>=3.0.0 \
        bcrypt>=3.2 \
        openpyxl>=3.1.0 \
        "reportlab>=3.6.0" \
        arabic-reshaper>=3.0.0 \
        python-bidi>=0.4.2

# نسخ كود التطبيق
COPY app.py database.py export_utils.py ./
COPY templates/ templates/
COPY static/    static/

# مجلد بيانات قابل للتعديل (يُربط بحجم خارجي)
VOLUME ["/app/data"]

# متغيرات البيئة
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/app/data/attendance.db

# المنفذ
EXPOSE 5000

# نقطة الدخول
CMD ["python", "app.py", "--docker"]
