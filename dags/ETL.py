from airflow import DAG
import datetime
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from pyspark.sql import SparkSession, Window
import pyspark.sql.functions as F
from src import utils
import os

default_args = {
    'owner': 'Harry',
    'retries': 2,
    'retry_delay': datetime.timedelta(hours=1)
}


def save_from_db():
    spark: SparkSession = SparkSession.builder.config(
        "spark.jars", "./postgresql-42.6.2.jar"
    ).master("local").appName("PySpark_Postgres_test").getOrCreate()
    utils.load_env('./.ENV')
    HOST = os.environ['pg_host']
    USER = os.environ['pg_user']
    DBNAME = os.environ['pg_dbname']
    PASSWORD = os.environ['pg_password']
    connection_base = spark.read.format("jdbc").option(
        "url", f"jdbc:postgresql://{HOST}:5432/{DBNAME}").option(
        "driver", "org.postgresql.Driver").option(
        "user", USER).option("password", PASSWORD)
    v = connection_base.option("dbtable", "video").load()
    vl = connection_base.option("dbtable", "video_log").load()
    c = connection_base.option("dbtable", "channel").load()
    cl = connection_base.option("dbtable", "channel_log").load()
    v.write.parquet('video_raw.parquet')
    vl.write.parquet('video_log_raw.parquet')
    c.write.parquet('channel_raw.parquet')
    cl.write.parquet('channel_log_raw.parquet')


def create_time_dimension_table():
    spark: SparkSession = SparkSession.builder.getOrCreate()
    start_date = (2024, 4, 1)
    end_date = (2030, 12, 31)
    start_unix = int(datetime.date(*start_date).strftime('%s'))
    end_unix = int(datetime.date(*end_date).strftime('%s'))
    date_df = spark.range(
        start_unix, end_unix+1, 24*60*60).toDF("timestamp")
    date_df = date_df.withColumn(
        "date", F.to_date(F.from_unixtime("timestamp")))
    date_df = date_df.select("date",
                             F.year("date").alias("year"),
                             F.month("date").alias("month"),
                             F.dayofmonth("date").alias("day"),
                             F.weekofyear("date").alias("week_of_year"),
                             F.dayofweek("date").alias("day_of_week"),
                             F.quarter("date").alias("quarter"),
                             F.dayofyear("date").alias("day_of_year")
                             )
    is_weekend_expr = F.when(
        F.col("day_of_week").isin([1, 7]), True).otherwise(False)
    date_df = date_df.withColumn("is_weekend", is_weekend_expr)
    date_df.write.csv("OLAP_table/time_dimension.csv", mode='overwrite')


def create_channel_dimension_table():
    spark: SparkSession = SparkSession.builder.getOrCreate()
    c = spark.read.parquet('channel_raw.parquet')
    channel_dim = c.select(['channel_id', 'name', 'customurl',
                            'published_date', 'country', 'keywords', 'topic'])
    channel_dim.write.csv('OLAP_table/channel_dimension.csv', mode='overwrite')


def create_monthly_channel_fact_table():
    spark: SparkSession = SparkSession.builder.getOrCreate()
    today = datetime.date.today()
    last_day = datetime.date(today.year, today.month,
                             1)-datetime.timedelta(days=1)
    first_day = datetime.date(last_day.year, last_day.month, 1)
    # start_unix = int(first_day.strftime('%s'))
    # end_unix = int(last_day.strftime('%s'))
    first_day_of_weeks = [
        first_day+datetime.timedelta(days=num) for num in range(0, 29, 6)]

    cl = spark.read.parquet('channel_log_raw.parquet')
    checkpoints = cl.select(['channel_id', 'sub_count', 'view_count',
                             'video_count', 'created_date']).where(
        cl['created_date'].isin(first_day_of_weeks))
    w = Window.partitionBy("channel_id").orderBy("created_date")
    checkpoints = checkpoints.withColumn('week_num', F.row_number().over(w))
    for col in ['sub_count', 'view_count', 'video_count']:
        checkpoints = checkpoints.withColumn(
            f"{col.split('_')[0]}_delta", F.lead(col, 1).over(w)-F.col(col))
    checkpoints = checkpoints.where(F.col('week_num') != 5).select(
        ['channel_id', 'week_num', 'sub_delta', 'view_delta', 'video_delta'])
    monthly_stat = checkpoints.groupBy('channel_id').pivot('week_num').agg(
        F.first('sub_delta').alias('sub_delta'),
        F.first('view_delta').alias('view_delta'),
        F.first('video_delta').alias('video_delta')
    )
    monthly_delta = cl.groupBy('channel_id').agg(
        (F.last('sub_count')-F.first('sub_count')).alias('monthly_sub_delta'),
        (F.last('view_count')-F.first('view_count')).alias('monthly_view_delta'),  # noqa
        (F.last('video_count')-F.first('video_count')).alias('monthly_video_delta')  # noqa
    )
    monthly_stat = monthly_stat.join(monthly_delta, on='channel_id')
    w = Window.orderBy(F.desc('monthly_sub_delta'))
    monthly_stat = monthly_stat.withColumn('sub_ranking', F.rank().over(w))
    w = Window.orderBy(F.desc('monthly_view_delta'))
    monthly_stat = monthly_stat.withColumn('view_ranking', F.rank().over(w))
    monthly_stat.write.csv(
        'OLAP_table/monthly_channel_fact.csv', mode='overwrite')


