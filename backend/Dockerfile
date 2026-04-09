FROM python:3.12-slim AS base
WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip setuptools && pip install --no-cache-dir -e .

COPY alembic.ini .
COPY alembic/ alembic/
COPY app/ app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
