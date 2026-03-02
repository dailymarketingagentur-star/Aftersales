#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! python -c "import socket; s=socket.create_connection(('${POSTGRES_HOST:-postgres}', ${POSTGRES_PORT:-5432}), timeout=1)" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Only run migrations from the backend container (not celery workers)
if echo "$@" | grep -q "manage.py"; then
    echo "Running migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput 2>/dev/null || true
else
    echo "Skipping migrations (worker process)."
fi

exec "$@"
