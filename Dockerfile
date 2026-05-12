FROM python:3.12-slim

# تثبيت أدوات النظام الضرورية لمكتبات الصوت
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ requirements أولاً للاستفادة من Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY configs/ ./configs/

# مجلد البيانات (يُربط كـ volume عند التشغيل)
RUN mkdir -p /data
ENV CIE_DATA_ROOT=/data

# منفذ FastAPI
EXPOSE 8000

# تشغيل
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
