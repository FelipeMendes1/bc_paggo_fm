import os
import logging
from datetime import datetime, timedelta
import httpx
import pandas as pd
import psycopg2 
import json
# Configure logging
logger = logging.getLogger(__name__)

# Get API URL from environment variable with default
SOURCE_API_URL = os.getenv("SOURCE_API_URL", "http://api:8000")

def fetch_data_from_api(start_date, end_date, columns=None):
    """
    Fetch data from the source API with date range filter
    
    Args:
        start_date: Start datetime
        end_date: End datetime
        columns: List of columns to fetch (optional)
    
    Returns:
        DataFrame with the fetched data
    """
    try:
        # Build query parameters
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        
        if columns:
            params["columns"] = ",".join(columns)
        
        url = f"{SOURCE_API_URL}/api/data"
        logger.info(f"Fetching data from {url} with params: {params}")

        
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, params=params)
            
            # Check for successful response
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            if not data.get("data"):
                logger.warning(f"No data returned from API for date range: {start_date} to {end_date}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(data["data"])
            
            # Convert timestamp column to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            logger.info(f"Successfully fetched {len(df)} records from API")
            return df
    
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching data from API: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error fetching data from API: {str(e)}")
        raise

def aggregate_data(df, window_minutes=10):
    """
    Aggregate data into specified time windows and calculate statistics
    
    Args:
        df: DataFrame with source data
        window_minutes: Size of aggregation window in minutes
    
    Returns:
        DataFrame with aggregated data
    """
    if df.empty:
        return pd.DataFrame()
    
    try:
        # Set timestamp as index for resampling
        df = df.set_index("timestamp")
        
        # Define resampling rule (e.g., '10T' for 10 minutes)
        rule = f"{window_minutes}T"
        
        # Calculate aggregations for wind_speed
        wind_speed_agg = df["wind_speed"].resample(rule).agg(["mean", "min", "max", "std"])
        wind_speed_agg.columns = [f"wind_speed_{col}" for col in wind_speed_agg.columns]
        
        # Calculate aggregations for power
        power_agg = df["power"].resample(rule).agg(["mean", "min", "max", "std"])
        power_agg.columns = [f"power_{col}" for col in power_agg.columns]
        
        # Combine aggregated data
        result = pd.concat([wind_speed_agg, power_agg], axis=1)
        
        # Reset index to make timestamp a column again
        result = result.reset_index()
        
        # Fill NaN values (can happen if a window has no data)
        result = result.fillna(0)
        
        logger.info(f"Aggregated data into {len(result)} {window_minutes}-minute windows")
        return result
    
    except Exception as e:
        logger.error(f"Error aggregating data: {str(e)}")
        raise

def save_to_target_db(df):
    """
    Save aggregated data to the target database using psycopg2
    
    Args:
        df: DataFrame with aggregated data
    
    Returns:
        Number of records saved
    """
    if df.empty:
        return 0

    try:
        # Conectar ao banco via psycopg2
        conn = psycopg2.connect(
            dbname="target",
            user="postgres",
            password="postgres",
            host="target_db",
            port=5432
        )
        cursor = conn.cursor()

        # Mapear colunas para signal types
        signal_type_mapping = {
            "wind_speed_mean": 1,
            "wind_speed_min": 2,
            "wind_speed_max": 3,
            "wind_speed_std": 4,
            "power_mean": 5,
            "power_min": 6,
            "power_max": 7,
            "power_std": 8,
        }

        insert_query = """
        INSERT INTO signal (name, timestamp, signal_id, value, data)
        VALUES (%s, %s, %s, %s, %s)
        """

        records = []
        for _, row in df.iterrows():
            timestamp = row["timestamp"]
            data_json = {col: float(row[col]) for col in df.columns if col != "timestamp"}

            for column, signal_type_id in signal_type_mapping.items():
                if column in row:
                    records.append((
                        column,
                        timestamp,
                        signal_type_id,
                        float(row[column]),
                        json.dumps(data_json)
                    ))

        if records:
            cursor.executemany(insert_query, records)
            conn.commit()
            logger.info(f"Successfully saved {len(records)} records to target database")
            return len(records)

        return 0

    except Exception as e:
        logger.error(f"Error saving data to target database: {str(e)}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def process_data_for_date(date):
    from models import db, Signal
    try:
        # Convert date to datetime objects for start/end of day
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = datetime.combine(date, datetime.max.time())

        # Fetch data from API (only wind_speed and power as required)
        df = fetch_data_from_api(
            start_datetime,
            end_datetime,
            columns=["wind_speed", "power"]
        )

        if df.empty:
            logger.warning(f"No data available for date: {date}")
            return {"processed": 0, "loaded": 0, "date": date.isoformat()}

        # Aggregate data in 10-minute windows
        agg_df = aggregate_data(df, window_minutes=10)

        # Save to target database using psycopg2
        records_saved = save_to_target_db(agg_df)

        return {
            "processed": len(df),
            "loaded": records_saved,
            "date": date.isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing data for date {date}: {str(e)}")
        return {"processed": 0, "loaded": 0, "date": date.isoformat(), "error": str(e)}

