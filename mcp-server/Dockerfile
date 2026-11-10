FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt


FROM base AS test

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY pyproject.toml .
COPY src ./src
COPY tests ./tests

CMD ["sh", "-c", "ruff check . && ruff format --check . && ty check && pytest"]


FROM base AS runtime

COPY src ./src

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["python", "-m", "catalog_mcp.main"]
