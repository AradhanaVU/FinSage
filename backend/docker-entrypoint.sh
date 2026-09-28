#!/bin/sh
set -e
alembic upgrade head
# Railway injects PORT; Docker Compose defaults to 8000
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
