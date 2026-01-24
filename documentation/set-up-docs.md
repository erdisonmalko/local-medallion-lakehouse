# Local Spark + Airflow Development Environment

This repository contains a **local, Docker-based data platform** built around:

- Apache Spark (standalone cluster)
- Apache Airflow (orchestration)
- MinIO (S3-compatible object storage)
- Postgres (source database)
- Jupyter (exploration & prototyping)

This document is intentionally **practical**. It exists to explain how the system *actually works*, how to run it safely, and how to debug it when (not if) something breaks.

---

## 1. High-level Architecture

> **Rule #1:** Airflow submits Spark jobs — Spark executes them.

Execution flow:

```
Airflow DAG
  └── spark-submit (inside Airflow container)
        ↓
Spark Master (spark://spark:7077)
  └── Spark Workers
        ↓
MinIO (S3) / Postgres
```

Key implications:
- `spark-submit` **must exist inside the Airflow container**
- Spark does **not** run inside Airflow
- Python & Spark versions must match across all Spark-related containers

An architecture diagram is stored alongside this document for reference.

---

## 2. Repository Structure (Relevant Parts)

```
.
├── docker/
│   ├── spark/        # Spark image (master & worker)
│   └── airflow/      # Airflow image (includes Spark binaries)
├── spark-app/
│   ├── jobs/         # Spark jobs executed by Airflow
│   └── notebooks/    # Jupyter exploration
├── airflow/
│   └── dags/         # Airflow DAG definitions
├── documentation/    # This file + diagrams
├── docker-compose.yml
└── Makefile
```

---

## 3. When to Use `make` vs Docker Commands

### `make init`
Use **only when**:
- First-time setup
- Volumes were deleted
- You want to reseed Postgres / recreate MinIO buckets

This command:
- Starts all services
- Initializes databases
- Creates required buckets

⚠️ **Do not run on every start** — it is destructive.

---

### `make up`
Use for normal development startup.

Equivalent to:
```bash
docker compose up -d
```

---

### `make down`
Use when:
- You need a clean reset
- Dockerfiles changed
- State is corrupted

Equivalent to:
```bash
docker compose down -v
```

---

### When to Use Docker Directly

| Task | Command |
|----|----|
Debug container | `docker exec -it <container> bash` |
Check logs | `docker logs <container>` |
Rebuild images | `docker compose build --no-cache` |
Inspect FS | `ls /opt/spark` inside container |

---

## 4. First Run Checklist (Mandatory)

Before running any DAGs, verify:

- [ ] Docker is running
- [ ] `docker compose build` completes successfully
- [ ] Spark UI accessible at `http://localhost:8080`
- [ ] Airflow UI accessible at `http://localhost:8085`
- [ ] MinIO console accessible at `http://localhost:9001`
- [ ] `spark-submit` exists inside Airflow container

```bash
docker exec -it airflow which spark-submit
docker exec -it airflow spark-submit --version
```

If **any** of these fail, do not run DAGs yet.

---

## 5. Jupyter: Intended Use

Use Jupyter for:
- Data exploration
- Prototyping Spark logic
- Testing transformations interactively

Do **not** use Jupyter for:
- Scheduled jobs
- Production pipelines

Once logic is stable, move it to:
```
spark-app/jobs/
```
and execute via Airflow.

---

## 6. Troubleshooting Guide

### Error: `spark-submit: No such file or directory`

**Cause:** Spark is not installed in the Airflow image.

**Fix:**
- Install Spark inside `docker/airflow/Dockerfile`
- Rebuild image:
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

Verify:
```bash
docker exec -it airflow ls /opt/spark/bin
```

---

### Error: Python Version Mismatch

```
PySparkRuntimeError: [PYTHON_VERSION_MISMATCH]
```

**Cause:** Airflow Python ≠ Spark Python

**Fix:**
- Use the same Python version everywhere (3.12)
- Set explicitly:

```bash
PYSPARK_PYTHON=/usr/bin/python3.12
PYSPARK_DRIVER_PYTHON=/usr/bin/python3.12
```

Verify:
```bash
python3 --version
```

---

### Spark Master or Worker Not Starting

Check logs:
```bash
docker logs spark
docker logs spark-worker
```

Common causes:
- Java not installed or wrong version
- Volume mounting over `/opt/spark`

---

### Volume Shadowing (Critical)

❌ **Never do this**:
```yaml
- ./spark:/opt/spark
```

This overwrites Spark binaries.

✅ Safe mounts:
- `/opt/spark-app`
- `/opt/airflow/dags`

---

## 7. Rebuild vs Restart (Very Important)

### Restart only when:
- DAG code changes
- Python job logic changes

```bash
docker compose restart airflow
```

---

### Rebuild required when:
- Dockerfile changes
- Python / Java / Spark version changes

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

---

## 8. Known Issues (Stand-by)

These are known pain points to be improved:
- Simplifying Spark + Airflow image coupling
- Health checks for Spark readiness
- Dev vs Prod configuration split
- CI validation for image compatibility

---

