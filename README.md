# Databricks Simulator — Local Medallion Pipeline (bronze → silver → gold)

A self-contained starter project that simulates a Databricks-style medallion pipeline locally using Docker:
Spark (standalone) + Delta Lake OSS + MinIO (S3) + Postgres (source) + Airflow + Jupyter.

## Quickstart

Prerequisites
- Docker & Docker Compose (v2)
- Python 3.10+ (optional for local scripts)
- bash, curl, jq (optional)

Start services
- Using bundled helper script (path may be `./scripts/run_local.sh` or `./scripts/local/run_local.sh`):
```bash
./scripts/run_local.sh up
# or
./scripts/local/run_local.sh up
# or directly
docker compose up -d
```

Initialize infra (create MinIO buckets, seed Postgres)
```bash
./scripts/run_local.sh init
# or
./scripts/local/run_local.sh init
```

Stop and remove
```bash
./scripts/run_local.sh down
# or
./scripts/local/run_local.sh down
```

## Services & default access

- Jupyter: http://localhost:8888 — token: local
- Airflow: http://localhost:8085 — user: admin / pass: admin
- MinIO Console: http://localhost:9001 — user: minio / pass: minio123
- Spark UI: http://localhost:8080
- Postgres: localhost:5432 — user: admin / pass: admin, DB: sourcedb

## What this repo contains (important files)

- Orchestration
  - docker-compose.yml
  - scripts/run_local.sh (or scripts/local/run_local.sh) — helper to manage lifecycle
- Init / seed
  - init-services/minio/init_minio.sh
  - init-services/postgres/init_postgres.sql
  - init-services/postgres/sample_data.py
- Spark app
  - spark-app/notebooks/00_bronze_ingest.py
  - spark-app/notebooks/01_silver_transform.py
  - spark-app/notebooks/02_gold_aggregate.py
  - spark-app/helpers/spark_session.py — builds Spark session & S3/MinIO config
  - spark-app/jars/ — place extra JDBC/Delta jars if required
- Airflow
  - airflow/dags/bronze_silver_gold_pipeline.py — orchestrates the three steps via spark-submit

## Running the pipeline

1. Ensure services are up and infra initialized.
2. Run via Airflow (web UI) using the `bronze_silver_gold_pipeline` DAG, or run tasks manually.

Example: run bronze ingest from host (executes spark-submit inside spark container)
```bash
docker exec -it spark /opt/spark/bin/spark-submit \
  --master spark://spark:7077 \
  --packages "io.delta:delta-spark_2.12:3.1.0,org.postgresql:postgresql:42.7.3,org.apache.hadoop:hadoop-aws:3.3.4" \
  /opt/spark-app/notebooks/00_bronze_ingest.py
```

## Configuration pointers

- S3/MinIO credentials and endpoints are read in spark-app/helpers/spark_session.py (environment-driven).
- JDBC connection and credentials are configured in the notebooks; update as needed.
- Add additional jars/drivers to spark-app/jars and mount into the spark container or add via --jars/--packages.

## Troubleshooting

- View logs: docker compose logs -f
- Ensure MinIO & Postgres are reachable before running Spark jobs (init scripts wait for readiness).
- If Delta / JDBC drivers are missing, add appropriate jars to spark-app/jars or include via spark-submit packages/--jars.

## Project layout (short)
- docker-compose.yml
- scripts/ (lifecycle helpers)
- init-services/ (minio/postgres init scripts)
- spark-app/ (notebooks, helpers, jars)
- airflow/ (DAGs, configs)
- Makefile (optional convenience targets)