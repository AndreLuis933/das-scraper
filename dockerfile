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
FROM public.ecr.aws/lambda/python:3.12

WORKDIR /app

# Instalar dependências de runtime do Camoufox
RUN microdnf install -y \
    gtk3 \
    alsa-lib \
    libX11-xcb \
    && microdnf clean all

# Copiar dependências Python para o diretório padrão do Lambda
COPY --from=builder /app/.venv/lib/python3.12/site-packages/ ${LAMBDA_TASK_ROOT}/

# Copiar código fonte para o diretório do Lambda
COPY --from=builder /app/src/ ${LAMBDA_TASK_ROOT}/

# Copiar o cache do Camoufox (navegador baixado)
COPY --from=builder /root/.cache/camoufox /root/.cache/camoufox

CMD ["main.handler"]