import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure logging
logger = logging.getLogger(__name__)

# Get database URL from environment variable with default fallback
TARGET_DB_URI = os.getenv("TARGET_DB_URI", "postgresql://postgres:postgres@target_db:5432/target")

# Create SQLAlchemy engine and session factory
engine = create_engine(TARGET_DB_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db_session():
    """
    Get a database session for the target database
    """
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        logger.error(f"Error creating database session: {str(e)}")
        raise

def init_target_db():
    """
    Initialize the target database with required tables
    """
    from models import Signal, SignalType, SignalData
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Target database tables created or already exist")
        
        # Initialize signal types if they don't exist
        session = get_db_session()
        
        # Check if we need to create default signal types
        if session.query(SignalType).count() == 0:
            logger.info("Creating default signal types")
            default_signal_types = [
                SignalType(id=1, name="wind_speed_avg"),
                SignalType(id=2, name="wind_speed_min"),
                SignalType(id=3, name="wind_speed_max"),
                SignalType(id=4, name="wind_speed_std"),
                SignalType(id=5, name="power_avg"),
                SignalType(id=6, name="power_min"),
                SignalType(id=7, name="power_max"),
                SignalType(id=8, name="power_std"),
            ]
            session.add_all(default_signal_types)
            session.commit()
            logger.info("Default signal types created")
        
        session.close()
        return True
    
    except Exception as e:
        logger.error(f"Error initializing target database: {str(e)}")
        return False