def create_video_fact_table():
    spark: SparkSession = SparkSession.builder.getOrCreate()
    vl = spark.read.parquet('video_log_raw.parquet')
    v = spark.read.parquet('video_raw.parquet')
    cl = spark.read.parquet('channel_log_raw.parquet')
    v = v.withColumns({"duration_list": F.split(F.col('duration'), ':'),
                       'duration_hour': F.col('duration_list')[0].cast('int'),
                       'duration_minute': F.col('duration_list')[1].cast('int'),  # noqa
                       'duration_second': F.col('duration_list')[2].cast('int')})  # noqa
    v = v.withColumn('published_hour', F.hour(v['published_time']))
    v = v.withColumn('duration',
                     F.col('duration_hour')*60 +
                     F.col('duration_minute') +
                     F.col('duration_second')/60
                     )
    v = v.select(['video_id', 'title', 'channel_id',
                 'video_type', 'published_time', 'duration'])
    w = Window.partitionBy('video_id').orderBy('created_date')
    vl = vl.withColumn("day_since_publish", F.row_number().over(w))
    vl = vl.groupBy('video_id').pivot('day_since_publish').agg(
        F.first('created_date').alias('date'),
        F.first('view_count').alias('view'),
        F.first('comment_count').alias('comment'),
        F.first('like_count').alias('like')
    )
    channel_sub_count_updated = cl.orderBy(
        'created_date', ascending=False).drop_duplicates(
            subset=['channel_id']).select(
                ['channel_id', 'sub_count'])
    result = v.join(vl, on='video_id').join(
        channel_sub_count_updated, on='channel_id')
    w = Window.partitionBy(['channel_id', 'video_type']).orderBy('30_view')
    result = result.withColumn(
        "video_ranking", F.row_number().over(w)).sort('published_time')
    result = result.withColumn(
        "avg_daily_view", (F.col('30_view')/6).cast('int'))
    result = result.withColumn(
        'sub_view_ratio', (F.col('30_view')/F.col('sub_count')).cast('int'))
    result.write.csv('OLAP_table/video_fact_table.csv', mode='overwrite')


ETL_demo = DAG(
    dag_id='ETL_demo',
    default_args=default_args,
    start_date=datetime(2024, 3, 30),
    schedule_interval='0 1 1 1 *',
    catchup=False
)

start_task = BashOperator(
        task_id='spin_up_db',
        bash_command='cd /opt/airflow && python src/airflow_scripts/db_control.py -set on',  # noqa
        dag=ETL_demo,
        execution_timeout=datetime.timedelta(minutes=20)
    )
load_data = PythonOperator(
    task_id='save_data_from_DB',
    python_callable=save_from_db,
    dag=ETL_demo,
)

time_dimension = PythonOperator(
    task_id='time_dimension',
    python_callable=create_time_dimension_table,
    dag=ETL_demo,
)

channel_dimension = PythonOperator(
    task_id='channel_dimension',
    python_callable=create_channel_dimension_table,
    dag=ETL_demo,
)

monthly_channel_fact = PythonOperator(
    task_id='monthly_channel_fact',
    python_callable=create_monthly_channel_fact_table,
    dag=ETL_demo,
)

video_fact = PythonOperator(
    task_id='video_fact',
    python_callable=create_video_fact_table,
    dag=ETL_demo,
)


start_task >> load_data

load_data >> time_dimension
load_data >> channel_dimension
load_data >> monthly_channel_fact
load_data >> video_fact
