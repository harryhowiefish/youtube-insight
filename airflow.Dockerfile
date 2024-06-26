FROM apache/airflow:2.8.1-python3.10
ENV PYTHONPATH "$AIRFLOW_HOME"
COPY requirements.txt /requirements.txt
COPY .ENV /opt/airflow/.ENV
RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt