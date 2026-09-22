import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow/scripts")

import extract as extract_module
import data_quality as dq_module
from db_utils import run_sql_file

SQL_DIR = "/opt/airflow/sql"

default_args = {
    "owner": "data-eng",
    "retries": 1,
}

with DAG(
    dag_id="stock_pipeline_dag",
    description="Extract stock prices, load raw, transform to marts, check quality",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["stock", "elt"],
) as dag:

    create_tables_task = PythonOperator(
        task_id="create_tables",
        python_callable=run_sql_file,
        op_args=[f"{SQL_DIR}/01_create_tables.sql"],
    )

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract_module.run,
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=run_sql_file,
        op_args=[f"{SQL_DIR}/02_transform.sql"],
    )

    quality_check_task = PythonOperator(
        task_id="quality_check",
        python_callable=dq_module.run,
    )

    create_tables_task >> extract_task >> transform_task >> quality_check_task