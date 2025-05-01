# dagster.Dockerfile
FROM python:3.9-slim

WORKDIR /opt/dagster/app

# Copia o código do projeto para dentro do container
COPY . .

# Instala dependências a partir do pyproject ou requirements
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt
