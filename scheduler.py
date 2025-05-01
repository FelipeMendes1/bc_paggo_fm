"""
Dagster orchestration for the ETL process (optional/bonus component)
This provides a more robust scheduling and orchestration framework
"""

import os
from datetime import datetime, timedelta
from dagster import asset, op, job, schedule, AssetIn, In, Out, daily_partitioned_config
from dagster.utils import file_relative_path
import pandas as pd

from transform import fetch_data_from_api, aggregate_data
from database import get_db_session, init_target_db
from models import Signal

# Define resources for database connections
@op
def initialize_target_db():
    """Initialize the target database if needed"""
    return init_target_db()

# Partitioned asset to process data by day
@asset(
    partitions_def=daily_partitioned_config(
        start_date=datetime.now() - timedelta(days=10),
    ),
)
def source_data(context):
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
    ins={"source_data": AssetIn()},
)
def aggregated_data(context, source_data):
    """Transform the source data with 10-minute aggregations"""
    if source_data.empty:
        context.log.warning("No source data available to aggregate")
        return pd.DataFrame()
    
    # Aggregate in 10-minute windows
    agg_df = aggregate_data(source_data, window_minutes=10)
    
    context.log.info(f"Aggregated data into {len(agg_df)} 10-minute windows")
    return agg_df

@asset(
    ins={"aggregated_data": AssetIn()},
    required_resource_keys={"target_db_initialized"}
)
def transformed_signals(context, aggregated_data):
    """Load the transformed data into the target database"""
    if aggregated_data.empty:
        context.log.warning("No aggregated data available to load")
        return {"loaded": 0}
    
    # Save to target database
    db_session = get_db_session()
    try:
        from transform import save_to_target_db
        records_saved = save_to_target_db(aggregated_data, db_session)
        
        context.log.info(f"Loaded {records_saved} signals into target database")
        return {"loaded": records_saved}
    finally:
        db_session.close()

# Define a job that processes data for a specific day
@job
def etl_daily_job():
    # Initialize database
    db_initialized = initialize_target_db()
    
    # Process ETL
    source = source_data()
    agg = aggregated_data(source)
    transformed_signals(aggregated_data=agg, target_db_initialized=db_initialized)

# Define a schedule that runs the job every day
@schedule(
    cron_schedule="0 1 * * *",  # Run at 1 AM every day
    job=etl_daily_job,
    execution_timezone="UTC",
)
def daily_etl_schedule():
    """Schedule for running the ETL job daily"""
    return {}
