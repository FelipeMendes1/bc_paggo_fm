FROM python:3.10-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia todos os arquivos da raiz
COPY . .

# Instala as dependências
#RUN pip install flask pandas sqlalchemy psycopg2-binary sqlalchemy

RUN pip install -r requirements.txt

# Expõe a porta
EXPOSE 8000

# Comando para rodar a aplicação Flask
CMD ["python", "main.py"]
