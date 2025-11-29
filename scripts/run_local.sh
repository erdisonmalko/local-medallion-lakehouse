#!/usr/bin/env bash
set -e
case "$1" in
  init)
    echo 'Waiting for services to be healthy...'
    sleep 5
    echo 'Initializing MinIO buckets...'
    ./init/init_minio.sh
    echo 'Seeding Postgres...'
    docker exec -i postgres psql -U admin -d sourcedb < init/init_postgres.sql
    echo 'Init complete.'
    ;;
  up)
    docker compose up -d
    ;;
  down)
    docker compose down
    ;;
  *)
    echo 'Usage: ./scripts/run_local.sh [init|up|down]'
    exit 1
    ;;
esac
