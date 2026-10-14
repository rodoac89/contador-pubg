FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system app \
    && useradd --system --gid app app

COPY --chown=app:app backend/ ./

USER app

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "cpoints.wsgi:application"]