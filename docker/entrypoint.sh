#!/usr/bin/env sh
set -e

until python manage.py migrate --noinput; do
  echo "Database is unavailable, retrying in 2 seconds..."
  sleep 2
done

exec "$@"
