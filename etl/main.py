import logging
import sys
from datetime import datetime, timedelta
from transform import process_data_for_date
from database import init_target_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    # Initialize target database if needed
    init_target_db()
    
    # Get date to process from command line argument or use yesterday
    if len(sys.argv) > 1:
        try:
            process_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        except ValueError:
            logger.error("Invalid date format. Please use YYYY-MM-DD")
            sys.exit(1)
    else:
        process_date = (datetime.now() - timedelta(days=1)).date()
    
    logger.info(f"Processing data for date: {process_date}")
    
    # Process data for the specified date
    result = process_data_for_date(process_date)
    
    logger.info(f"ETL process completed: {result['processed']} records processed, {result['loaded']} records loaded")
    
    return result

if __name__ == "__main__":
    main()
