#!/usr/bin/env bash
# Create buckets in MinIO using mc (MinIO client). This script runs mc inside a temporary container.

MC_ALIAS=minio_local
MC=minio/mc

# Use host.docker.internal on Mac/Windows, 127.0.0.1 on Linux may require tweaks.
docker run --rm --network host ${MC} alias set ${MC_ALIAS} http://127.0.0.1:9000 minio minio123 || true
docker run --rm --network host ${MC} mb ${MC_ALIAS}/bronze || true
docker run --rm --network host ${MC} mb ${MC_ALIAS}/silver || true
docker run --rm --network host ${MC} mb ${MC_ALIAS}/gold || true
docker run --rm --network host ${MC} mb ${MC_ALIAS}/logs || true
docker run --rm --network host ${MC} ls ${MC_ALIAS} || true
echo "MinIO buckets created: bronze, silver, gold, logs"
