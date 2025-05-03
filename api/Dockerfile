FROM python:3.9-slim

WORKDIR /app

# Instala dependências do sistema (úteis para psycopg2 e outras libs)
RUN apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Copia os arquivos antes de instalar as dependências
COPY requirements.txt .

# Instala as dependências do Python com base no requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY . .

# Comando para rodar a aplicação Flask
CMD ["python", "main.py"]
