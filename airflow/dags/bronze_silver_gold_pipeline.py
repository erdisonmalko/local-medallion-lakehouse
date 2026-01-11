from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator  # type: ignore

SPARK_SUBMIT = "/opt/spark/bin/spark-submit"
SPARK_MASTER = "spark://spark:7077"
SPARK_PACKAGES = (
    "io.delta:delta-spark_2.12:3.1.0,"
    "org.postgresql:postgresql:42.7.3,"
    "org.apache.hadoop:hadoop-aws:3.3.4"
)
ROOT = "/opt/spark-app/notebooks/"


STEPS = [
    "00_bronze_ingest.py",
    "01_silver_transform.py",
    "02_gold_aggregate.py",
]

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(seconds=20)
}

with DAG(
    "bronze_silver_gold_pipeline_spark_submit",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@once",
    catchup=False,
    default_args=default_args
) as dag:

    previous_task = None

    for job in STEPS:
        task = BashOperator(
    task_id=f"run_{job.split('.')[0]}",
    bash_command=(
        f"{SPARK_SUBMIT} "
        f"--master {SPARK_MASTER} "
        f"--packages {SPARK_PACKAGES} "
        f"{ROOT}{job}"
    ),
)

        if previous_task:
            previous_task >> task

        previous_task = task
