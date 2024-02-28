from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'Harry',
    'retries': 0
}


def status_update():
    from src.core import DB_Connection
    db = DB_Connection()
    db.update(
        '''
          update video
          set active = False
          where published_date < current_date - interval '30 day'
          and active = True
        ''')


update_video_status = DAG(
    dag_id='update_video_status',
    default_args=default_args,
    start_date=datetime(2024, 2, 18),
    schedule_interval='@daily',
    catchup=False
)

start_task = BashOperator(
        task_id='spin_up_db',
        bash_command='cd /opt/airflow && python src/airflow_scripts/db_control.py -set on',  # noqa
        dag=update_video_status,
        execution_timeout=timedelta(minutes=20)
    )

sql_update = PythonOperator(
    task_id='sql_update',
    python_callable=status_update,
    dag=update_video_status
)

end_task = BashOperator(
        task_id='initiate_shutdown',
        bash_command='cd /opt/airflow && python src/airflow_scripts/db_control.py -set off',  # noqa
        dag=update_video_status,
        execution_timeout=timedelta(minutes=20)
    )

start_task >> sql_update
sql_update >> end_task
