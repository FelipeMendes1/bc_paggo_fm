from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SignalType(Base):
    """
    Model for signal types in the target database
    """
    __tablename__ = "signal_type"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    
    # Relationship to signals
    signals = relationship("Signal", back_populates="signal_type")
    
    def __repr__(self):
        return f"<SignalType(id={self.id}, name={self.name})>"

class Signal(Base):
    """
    Model for the signal table in the target database
    """
    __tablename__ = "signal"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    signal_id = Column(Integer, ForeignKey("signal_type.id"), nullable=False)
    value = Column(Float, nullable=False)
    
    # Relationship to signal type
    signal_type = relationship("SignalType", back_populates="signals")
    
    def __repr__(self):
        return f"<Signal(id={self.id}, name={self.name}, timestamp={self.timestamp}, value={self.value})>"

class SignalData(Base):
    """
    Model for additional signal data storage (if needed)
    """
    __tablename__ = "signal_data"
    
    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey("signal.id"), nullable=False)
    key = Column(String(50), nullable=False)
    value = Column(String(200), nullable=False)
    
    # Relationship to signal
    signal = relationship("Signal")
    
    def __repr__(self):
        return f"<SignalData(id={self.id}, signal_id={self.signal_id}, key={self.key}, value={self.value})>"
