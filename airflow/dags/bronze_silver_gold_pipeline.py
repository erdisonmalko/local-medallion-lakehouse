"""
DAG: bronze_silver_gold_pipeline_spark_submit

This DAG orchestrates a local, Databricks-style Medallion Lakehouse pipeline
(Bronze → Silver → Gold) using Apache Spark submitted from Airflow.

Key architectural idea:
- Airflow acts as the Spark *client* (driver runs inside the Airflow container)
- Spark workers execute the actual computation
- This mirrors how spark-submit works in real production environments
  where orchestration and compute are separated
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator  # type: ignore

# -------------------------------------------------------------------
# Spark submission configuration
# -------------------------------------------------------------------

# Path to spark-submit installed inside the Airflow image
SPARK_SUBMIT = "/opt/spark/bin/spark-submit"

# Spark Standalone cluster master URL
# Airflow connects to the Spark cluster as a client
SPARK_MASTER = "spark://spark:7077"

# External Spark dependencies resolved at submission time
# This avoids baking connectors directly into the Spark image
SPARK_PACKAGES = (
    "io.delta:delta-spark_2.12:3.1.0,"        # Delta Lake support
    "org.postgresql:postgresql:42.7.3,"       # JDBC source / sink
    "org.apache.hadoop:hadoop-aws:3.3.4"      # S3-compatible storage (e.g. MinIO)
)

# Root directory where Spark jobs are mounted inside containers
ROOT = "/opt/spark-app/notebooks/"

# -------------------------------------------------------------------
# Medallion pipeline steps
# Each script represents a logical layer in the lakehouse
# -------------------------------------------------------------------

STEPS = [
    "00_bronze_ingest.py",     # Raw ingestion (append-only, minimal schema enforcement)
    "01_silver_transform.py",  # Cleansing, normalization, business rules
    "02_gold_aggregate.py",    # Aggregations and analytics-ready outputs
]

# -------------------------------------------------------------------
# Default DAG arguments
# -------------------------------------------------------------------

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(seconds=20),
}

# -------------------------------------------------------------------
# DAG definition
# -------------------------------------------------------------------

with DAG(
    dag_id="bronze_silver_gold_pipeline_spark_submit",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@once",
    catchup=False,
    default_args=default_args,
    tags=["spark", "lakehouse", "medallion"],
) as dag:

    """
    Execution model:

    - Each task uses spark-submit in *client mode*
    - The Spark driver runs inside the Airflow container
    - Executors run on Spark worker nodes
    - Tasks are chained to enforce Bronze → Silver → Gold order

    This setup intentionally avoids running the driver on Spark workers,
    which simplifies networking, logging, and dependency management.
    """

    previous_task = None

    for job in STEPS:
        task = BashOperator(
            task_id=f"run_{job.split('.')[0]}",
            bash_command=(
                # Submit Spark job from Airflow (client mode)
                f"{SPARK_SUBMIT} "
                f"--master {SPARK_MASTER} "

                # Explicit Python configuration to avoid version mismatches
                # Driver = Airflow container
                # Workers = Spark containers
                f"--conf spark.pyspark.python=python3 "
                f"--conf spark.pyspark.driver.python=python3 "

                # Resolve external dependencies dynamically
                f"--packages {SPARK_PACKAGES} "

                # Actual Spark application
                f"{ROOT}{job}"
            ),
        )

        # Enforce sequential execution between medallion layers
        if previous_task:
            previous_task >> task

        previous_task = task
