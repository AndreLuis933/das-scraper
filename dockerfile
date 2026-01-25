FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependências de compilação
RUN apt-get update && apt-get install -y \
    g++ \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock

RUN uv sync --locked --no-dev --compile-bytecode

# Baixar o navegador Camoufox no builder
RUN .venv/bin/python -m camoufox fetch

COPY src /app/src

# Compilar pandascamoufox durante o build
RUN .venv/bin/python src/main.py --no-run

# Estágio final - sem ferramentas de compilação
FROM python:3.12-slim

WORKDIR /app

# Instalar dependências de runtime do Camoufox
RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libasound2 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependências Python para o diretório padrão do Lambda
COPY --from=builder /app/.venv /app/.venv

# Copiar código fonte para o diretório do Lambda
COPY --from=builder /app/src /app/src

# Copiar o cache do Camoufox (navegador baixado)
COPY --from=builder /root/.cache/camoufox /root/.cache/camoufox

CMD [".venv/bin/python", "src/main.py"]