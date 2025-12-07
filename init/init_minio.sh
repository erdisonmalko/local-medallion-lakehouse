#!/usr/bin/env bash
set -euo pipefail

MC_IMAGE=minio/mc
NETWORK=end-to-end-data-pipeline_default
ALIAS=minio_local
ENDPOINT=http://minio:9000

echo "Setting alias..."
docker run --rm --network $NETWORK $MC_IMAGE alias set $ALIAS $ENDPOINT minio minio123

echo "Creating buckets..."
for bucket in bronze silver gold logs; do
  docker run --rm --network $NETWORK $MC_IMAGE mb $ALIAS/$bucket || true
done

echo "Listing buckets..."
docker run --rm --network $NETWORK $MC_IMAGE ls $ALIAS
