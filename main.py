import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

def create_app():
    app = Flask(__name__, template_folder='templates')
    from models import SignalType
    from models import Data, Signal

    app = Flask(__name__, template_folder='templates')  # ✅
    app.secret_key = os.environ.get("SESSION_SECRET", "development_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

    db.init_app(app)

    with app.app_context():
        db.create_all()
        if not db.session.query(SignalType).first():
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
            db.session.add_all(default_signal_types)
            db.session.commit()
            logger.info("Default signal types initialized")

    from models import Data, Signal, SignalType

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/docs')
    def docs():
        return render_template('docs.html')

    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(),
            "component": "ETL Dashboard"
        })
    
    @app.route('/api/data')
    def get_data():
        """
        API endpoint to get data with date range filtering
        """
        try:
            # Get query parameters
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            columns = request.args.get('columns')
            
            # Default to last 24 hours if no dates provided
            if not start_date_str:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=1)
            else:
                # Parse dates
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str) if end_date_str else datetime.now()
            
            # Validate date range
            if start_date > end_date:
                return jsonify({
                    "error": "Start date must be before end date"
                }), 400
            
            # Parse requested columns
            requested_columns = []
            if columns:
                requested_columns = [col.strip() for col in columns.split(',')]
                valid_columns = ["wind_speed", "power", "ambient_temperature"]
                if not all(col in valid_columns for col in requested_columns):
                    return jsonify({
                        "error": f"Invalid column. Available columns: {', '.join(valid_columns)}"
                    }), 400
            
            # Query data from database
            query = Data.query.filter(
                Data.timestamp >= start_date,
                Data.timestamp <= end_date
            ).order_by(Data.timestamp)
            
            # Get all data
            data_rows = query.all()
            
            if not data_rows:
                return jsonify({
                    "data": [], 
                    "count": 0, 
                    "message": "No data found for the specified time range"
                })
            
            # Convert to dictionary format
            result = []
            for row in data_rows:
                row_dict = {
                    "timestamp": row.timestamp.isoformat(),
                }
                
                # Add requested columns or all columns if none specified
                if not requested_columns or "wind_speed" in requested_columns:
                    row_dict["wind_speed"] = row.wind_speed
                if not requested_columns or "power" in requested_columns:
                    row_dict["power"] = row.power
                if not requested_columns or "ambient_temperature" in requested_columns:
                    row_dict["ambient_temperature"] = row.ambient_temperature
                
                result.append(row_dict)
            
            return jsonify({
                "data": result,
                "count": len(result),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error retrieving data: {str(e)}")
            return jsonify({
                "error": f"Internal server error: {str(e)}"
            }), 500

    @app.route('/api/signals')
    def get_signals():
        """
        API endpoint to get transformed signal data
        """
        try:
            # Get query parameters
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            signal_type = request.args.get('signal_type')
            
            # Default to last 24 hours if no dates provided
            if not start_date_str:
                end_date = datetime.now()
                start_date = end_date - timedelta(hours=24)
            else:
                # Parse dates
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str) if end_date_str else datetime.now()
            
            # Base query
            query = Signal.query.filter(
                Signal.timestamp >= start_date,
                Signal.timestamp <= end_date
            )
            
            # Filter by signal type if provided
            if signal_type:
                # Get signal type ID by name
                signal_type_obj = SignalType.query.filter_by(name=signal_type).first()
                if not signal_type_obj:
                    return jsonify({
                        "error": "Invalid signal type"
                    }), 400
                
                query = query.filter(Signal.signal_id == signal_type_obj.id)
            
            # Execute query
            signals = query.order_by(Signal.timestamp).all()
            
            if not signals:
                return jsonify({
                    "data": [], 
                    "count": 0, 
                    "message": "No signals found for the specified criteria"
                })
            
            # Convert to dictionary format
            result = []
            for signal in signals:
                # Get signal type name
                signal_type_name = SignalType.query.get(signal.signal_id).name
                
                signal_dict = {
                    "id": signal.id,
                    "name": signal.name,
                    "timestamp": signal.timestamp.isoformat(),
                    "value": signal.value,
                    "signal_type": signal_type_name
                }
                
                # Add data JSON if present
                if signal.data:
                    signal_dict["data"] = signal.data
                
                result.append(signal_dict)
            
            return jsonify({
                "data": result,
                "count": len(result),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error retrieving signals: {str(e)}")
            return jsonify({
                "error": f"Internal server error: {str(e)}"
            }), 500
    @app.route('/api/generate-data', methods=['POST'])
    def generate_data():
        try:
            data = request.get_json() or {}
            days = data.get('days', 3)
            frequency = data.get('frequency', '1min')

            days = min(max(1, days), 30)
            valid_frequencies = ['1min', '5min', '10min']
            if frequency not in valid_frequencies:
                frequency = '1min'

            start_date = datetime.now() - timedelta(days=days)

            with current_app.app_context():
                from init_db import generate_random_data
                df = generate_random_data(start_date, days=days, frequency=frequency)

                # salvar no banco
                from models import Data, db
                record_count = 0
                if not df.empty:
                    for _, row in df.iterrows():
                        record = Data(
                            timestamp=row['timestamp'],
                            wind_speed=row['wind_speed'],
                            power=row['power'],
                            ambient_temperature=row['ambient_temperature']
                        )
                        db.session.add(record)
                        record_count += 1

                    db.session.commit()

            return jsonify({
                "status": "success",
                "message": f"Generated {record_count} data points with {frequency} frequency",
                "record_count": record_count,
                "days": days,
                "frequency": frequency,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error generating data: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Error generating data: {str(e)}"
            }), 500
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)

