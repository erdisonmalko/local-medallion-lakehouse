from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'erdison',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id='medallion_dag',
    default_args=default_args,
    description='Bronze->Silver->Gold pipeline',
    schedule_interval=None,
    start_date=datetime(2025,1,1),
    catchup=False
) as dag:

    t1 = BashOperator(
        task_id='bronze_ingest',
        bash_command='spark-submit /opt/spark-app/notebooks/00_bronze_ingest.py || exit 1'
    )

    t2 = BashOperator(
        task_id='silver_transform',
        bash_command='spark-submit /opt/spark-app/notebooks/10_silver_transform.py || exit 1'
    )

    t3 = BashOperator(
        task_id='gold_aggregate',
        bash_command='spark-submit /opt/spark-app/notebooks/20_gold_aggregate.py || exit 1'
    )

    t1 >> t2 >> t3
