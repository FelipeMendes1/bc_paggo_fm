from sqlalchemy import Column, Integer, Float, DateTime
from database import Base

class Data(Base):
    """
    Model for the time series data in the source database
    """
    __tablename__ = "data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    wind_speed = Column(Float, nullable=False)
    power = Column(Float, nullable=False)
    ambient_temperature = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<Data(timestamp={self.timestamp}, wind_speed={self.wind_speed}, power={self.power}, temp={self.ambient_temperature})>"
