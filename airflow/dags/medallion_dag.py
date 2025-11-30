from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator # type: ignore

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

    ingest = BashOperator(
        task_id="bronze_ingest",
        bash_command="docker exec spark-master spark-submit /opt/spark-app/notebooks/00_bronze_ingest.py",
    )
    
    silver_transform = BashOperator(
        task_id='silver_transform',
        bash_command='docker exec spark-master spark-submit /opt/spark-app/notebooks/10_silver_transform.py',
    )

    gold_aggregate = BashOperator(
        task_id='gold_aggregate',
        bash_command='docker exec spark-master spark-submit /opt/spark-app/notebooks/20_gold_aggregate.py',
    )

    ingest >> silver_transform >> gold_aggregate
