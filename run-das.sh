#!/bin/bash
set -e

IMAGE="ghcr.io/andreluis933/das-scraper:latest"
CONTAINER_NAME="das-scraper"
ENV_FILE="/das-scraper/.env"

echo "[$(date)] Atualizando imagem..."
docker pull "$IMAGE"

echo "[$(date)] Iniciando scraper..."
docker run --rm \
  --name "$CONTAINER_NAME" \
  --network whatsapp_network \
  --env-file "$ENV_FILE" \
  "$IMAGE"

echo "[$(date)] Scraper finalizado!"
docker image prune -f