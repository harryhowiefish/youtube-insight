from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator
# from airflow.sensors.time_delta import TimeDeltaSensor


default_args = {
    'owner': 'Harry',
    'retries': 1,
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
        bash_command='cd /opt/airflow && python airflow_scripts/db_control.py off',  # noqa
        dag=db_control,
        execution_timeout=timedelta(minutes=20)
    )

# delay_task = TimeDeltaSensor(
#     delta=datetime.timedelta(minutes=5)

# )

# status_check = BashOperator(
#         task_id='initiate_shutdown',
#         bash_command='cd /opt/airflow && python airflow_scripts/db_control.py off',  # noqa
#         dag=db_control
#     )

# start_task >> delay_task >> status_check
