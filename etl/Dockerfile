FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
  sqlalchemy \
  psycopg2-binary \
  pandas \
  httpx \
  numpy \
  dagster \
  dagit\
  flask_sqlalchemy\
  flask

# Copy application files
COPY . .

# Command to run the ETL process
CMD ["python", "main.py"]
