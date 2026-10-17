FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False \
    SQLITE_PATH=/data/db.sqlite3

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system app \
    && useradd --system --gid app --no-create-home --home-dir /app --shell /bin/sh app \
    && mkdir -p /data \
    && chown app:app /data

COPY --chown=app:app backend/ ./
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh \
    && chmod 755 /app/docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD /usr/local/bin/python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/', timeout=4)"

ENTRYPOINT ["/app/docker-entrypoint.sh"]
