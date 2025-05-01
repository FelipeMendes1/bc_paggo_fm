import logging
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
from database import get_db
from models import Data
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Wind Power Data API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "api", "templates"))


@app.get("/health")
def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/data")
def get_data(
    start_date: datetime = Query(..., description="Start date in ISO format"),
    end_date: datetime = Query(..., description="End date in ISO format"),
    columns: Optional[str] = Query(None, description="Comma-separated list of columns to return (wind_speed, power, ambient_temperature)"),
    db: Session = Depends(get_db)
):
    """
    Get time series data with filtering capabilities
    """
    try:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
        # Parse requested columns
        requested_columns = []
        if columns:
            requested_columns = [col.strip() for col in columns.split(',')]
            valid_columns = ["wind_speed", "power", "ambient_temperature"]
            if not all(col in valid_columns for col in requested_columns):
                raise HTTPException(status_code=400, detail=f"Invalid column. Available columns: {', '.join(valid_columns)}")
        
        # Query data from database
        query = db.query(Data).filter(
            Data.timestamp >= start_date,
            Data.timestamp <= end_date
        ).order_by(Data.timestamp)
        
        # Get all data
        data_rows = query.all()
        
        if not data_rows:
            return {"data": [], "count": 0, "message": "No data found for the specified time range"}
        
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
        
        return {
            "data": result,
            "count": len(result),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error retrieving data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
