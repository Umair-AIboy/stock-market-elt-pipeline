import os
from sqlalchemy import create_engine, text

def get_engine():
    host = os.getenv("STOCKDB_HOST", "localhost")
    return create_engine(f"postgresql+psycopg2://airflow:airflow@{host}:5432/stockdata")

def run_sql_file(path: str):
    """Execute a .sql file against stockdata. Used by Airflow for DDL + transform steps."""
    engine = get_engine()
    with open(path, "r") as f:
        sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(sql))
    print(f"Executed {path}")