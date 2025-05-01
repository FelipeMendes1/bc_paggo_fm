FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir sqlalchemy psycopg2-binary pandas numpy

# Copy application files
COPY . .

# Command to run the initialization scripts
CMD ["python", "-c", "import init_source_db; import init_target_db; init_source_db.main(); init_target_db.main()"]
