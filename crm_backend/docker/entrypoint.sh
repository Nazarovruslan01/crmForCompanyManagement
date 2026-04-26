#!/bin/sh
set -e

# Docker entrypoint script for Django + Celery

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h db -p 5432 -U crm_user > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL is ready"

# Run Django migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files (only for web, but harmless for worker/beat)
if [ "$1" = "daphne" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput --clear
fi

echo "Starting $@"
exec "$@"
