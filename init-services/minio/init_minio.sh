#!/usr/bin/env bash
set -euo pipefail

# ---------- CONFIG ----------
MC_IMAGE=minio/mc
NETWORK=end-to-end-data-pipeline_default
ENDPOINT=http://minio:9000
USER=minio
PASSWORD=minio123
CONFIG_VOLUME=mc_config  # persistent volume for mc config

# Buckets
BUCKETS=(bronze silver gold logs control)

# Folders / Keys inside buckets
FOLDERS=(
  "bronze/customers"
  "silver/customers"
  "silver/bad_records"
  "gold/customers_summary"
  "logs/dq_violations"
  "logs/ingest_logs"
  "control/ingest_control"
)

PLACEHOLDER=".gitkeep"
# ----------------------------

# Create a Docker volume to persist mc config if it doesn't exist
if ! docker volume ls | grep -q "^${CONFIG_VOLUME}$"; then
  echo "Creating Docker volume for mc config: $CONFIG_VOLUME"
  docker volume create $CONFIG_VOLUME
fi

echo "Setting MinIO alias..."
docker run --rm -v $CONFIG_VOLUME:/root/.mc --network $NETWORK $MC_IMAGE alias set local $ENDPOINT $USER $PASSWORD

echo "Creating buckets..."
for bucket in "${BUCKETS[@]}"; do
  docker run --rm -v $CONFIG_VOLUME:/root/.mc --network $NETWORK $MC_IMAGE mb -p local/$bucket || true
done

echo "Creating folder structure with placeholders..."
for folder in "${FOLDERS[@]}"; do
  # Add a placeholder file to force folder to exist
  docker run --rm -v $CONFIG_VOLUME:/root/.mc --network $NETWORK $MC_IMAGE pipe local/$folder/$PLACEHOLDER <<< ""
done

echo "Listing buckets and folders..."
docker run --rm -v $CONFIG_VOLUME:/root/.mc --network $NETWORK $MC_IMAGE ls local

