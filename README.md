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

# Local Development Environment

This project uses Docker Compose to run:

- Apache Spark (Master + Worker)
- MinIO (S3-compatible storage)
- Postgres
- Jupyter/PySpark Notebook
- Airflow

---

## 🛠 Prerequisites

- WSL 2 (Ubuntu 22.04)
- Docker Desktop / Docker Engine
- Python 3.10+
- `bash`, `curl`, `jq` (optional for debugging)

---

## 🚀 Startup Workflow

### 1️⃣ Start all services
```bash
./scripts/run_local.sh up
```

### Initialize environment (once)
```bash
./scripts/run_local.sh init
```

- Creates MinIO buckets: bronze, silver, gold, logs
- Seeds Postgres database

### Stop all services
```bash
./scripts/run_local.sh down
```