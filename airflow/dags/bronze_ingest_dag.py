from datetime import datetime, timedelta
import json
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator # type: ignore

SPARK_REST_URL = "http://spark:6066/v1/submissions/create"
SPARK_STATUS_URL = "http://spark:6066/v1/submissions/status"
APP_RESOURCE = "file:/opt/spark-app/notebooks/00_bronze_ingest.py"

def submit_spark_job(**context):
    """Submit the Spark job via REST API."""
    payload = {
        "action": "CreateSubmissionRequest",
        "appResource": APP_RESOURCE,
        "clientSparkVersion": "3.5.1",
        "appArgs": [],
        "sparkProperties": {
            "spark.master": "spark://spark:7077",
            "spark.submit.deployMode": "cluster",
            "spark.driver.supervise": "false",
        }
    }

    response = requests.post(
        SPARK_REST_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        raise Exception(f"Failed to submit job: {response.text}")

    submission_id = response.json().get("submissionId")
    if not submission_id:
        raise Exception("Spark did not return submissionId")

    context['ti'].xcom_push(key="submission_id", value=submission_id)
    return submission_id


def poll_spark_status(**context):
    """Poll Spark until job finishes."""
    submission_id = context['ti'].xcom_pull(key="submission_id")
    if not submission_id:
        raise Exception("No submission_id found in XCom")

    print(f"Checking status for Spark job: {submission_id}")

    status_response = requests.get(f"{SPARK_STATUS_URL}/{submission_id}")
    status_json = status_response.json()

    driver_state = status_json.get("driverState")

    print("Spark driver state:", driver_state)

    # treat Succeeded as final success
    if driver_state == "FINISHED" or driver_state == "SUCCEEDED":
        return "Job Succeeded"

    if driver_state in ("ERROR", "FAILED", "KILLED"):
        raise Exception(f"Spark job failed: {driver_state}")

    # Otherwise still running
    raise Exception(f"Spark still running or unknown state: {driver_state}")


default_args = {
    "owner": "airflow",
    "retry_delay": timedelta(seconds=30),
    "retries": 3,
}

with DAG(
    "bronze_ingest_pipeline",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval="@once",
    catchup=False
) as dag:

    submit_job = PythonOperator(
        task_id="submit_spark_job",
        python_callable=submit_spark_job
    )

    poll_job = PythonOperator(
        task_id="poll_spark_job",
        python_callable=poll_spark_status
    )

    submit_job >> poll_job
