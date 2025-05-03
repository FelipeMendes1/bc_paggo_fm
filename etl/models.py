from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship 
from extensions import db
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SignalType(db.Model):
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


class Signal(db.Model):
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
        return (
            f"<Signal(id={self.id}, name={self.name}, timestamp={self.timestamp}, value={self.value})>"
        )

class Data(db.Model):
    """
    Model for the raw input data table in the source database
    """
    __tablename__ = "data"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    wind_speed = Column(Float, nullable=False)
    power = Column(Float, nullable=False)
    ambient_temperature = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Data(id={self.id}, timestamp={self.timestamp})>"

class SignalData(db.Model):
    """
    Optional model for storing key-value metadata for signals
    """
    __tablename__ = "signal_data"

    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey("signal.id"), nullable=False)
    key = Column(String(50), nullable=False)
    value = Column(String(200), nullable=False)

    signal = relationship("Signal")

    def __repr__(self):
        return f"<SignalData(id={self.id}, signal_id={self.signal_id}, key={self.key}, value={self.value})>"
