import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable with default fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@source_db:5432/source")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """
    Dependency for database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
