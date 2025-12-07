from datetime import datetime, timedelta
import json
import requests
import time
from airflow import DAG
from airflow.operators.python import PythonOperator # type: ignore

SPARK_REST_CREATE = "http://spark:6066/v1/submissions/create"
SPARK_REST_STATUS = "http://spark:6066/v1/submissions/status"
ROOT = "/opt/spark-app/notebooks/"
# steps or files defined
STEPS = [
    "00_bronze_ingest.py",
    "01_silver_transform.py",
    "02_gold_aggregate.py",
]


def submit_job(job_file, **context):
    payload = { 
        "action": "CreateSubmissionRequest", 
        "appResource": f"{ROOT}{job_file}", 
        "clientSparkVersion": "3.5.1", 
        "mainClass": "org.apache.spark.deploy.PythonRunner", 
        "environmentVariables": { "PYSPARK_DRIVER_PYTHON": "python3", "PYSPARK_PYTHON": "python3" },
        "sparkProperties": { 
            "spark.app.name": "bronze_ingest", 
            "spark.master": "spark://spark:7077", 
            "spark.submit.deployMode": "cluster", 
            "spark.driver.supervise": "false", 
            "spark.jars": "", 
            "spark.executor.memory": "1g", 
            "spark.driver.memory": "1g"
            },

        "appArgs":
            [f"{ROOT}{job_file}"] 
        }

    response = requests.post(
        SPARK_REST_CREATE,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )

    if response.status_code != 200:
        raise Exception(f"Spark submit failed: {response.text}")

    submission_id = response.json().get("submissionId")
    if not submission_id:
        raise Exception("No submissionId returned")

    context['ti'].xcom_push(key=f"{job_file}_submission", value=submission_id)
    return submission_id



def wait_for_job(job_file, **context):
    submission_id = context['ti'].xcom_pull(key=f"{job_file}_submission")

    for _ in range(100):
        resp = requests.get(f"{SPARK_REST_STATUS}/{submission_id}")
        data = resp.json()
        state = data.get("driverState")

        if state in ("FINISHED", "SUCCEEDED"):
            print(f"{job_file} completed successfully")
            return

        if state in ("FAILED", "ERROR", "KILLED"):
            raise Exception(f"{job_file} failed with state: {state}")

        time.sleep(5)

    raise TimeoutError(f"{job_file} did not finish in time")


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(seconds=20)
}

with DAG(
    "bronze_silver_gold_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@once",
    catchup=False,
    default_args=default_args
) as dag:

    tasks = []

    for job in STEPS:
        submit = PythonOperator(
            task_id=f"submit_{job}",
            python_callable=submit_job,
            op_kwargs={"job_file": job}
        )

        wait = PythonOperator(
            task_id=f"wait_{job}",
            python_callable=wait_for_job,
            op_kwargs={"job_file": job}
        )

        submit >> wait
        tasks.append(wait)

    # Force linear order bronze -> silver -> gold
    tasks[0] >> tasks[1] >> tasks[2]
