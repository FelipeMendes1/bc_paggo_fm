import os
import logging
import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, MetaData, Table
from sqlalchemy import text
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Source database connection string
SOURCE_DB_URI = os.getenv("SOURCE_DB_URI", "postgresql://postgres:postgres@source_db:5432/source")

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
    cubic_factor = (wind_speed[mask_below_rated] - cut_in) / (rated_speed - cut_in)
    power_base[mask_below_rated] = rated_power * cubic_factor**3
    
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

def main():
    """
    Initialize source database and populate with random data
    """
    try:
        # Create engine
        engine = create_engine(SOURCE_DB_URI)
        
        # Create metadata and tables
        metadata = MetaData()
        
        # Define 'data' table
        data_table = Table(
            'data', 
            metadata,
            Column('id', Integer, primary_key=True),
            Column('timestamp', DateTime, nullable=False, index=True),
            Column('wind_speed', Float, nullable=False),
            Column('power', Float, nullable=False),
            Column('ambient_temperature', Float, nullable=False)
        )
        
        # Create tables
        metadata.create_all(engine)
        logger.info("Source database tables created")
        
        # Check if table already has data
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM data"))
            count = result.scalar()
            
            if count > 0:
                logger.info(f"Source database already contains {count} records, skipping data generation")
                return
        
        # Generate random data (10 days of data at 1-minute intervals)
        start_date = datetime.now() - timedelta(days=10)
        df = generate_random_data(start_date, days=10, frequency='1min')
        
        # Insert data into database
        df.to_sql('data', engine, if_exists='append', index=False)
        
        logger.info(f"Successfully added {len(df)} records to source database")
        
    except Exception as e:
        logger.error(f"Error initializing source database: {str(e)}")
        raise

if __name__ == "__main__":
    main()
