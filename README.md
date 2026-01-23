# Databricks Simulator — Local Medallion Data Platform

This repository provides a **local, production-inspired data platform** that mirrors common Databricks architectures using only open-source components and Docker.

It is designed for:

* Learning and experimenting with **medallion architecture** (Bronze → Silver → Gold)
* Developing **Spark + Delta Lake pipelines** locally
* Practicing **Airflow orchestration** of distributed Spark jobs
* Validating data engineering patterns before deploying to managed platforms (Databricks, EMR, Spark on Kubernetes)

The stack runs entirely on your machine but follows **real-world separation of concerns** between orchestration, compute, storage, and analytics.

---

## High-level architecture

The platform is composed of the following services:

* **Apache Spark (Standalone cluster)**
  Distributed compute engine used for all data processing.
* **Delta Lake (OSS)**
  Storage layer providing ACID tables and versioned datasets.
* **MinIO (S3-compatible storage)**
  Object storage backend for Bronze/Silver/Gold datasets.
* **PostgreSQL**
  Source system simulating an operational database.
* **Apache Airflow**
  Orchestration layer responsible for scheduling and dependency management.
* **Jupyter Notebook**
  Interactive environment for exploration, debugging, and development.

Spark jobs are executed in **cluster mode**, with Airflow acting strictly as an orchestrator — not as a Spark driver.

---

## Medallion pipeline concept

This repository follows the **Databricks medallion pattern**:

* **Bronze**
  Raw ingestion from Postgres into Delta tables (append-only, minimal transformation).
* **Silver**
  Cleaned, validated, and standardized datasets.
* **Gold**
  Aggregated, analytics-ready tables for downstream consumers.

Each layer is implemented as a separate Spark job and can be executed independently or orchestrated end-to-end.

---

## What this repo is (and is not)

**This repo is:**

* A realistic local simulation of a modern data platform
* A safe place to experiment with Spark, Delta Lake, and Airflow
* A reference for structuring Spark jobs and orchestration code
* A stepping stone toward Databricks / cloud deployments

**This repo is not:**

* A Databricks replacement
* A single-node Spark playground
* An Airflow tutorial repo

---

## Repository structure (important)

```
.
├── docker-compose.yml        # Full local platform definition
├── docker/                  # Custom images (Spark, Airflow, spark-submit)
├── scripts/                 # Lifecycle helpers (up / down / init)
├── init-services/            # Postgres + MinIO initialization
│   ├── postgres/
│   └── minio/
├── spark-app/
│   ├── notebooks/            # Bronze / Silver / Gold Spark jobs
│   ├── helpers/              # Spark session & shared config
│   ├── jars/                 # Optional JDBC / Spark dependencies
│   └── jobs/                 # spark-submit–ready scripts
├── airflow/
│   └── dags/                 # Airflow DAGs orchestrating Spark jobs
├── documentation/            # Detailed docs & diagrams (deep dives)
└── README.md                 # This file (high-level overview)
```

---

## Service access (default)

| Service       | URL / Access                                                      |
| ------------- | ----------------------------------------------------------------- |
| Airflow       | [http://localhost:8085](http://localhost:8085) (admin / admin)    |
| Spark UI      | [http://localhost:8080](http://localhost:8080)                    |
| Jupyter       | [http://localhost:8888](http://localhost:8888) (token: `local`)   |
| MinIO Console | [http://localhost:9001](http://localhost:9001) (minio / minio123) |
| Postgres      | localhost:5432 (admin / admin, DB: sourcedb)                      |

---


## Execution Model: The "Remote Submitter" Pattern

This platform uses **Apache Airflow** as the "Brain" and **Spark Standalone** as the "Muscle."

* **The Submitter (Airflow):** When a DAG task runs, Airflow executes a `spark-submit` command via the `BashOperator`.
* **The Driver (Inside Airflow):** The Spark Driver starts **inside the Airflow worker container**. It parses your Python script, builds the DAG of Spark stages, and communicates with the Spark Master.
* **The Executors (Spark Workers):** The Spark Master allocates resources on the `spark-worker` containers. These workers execute the actual data processing tasks and write directly to **MinIO (S3)**.

> **Note on Versioning:** To avoid `PYTHON_VERSION_MISMATCH` errors, the Python version in the Airflow container and the Spark Worker containers are strictly pinned to **Python 3.9**.

---

## Medallion Pipeline Section

### 🥉 Bronze: Raw Ingestion

* **Source:** PostgreSQL (`customers` table)
* **Action:** JDBC Read via Spark
* **Format:** Delta Lake (Append-only)
* **Path:** `s3a://bronze/customers/`

### 🥈 Silver: Cleanse & Conform

* **Action:** Schema enforcement, deduplication, and null handling.
* **Format:** Delta Lake (Overwrite/Upsert)
* **Path:** `s3a://silver/customers_cleansed/`

### 🥇 Gold: Business Aggregates

* **Action:** Window functions, joins, and aggregations (e.g., `customers_by_country`).
* **Format:** Delta Lake
* **Path:** `s3a://gold/total_usage_stats/`

---


## Development workflow

Typical usage looks like:

1. Explore or prototype logic in **Jupyter**
2. Convert logic into **Spark jobs** under `spark-app/`
3. Orchestrate jobs using **Airflow DAGs**
4. Validate outputs in **MinIO (Delta tables)**
5. Iterate safely without cloud costs

---

## Configuration philosophy

* Infrastructure is managed via **Docker Compose**
* Runtime behavior is driven by **environment variables**
* Spark configuration is centralized in shared helpers
* Storage is treated as external and persistent

Detailed configuration instructions live in the `documentation/` directory.

---

## Observability & debugging

* Spark execution: Spark UI (jobs, stages, executors)
* Orchestration state: Airflow UI
* Logs: `docker compose logs` or per-container logs
* Data inspection: MinIO Console or Spark SQL

---

## Why this setup matters

This repository intentionally avoids shortcuts (like local Spark sessions inside Airflow) in favor of patterns that:

* Scale to real clusters
* Translate directly to Databricks / EMR / Kubernetes
* Encourage clean separation between orchestration and compute
* Reduce “works locally, fails in prod” issues

---

## Next steps

* Read the documents in `documentation/` for deep dives
* Inspect the Airflow DAGs to understand orchestration patterns
* Extend the pipeline with new Silver or Gold transformations
* Replace MinIO with real S3 or migrate Spark to Kubernetes when ready

---
