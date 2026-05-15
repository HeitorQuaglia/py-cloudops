FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md /app/
COPY libs/cloudops-core /app/libs/cloudops-core
COPY services/audit /app/services/audit
RUN uv sync --frozen --package audit
ENV PATH=/app/.venv/bin:$PATH
WORKDIR /app/services/audit
CMD ["python", "-m", "audit.main"]
