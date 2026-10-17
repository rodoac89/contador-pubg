#!/bin/sh
set -eu

db_path="${SQLITE_PATH:-/data/db.sqlite3}"
db_dir=$(dirname "$db_path")

mkdir -p "$db_dir"
chown app:app "$db_dir"

if [ ! -e "$db_path" ] && [ -f /app/db.sqlite3 ] && [ "$db_path" != "/app/db.sqlite3" ]; then
    cp -a /app/db.sqlite3 "$db_path"
fi

chown -R app:app "$db_dir"

cd /app
runuser -u app -- /usr/local/bin/python manage.py migrate --noinput
exec runuser -u app -- /usr/local/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --no-control-socket \
    cpoints.wsgi:application
