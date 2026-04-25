FROM python:3.12-slim

WORKDIR /app

# System dependencies for psycopg2 and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    gzip \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY crm_backend/requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# Application code
COPY crm_backend/ .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
