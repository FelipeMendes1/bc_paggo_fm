# ETL Wind Power - Complete ETL Solution

This project provides a complete ETL (Extract, Transform, Load) pipeline for wind energy data using PostgreSQL, Python (Flask), and Dagster for orchestration.

## 🗂 Overview

The system ingests raw turbine data (wind speed, power, ambient temperature), applies transformations (10-minute statistical aggregation), and loads the processed data into a target database for analysis and visualization.

## 🧱 Architecture

- **Source DB**: PostgreSQL storing raw sensor data.
- **Target DB**: PostgreSQL storing aggregated signal data.
- **API**: Flask service exposing REST endpoints.
- **ETL Processor**: Handles extraction, transformation, and loading.
- **Dagster**: Manages orchestration and scheduling of the ETL jobs.

## 🚀 Quick Start (with Docker Compose)

### 1. Clone the repository

```bash
git clone https://github.com/FelipeMendes1/bc_paggo_fm.git
cd DataPipelineSage
```

### 2. Build and start all services

```bash
docker-compose up --build -d
```

This will start:
- `api`: Flask application
- `etl`: ETL processor
- `source_db`: PostgreSQL for raw data
- `target_db`: PostgreSQL for processed data
- `dagster-dagit`: Dagster web UI
- `dagster-daemon`: Scheduler

### 3. Access interfaces

- **API Dashboard**: http://localhost:8000  
- **Dagster UI**: http://localhost:3000  
- **Health Check**: http://localhost:8000/health  
- **Docs Page**: http://localhost:8000/docs

### 4. Shut down services

```bash
docker-compose down
```

## 🔌 API Endpoints

| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| GET    | `/api/data`           | Retrieve raw sensor data                 |
| GET    | `/api/signals`        | Retrieve aggregated signal data          |
| POST   | `/api/run-etl`        | Manually trigger ETL process             |
| POST   | `/api/generate-data`  | Generate synthetic sample data           |
| GET    | `/health`             | Health check                             |

## ⚙️ ETL Flow

1. **Extract**: Query raw data from source database.
2. **Transform**: Resample and aggregate data into 10-minute intervals:
   - `wind_speed`: mean, min, max, std
   - `power`: mean, min, max, std
3. **Load**: Save structured data to target database as signals

