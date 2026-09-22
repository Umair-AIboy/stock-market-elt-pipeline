# Stock Market ELT Data Pipeline

An end-to-end ELT pipeline for ingesting, transforming, validating, and analyzing stock market data using Python, PostgreSQL, Apache Airflow, Docker, SQL, and Streamlit.

## Tech Stack

- Python
- PostgreSQL
- SQL
- Apache Airflow
- Docker & Docker Compose
- Streamlit
- yfinance API

## Pipeline

yfinance API
      ↓
Raw Data
      ↓
PostgreSQL
      ↓
Staging Layer
      ↓
SQL Transformations
      ↓
Mart Layer
      ↓
Streamlit Dashboard

## Features

- Automated stock market data ingestion
- PostgreSQL data warehouse
- Raw, staging, and mart layers
- SQL-based transformations
- Moving averages and day-over-day returns
- Stock trend classification
- Data quality validation
- Apache Airflow orchestration
- Dockerized deployment
- Interactive Streamlit dashboard