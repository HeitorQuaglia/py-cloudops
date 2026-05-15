FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app

COPY pyproject.toml uv.lock README.md /app/
COPY libs/cloudops-core /app/libs/cloudops-core
COPY services/api-ingress /app/services/api-ingress

RUN uv sync --frozen --package api-ingress

ENV PATH=/app/.venv/bin:$PATH
WORKDIR /app/services/api-ingress
CMD ["uvicorn", "api_ingress.main:app", "--host", "0.0.0.0", "--port", "8000"]
