import os
import logging
import sys
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, MetaData, Table, JSON
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Target database connection string
TARGET_DB_URI = os.getenv("TARGET_DB_URI", "postgresql://postgres:postgres@target_db:5432/target")

def main():
    """
    Initialize target database with required schema
    """
    try:
        # Create engine
        engine = create_engine(TARGET_DB_URI)
        
        # Create metadata and tables
        metadata = MetaData()
        
        # Define 'signal_type' table
        signal_type_table = Table(
            'signal_type', 
            metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50), nullable=False, unique=True)
        )
        
        # Define 'signal' table
        signal_table = Table(
            'signal', 
            metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(100), nullable=False),
            Column('data', JSON, nullable=True),
            Column('timestamp', DateTime, nullable=False),
            Column('signal_id', Integer, ForeignKey('signal_type.id'), nullable=False),
            Column('value', Float, nullable=False)
        )
        
        # Define 'signal_data' table for additional metadata
        signal_data_table = Table(
            'signal_data', 
            metadata,
            Column('id', Integer, primary_key=True),
            Column('signal_id', Integer, ForeignKey('signal.id'), nullable=False),
            Column('key', String(50), nullable=False),
            Column('value', String(200), nullable=False)
        )
        
        # Create tables
        metadata.create_all(engine)
        logger.info("Target database tables created")
        
        # Check if signal_type table has data
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM signal_type"))
            count = result.scalar()
            
            if count > 0:
                logger.info(f"Target database signal_type table already contains {count} records, skipping initialization")
                return
            
            # Insert default signal types
            signal_types = [
                {"id": 1, "name": "wind_speed_avg"},
                {"id": 2, "name": "wind_speed_min"},
                {"id": 3, "name": "wind_speed_max"},
                {"id": 4, "name": "wind_speed_std"},
                {"id": 5, "name": "power_avg"},
                {"id": 6, "name": "power_min"},
                {"id": 7, "name": "power_max"},
                {"id": 8, "name": "power_std"},
            ]
            
            connection.execute(signal_type_table.insert(), signal_types)
            logger.info(f"Added {len(signal_types)} default signal types to target database")
        
    except Exception as e:
        logger.error(f"Error initializing target database: {str(e)}")
        raise

if __name__ == "__main__":
    main()
