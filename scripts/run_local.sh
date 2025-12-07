#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log() {
  echo -e "${CYAN}▶ $1${NC}"
}

error() {
  echo -e "${RED}✖ $1${NC}"
}

success() {
  echo -e "${GREEN}✔ $1${NC}"
}

wait_for_service() {
  local name=$1
  local host=$2
  local port=$3

  log "Waiting for $name ($host:$port)..."
  for i in {1..20}; do
    if nc -z "$host" "$port"; then
      success "$name is ready!"
      return
    fi
    sleep 1
  done
  error "$name did NOT become ready!"
  exit 1
}

case "${1:-}" in
  up)
    log "Starting stack..."
    docker compose up -d
    success "Services started."
    ;;

  down)
    log "Stopping stack..."
    docker compose down -v
    success "Services stopped."
    ;;

  init)
    log "Starting stack for initialization..."
    docker compose up -d

    wait_for_service "Postgres" "localhost" "5432"
    wait_for_service "MinIO" "localhost" "9000"

    log "Initializing MinIO buckets..."
    ./init/init_minio.sh

    if [[ -f "init/init_postgres.sql" ]]; then
      log "Running Postgres seed file..."
      docker exec -i postgres psql -U admin -d sourcedb < init/init_postgres.sql
      success "Postgres seeded."
    else
      error "init_postgres.sql NOT found — skipping"
    fi

    success "Initialization complete."
    ;;

  *)
    echo "Usage: ./scripts/run_local.sh [init|up|down]"
    exit 1
    ;;
esac
