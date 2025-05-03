from extensions import db
from sqlalchemy import JSON
from datetime import datetime

class Data(db.Model):
    """
    Model for the time series data in the source database
    """
    __tablename__ = "data"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    wind_speed = db.Column(db.Float, nullable=False)
    power = db.Column(db.Float, nullable=False)
    ambient_temperature = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f"<Data(timestamp={self.timestamp}, wind_speed={self.wind_speed}, power={self.power}, temp={self.ambient_temperature})>"

class SignalType(db.Model):
    """
    Model for signal types in the target database
    """
    __tablename__ = "signal_type"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    # Relationship to signals
    signals = db.relationship("Signal", back_populates="signal_type")
    
    def __repr__(self):
        return f"<SignalType(id={self.id}, name={self.name})>"

class Signal(db.Model):
    """
    Model for the signal table in the target database
    """
    __tablename__ = "signal"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    data = db.Column(JSON, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    signal_id = db.Column(db.Integer, db.ForeignKey("signal_type.id"), nullable=False)
    value = db.Column(db.Float, nullable=False)
    
    # Relationship to signal type
    signal_type = db.relationship("SignalType", back_populates="signals")
    
    def __repr__(self):
        return f"<Signal(id={self.id}, name={self.name}, timestamp={self.timestamp}, value={self.value})>"

class SignalData(db.Model):
    """
    Model for additional signal data storage (if needed)
    """
    __tablename__ = "signal_data"
    
    id = db.Column(db.Integer, primary_key=True)
    signal_id = db.Column(db.Integer, db.ForeignKey("signal.id"), nullable=False)
    key = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(200), nullable=False)
    
    # Relationship to signal
    signal = db.relationship("Signal")
    
    def __repr__(self):
        return f"<SignalData(id={self.id}, signal_id={self.signal_id}, key={self.key}, value={self.value})>"
