FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md /app/
COPY libs/cloudops-core /app/libs/cloudops-core
COPY services/provisioning /app/services/provisioning
RUN uv sync --frozen --package provisioning
ENV PATH=/app/.venv/bin:$PATH
WORKDIR /app/services/provisioning
CMD ["sh", "-c", "alembic upgrade head && python -m provisioning.main"]
