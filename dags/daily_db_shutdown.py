from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator


default_args = {
    'owner': 'Harry',
    'retries': 2,
    'retry_delay': timedelta(minutes=1)
}

db_control = DAG(
    dag_id='daily_db_shutdown',
    default_args=default_args,
    start_date=datetime(2024, 2, 17),
    schedule_interval='0 15 * * *',
    catchup=False
)

start_task = BashOperator(
        task_id='initiate_shutdown',
        bash_command='cd /opt/airflow && python src/airflow_scripts/db_control.py -set off',  # noqa
        dag=db_control,
        execution_timeout=timedelta(minutes=20)
    )
