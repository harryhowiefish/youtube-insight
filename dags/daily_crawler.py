from airflow import DAG
from datetime import timedelta, datetime
from airflow.operators.bash import BashOperator
# from airflow.operators.python import PythonOperator
# from airflow_scripts import update_channel_stat
default_args = {
    'owner': 'Harry',
    'retries': 2,
    'retry_delay': timedelta(minutes=1)
}

pipeline = DAG(
    dag_id='daily_crawler',
    default_args=default_args,
    schedule_interval='0 9 * * *',
    start_date=datetime(2024, 2, 16),
    catchup=False
)

start_task = BashOperator(
        task_id='spin_up_db',
        bash_command='cd /opt/airflow && python airflow_scripts/db_control.py -set on',  # noqa
        dag=pipeline,
        execution_timeout=timedelta(minutes=20)
    )

new_video = BashOperator(
    task_id='crawl_new_video',
    bash_command='cd /opt/airflow && python airflow_scripts/crawl_new_videos.py',  # noqa
    dag=pipeline
)

update_channel = BashOperator(
    task_id='refresh_channel_stat',
    bash_command='cd /opt/airflow && python airflow_scripts/update_channel_stat.py',  # noqa
    dag=pipeline
)

update_video = BashOperator(
    task_id='refresh_video_stat',
    bash_command='cd /opt/airflow && python airflow_scripts/update_video_stat.py',  # noqa
    dag=pipeline
)

end_task = BashOperator(
        task_id='initiate_shutdown',
        bash_command='cd /opt/airflow && python airflow_scripts/db_control.py -set off',  # noqa
        dag=pipeline,
        execution_timeout=timedelta(minutes=20)
    )

start_task >> new_video
start_task >> update_channel
new_video >> update_video
update_video >> end_task
update_channel >> end_task
