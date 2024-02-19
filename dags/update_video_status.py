from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'Harry',
    'retries': 0
}


def status_update():
    from src import db_connection
    db = db_connection.DB_Connection()
    db.conn_string_from_path('config/secrets.json')
    rowcount = db.update(
          '''
          update video
          set active = False
          where published_date < current_date - interval '30 day'
          and active = True
          ''')
    print(f'Number of row updated: {rowcount}')


update_video_status = DAG(
    dag_id='update_video_status',
    default_args=default_args,
    start_date=datetime(2024, 2, 18),
    schedule_interval='@daily',
    catchup=False
)

sql_update = PythonOperator(
    task_id='sql_update',
    python_callable=status_update,
    dag=update_video_status
)
