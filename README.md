# Databricks Simulator — Full Starter Project

This project simulates a Databricks-like medallion pipeline (bronze → silver → gold) locally using Docker:
Spark (standalone) + Delta Lake OSS + MinIO (S3) + Postgres (source) + Airflow + Jupyter.

## Quickstart
1. Install Docker and Docker Compose (v2).
2. Unzip into a folder and run:
   ```bash
   docker compose up -d
   ```
3. Initialize infra:
   ```bash
   ./scripts/run_local.sh init
   ```
4. Access services:
   - Jupyter: http://localhost:8888
   - Airflow: http://localhost:8085 (admin/admin)
   - MinIO Console: http://localhost:9001 (minio/minio123)
   - Spark UI: http://localhost:8080
   - Postgres: localhost:5432 (admin/admin)

See `notebooks/` for the PySpark scripts (can be run via `spark-submit` or inside Jupyter).
