FROM ghcr.io/astral-sh/uv:0.9.17-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy \
  UV_PYTHON_PREFERENCE=only-managed \
  UV_NO_DEV=1 \
  UV_PYTHON_INSTALL_DIR=/python

RUN apt-get update && apt-get install -y \
    g++ \
    gcc \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

RUN uv python install 3.12

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --frozen --no-install-project ;


RUN .venv/bin/python -m camoufox fetch

RUN .venv/bin/python -c "from pandascamoufox import CamoufoxDf"

COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock

COPY src /app/src
COPY template /app/template

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen

FROM debian:trixie-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8

RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libasound2 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r python && useradd -r -g python python

COPY --from=builder /python /python
COPY --from=builder --chown=python:python /root/.cache/camoufox /home/python/.cache/camoufox
COPY --from=builder --chown=python:python /app/.venv /app/.venv
COPY --from=builder --chown=python:python /app/src /app/src
COPY --from=builder --chown=python:python /app/template /app/template

ENV PATH="/app/.venv/bin:${PATH}"

USER python
WORKDIR /app

CMD ["python", "src/main.py"]