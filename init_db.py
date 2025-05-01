import os
import logging
import sys
from datetime import datetime, timedelta
import random
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import db
from models import Data, SignalType, Signal

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def generate_random_data(start_date, days=10, frequency='1min'):
    """
    Generate random time series data for the source database
    
    Args:
        start_date: Start date for data generation
        days: Number of days to generate data for
        frequency: Data frequency (default: 1 minute)
    
    Returns:
        DataFrame with generated data
    """
    logger.info(f"Generating random data from {start_date} for {days} days with {frequency} frequency")
    
    # Calculate end date
    end_date = start_date + timedelta(days=days)
    
    # Create date range with the specified frequency
    date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)
    
    # Initialize random number generators with seeds for reproducibility
    wind_rng = np.random.RandomState(42)
    power_rng = np.random.RandomState(43)
    temp_rng = np.random.RandomState(44)
    
    # Generate random data with realistic patterns
    
    # Wind speed: 0-25 m/s with daily and hourly patterns
    # Base wind speed
    wind_base = 8 + 5 * np.sin(np.linspace(0, days * 2 * np.pi, len(date_range)))
    # Add hourly variation
    hourly_var = 2 * np.sin(np.linspace(0, days * 24 * 2 * np.pi, len(date_range)))
    # Add random noise
    wind_noise = wind_rng.normal(0, 1, size=len(date_range))
    # Combine and clip to realistic range
    wind_speed = np.clip(wind_base + hourly_var + wind_noise, 0, 25)
    
    # Power output: 0-1500 kW, correlated with wind speed
    # Power is a function of wind speed (roughly cubic relationship with cutoffs)
    power_base = np.zeros_like(wind_speed)
    # Below cut-in speed (typically 3-4 m/s) no power
    cut_in = 3.5
    cut_out = 25.0  # Above cut-out, turbine shuts down
    rated_speed = 12.0  # Speed at which rated power is reached
    rated_power = 1500.0  # Rated power in kW
    
    # Calculate power based on wind speed regions
    mask_below_cutin = wind_speed < cut_in
    mask_above_cutout = wind_speed > cut_out
    mask_below_rated = (wind_speed >= cut_in) & (wind_speed < rated_speed)
    mask_rated = (wind_speed >= rated_speed) & (wind_speed <= cut_out)
    
    # No power below cut-in or above cut-out
    power_base[mask_below_cutin | mask_above_cutout] = 0
    
    # Cubic relationship between cut-in and rated speed
    cubic_factor = np.zeros_like(wind_speed)
    if np.any(mask_below_rated):
        cubic_factor[mask_below_rated] = (wind_speed[mask_below_rated] - cut_in) / (rated_speed - cut_in)
        power_base[mask_below_rated] = rated_power * cubic_factor[mask_below_rated]**3
    
    # Rated power between rated speed and cut-out
    power_base[mask_rated] = rated_power
    
    # Add some random variation (efficiency, errors, etc.)
    power_noise = power_rng.normal(0, 50, size=len(date_range))
    power = np.clip(power_base + power_noise, 0, rated_power)
    
    # Ambient temperature: -10 to 35°C with daily cycle
    temp_base = 15 + 10 * np.sin(np.linspace(0, days * 2 * np.pi, len(date_range)))
    # Add hourly variation (cooler nights, warmer days)
    temp_hourly = 5 * np.sin(np.linspace(0, days * 24 * 2 * np.pi, len(date_range)))
    # Add random noise
    temp_noise = temp_rng.normal(0, 1, size=len(date_range))
    # Combine and clip to realistic range
    ambient_temperature = np.clip(temp_base + temp_hourly + temp_noise, -10, 35)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': date_range,
        'wind_speed': wind_speed,
        'power': power,
        'ambient_temperature': ambient_temperature
    })
    
    logger.info(f"Generated {len(df)} data points")
    return df

def process_etl_data(days=1):
    """
    Process ETL data for the last 'days' days
    
    Args:
        days: Number of days to process
    
    Returns:
        Number of records processed
    """
    from main import app
    
    with app.app_context():
        try:
            # Get date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get data from the database
            data_records = Data.query.filter(
                Data.timestamp >= start_date,
                Data.timestamp <= end_date
            ).order_by(Data.timestamp).all()
            
            if not data_records:
                logger.warning(f"No data found for ETL processing in date range: {start_date} to {end_date}")
                return 0
            
            # Convert to DataFrame
            df_data = []
            for record in data_records:
                df_data.append({
                    'timestamp': record.timestamp,
                    'wind_speed': record.wind_speed,
                    'power': record.power
                })
            
            df = pd.DataFrame(df_data)
            df = df.set_index('timestamp')
            
            # Resample to 10-minute windows
            rule = '10T'
            
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
            
            # Define mapping of DataFrame columns to signal types
            signal_type_mapping = {
                "wind_speed_mean": 1,  # wind_speed_avg
                "wind_speed_min": 2,   # wind_speed_min
                "wind_speed_max": 3,   # wind_speed_max
                "wind_speed_std": 4,   # wind_speed_std
                "power_mean": 5,       # power_avg
                "power_min": 6,        # power_min
                "power_max": 7,        # power_max
                "power_std": 8,        # power_std
            }
            
            signals_to_add = []
            
            # Iterate through DataFrame rows
            for _, row in result.iterrows():
                timestamp = row["timestamp"]
                
                # Create data JSON object with all values from the row
                data_json = {col: float(row[col]) for col in result.columns if col != "timestamp"}
                
                # Create a signal record for each metric
                for column, signal_type_id in signal_type_mapping.items():
                    if column in row:
                        signal = Signal(
                            name=column,
                            timestamp=timestamp,
                            signal_id=signal_type_id,
                            value=float(row[column]),
                            data=data_json
                        )
                        signals_to_add.append(signal)
            
            # Bulk insert records
            if signals_to_add:
                db.session.add_all(signals_to_add)
                db.session.commit()
                
                logger.info(f"Successfully saved {len(signals_to_add)} signal records")
                return len(signals_to_add)
            
            return 0
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing ETL data: {str(e)}")
            return 0

def initialize_database():
    """
    Initialize the database with sample data
    """
    from main import app
    
    with app.app_context():
        try:
            # Check if there's any data in the database
            if Data.query.count() > 0:
                logger.info("Database already contains data, skipping initialization")
                return
            
            # Generate sample data
            start_date = datetime.now() - timedelta(days=10)
            df = generate_random_data(start_date, days=10, frequency='1min')
            
            # Insert data into database
            for _, row in df.iterrows():
                data = Data(
                    timestamp=row['timestamp'],
                    wind_speed=row['wind_speed'],
                    power=row['power'],
                    ambient_temperature=row['ambient_temperature']
                )
                db.session.add(data)
            
            db.session.commit()
            logger.info(f"Successfully inserted {len(df)} records into database")
            
            # Process ETL data for the sample data
            process_etl_data(days=10)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error initializing database: {str(e)}")

if __name__ == "__main__":
    initialize_database()