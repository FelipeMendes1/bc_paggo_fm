"""
Dagster definitions for ETL Wind Power Pipeline
"""
import os
from datetime import datetime, timedelta

from dagster import (
    AssetIn, 
    AssetKey, 
    Definitions, 
    ScheduleDefinition, 
    asset, 
    define_asset_job, 
    job, 
    op, 
    repository, 
    schedule,
    DailyPartitionsDefinition
)

# Import ETL functions
from etl.transform import fetch_data_from_api, aggregate_data, save_to_target_db
from etl.database import get_db_session, init_target_db

# Get environment variables
SOURCE_API_URL = os.getenv("SOURCE_API_URL", "http://api:8000")
TARGET_DB_URI = os.getenv("TARGET_DB_URI", "postgresql://postgres:postgres@target_db:5432/target")

# Create a daily partition definition starting 30 days ago
start_date = datetime.now() - timedelta(days=30)
daily_partitions = DailyPartitionsDefinition(start_date=start_date)

# Assets-based definitions
@asset(
    partitions_def=daily_partitions,
    compute_kind="python",
    group_name="etl",
    description="Raw wind power data from the source API"
)
def raw_wind_power_data(context):
    """Extract data from the source API for the partitioned date"""
    # Get partition date
    partition_date_str = context.asset_partition_key_for_output()
    partition_date = datetime.strptime(partition_date_str, "%Y-%m-%d").date()
    
    # Define time boundaries
    start_datetime = datetime.combine(partition_date, datetime.min.time())
    end_datetime = datetime.combine(partition_date, datetime.max.time())
    
    # Fetch data from API
    df = fetch_data_from_api(
        start_datetime, 
        end_datetime,
        columns=["wind_speed", "power"]
    )
    
    context.log.info(f"Fetched {len(df)} records for date {partition_date_str}")
    return df

@asset(
    partitions_def=daily_partitions,
    compute_kind="python",
    ins={"raw_data": AssetIn("raw_wind_power_data")},
    group_name="etl",
    description="Aggregated wind power data in 10-minute windows"
)
def aggregated_wind_power_data(context, raw_data):
    """Transform the raw data with 10-minute aggregations"""
    if raw_data.empty:
        context.log.warning("No source data available to aggregate")
        return None
    
    # Aggregate in 10-minute windows
    agg_df = aggregate_data(raw_data, window_minutes=10)
    
    context.log.info(f"Aggregated data into {len(agg_df)} 10-minute windows")
    return agg_df

@asset(
    partitions_def=daily_partitions,
    compute_kind="python",
    ins={"aggregated_data": AssetIn("aggregated_wind_power_data")},
    group_name="etl",
    description="Transformed wind power data stored in the target database"
)
def wind_power_signals(context, aggregated_data):
    """Load the transformed data into the target database"""
    if aggregated_data is None or aggregated_data.empty:
        context.log.warning("No aggregated data available to load")
        return {"loaded": 0}
    
    # Initialize target database if needed
    init_target_db()
    
    # Save to target database
    db_session = get_db_session()
    try:
        records_saved = save_to_target_db(aggregated_data)
        
        context.log.info(f"Loaded {records_saved} signals into target database")
        return {"loaded": records_saved, "timestamp": datetime.now().isoformat()}
    finally:
        db_session.close()

# Define a job that materializes all ETL assets for a partition
etl_job = define_asset_job(
    name="etl_daily_job",
    selection=["raw_wind_power_data", "aggregated_wind_power_data", "wind_power_signals"],
    description="Daily ETL job that processes wind power data"
)

# Define a schedule that runs the job every day at 2 AM
etl_schedule = ScheduleDefinition(
    name="daily_etl_schedule",
    job=etl_job,
    cron_schedule="0 2 * * *",  # Run at 2 AM every day
    description="Schedule for running the ETL job daily"
)

# Ops-based definitions (alternative approach)
@op
def initialize_target_db_op():
    """Initialize the target database if needed"""
    result = init_target_db()
    return result

@op
def extract_data_op(start_date, end_date):
    """Extract data from the source API for date range"""
    df = fetch_data_from_api(start_date, end_date, columns=["wind_speed", "power"])
    return df

@op
def transform_data_op(df):
    """Transform data with 10-minute aggregations"""
    if df.empty:
        return None
    return aggregate_data(df, window_minutes=10)

@op
def load_data_op(agg_df):
    """Load data into target database"""
    if agg_df is None or agg_df.empty:
        return {"loaded": 0}
    
    db_session = get_db_session()
    try:
        records_saved = save_to_target_db(agg_df)
        return {"loaded": records_saved}
    finally:
        db_session.close()
@op
def get_start_datetime():
    yesterday = datetime.now() - timedelta(days=1)
    return datetime.combine(yesterday, datetime.min.time())

@op
def get_end_datetime():
    yesterday = datetime.now() - timedelta(days=1)
    return datetime.combine(yesterday, datetime.max.time())

@job
def etl_pipeline_job():
    """ETL pipeline job for wind power data"""
    initialize_target_db_op()
    
    start = get_start_datetime()
    end = get_end_datetime()
    
    data_df = extract_data_op(start, end)
    agg_df = transform_data_op(data_df)
    load_data_op(agg_df)

# Define a schedule for the ops-based job
@schedule(
    cron_schedule="0 1 * * *",  # Run at 1 AM every day
    job=etl_pipeline_job,
    execution_timezone="UTC",
)
def daily_etl_pipeline_schedule():
    """Schedule for running the ETL pipeline job daily"""
    return {}

# Define Dagster definitions
defs = Definitions(
    assets=[raw_wind_power_data, aggregated_wind_power_data, wind_power_signals],
    schedules=[etl_schedule],
    jobs=[etl_pipeline_job],
)
