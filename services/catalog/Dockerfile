FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md /app/
COPY libs/cloudops-core /app/libs/cloudops-core
COPY services/catalog /app/services/catalog
RUN uv sync --frozen --package catalog
ENV PATH=/app/.venv/bin:$PATH
WORKDIR /app/services/catalog
CMD ["sh", "-c", "alembic upgrade head && python -m catalog.main"]
