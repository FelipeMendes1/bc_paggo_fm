# ETL Wind Power - Solução Completa de ETL

Este projeto implementa uma solução completa de ETL (Extract, Transform, Load) para dados de energia eólica, usando PostgreSQL, Python, Flask e Dagster para orquestração.

## Visão Geral

O sistema coleta dados brutos de turbinas eólicas (velocidade do vento, potência gerada, temperatura ambiente), transforma-os calculando estatísticas em janelas de tempo de 10 minutos, e carrega os dados processados em um banco de dados de destino para análise.

![ETL Wind Power](/templates/static/img/dashboard.png)

## Componentes do Sistema

1. **Banco de Dados de Origem**: PostgreSQL contendo dados de série temporal com colunas:
   - timestamp
   - wind_speed (velocidade do vento em m/s)
   - power (potência gerada em kW)
   - ambient_temperature (temperatura ambiente em °C)

2. **Interface Web e API**: Aplicação Flask fornecendo acesso aos dados brutos e transformados com capacidades de filtragem

3. **Processo ETL**: Scripts Python que extraem dados do banco de origem, realizam transformações (agregações estatísticas) e carregam para o banco de destino

4. **Banco de Dados de Destino**: PostgreSQL com schema específico para armazenar dados transformados:
   - SignalType (tipos de sinais processados)
   - Signal (registros de sinais agregados)
   - SignalData (metadados adicionais)

5. **Orquestração Dagster**: Sistema de orquestração para agendamento de jobs ETL, monitoramento e recuperação de falhas

## Requisitos do Projeto

- Python 3.9+
- PostgreSQL
- Pacotes Python: 
  - Flask
  - Flask-SQLAlchemy
  - Gunicorn
  - HTTPX
  - NumPy
  - Pandas
  - Psycopg2-binary
  - SQLAlchemy
  - Email-validator
  - Dagster (opcional para orquestração)
- Docker e Docker Compose (opcional, para execução em contêineres)

## Como Iniciar

Este projeto oferece dois modos de execução:

### Modo Python (Replit ou Ambiente Local)

1. Clone o repositório
2. Instale as dependências:
   ```bash
   # Dependências principais
   pip install flask flask-sqlalchemy gunicorn httpx numpy pandas psycopg2-binary sqlalchemy email-validator
   
   # Opcional para Dagster
   pip install dagster dagit dagster-postgres dagster-docker
   ```
3. Execute o servidor Flask:
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```
4. Execute o ETL manualmente:
   ```bash
   python run_etl.py
   ```
5. Acesse o dashboard em: http://localhost:5000

### Modo Docker (Ambiente Local com Docker)

1. Clone o repositório
2. Execute usando Docker Compose:
   ```bash
   # Iniciar todos os serviços
   python run_etl.py --docker
   
   # Ou diretamente com Docker Compose
   docker-compose up -d
   ```
3. Acesse o dashboard em: http://localhost:5000
4. Acesse a interface Dagster em: http://localhost:3000
5. Para parar os serviços:
   ```bash
   python run_etl.py --docker --stop
   
   # Ou diretamente com Docker Compose
   docker-compose down
   ```

## Endpoints da API

- **GET /api/data**: Retorna dados brutos do banco de origem
  - Parâmetros: start_date, end_date, columns
  
- **GET /api/signals**: Retorna dados transformados do banco de destino
  - Parâmetros: start_date, end_date, signal_type
  
- **POST /api/run-etl**: Executa manualmente o processo ETL
  - Parâmetros: days (número de dias para processar)
  
- **POST /api/generate-data**: Gera novos dados aleatórios
  - Parâmetros: days, frequency

## Processo ETL

1. **Extração**: Dados brutos são extraídos do banco de origem com frequência de 1 minuto
2. **Transformação**: Dados são agregados em janelas de 10 minutos calculando:
   - Média (mean)
   - Mínimo (min)
   - Máximo (max)
   - Desvio padrão (std)
3. **Carregamento**: Dados transformados são armazenados no banco de destino como sinais categorizados

## Arquitetura de Microserviços

No modo Docker, o sistema opera como uma arquitetura de microserviços:

- **source_db**: Banco de dados PostgreSQL para dados de origem
- **target_db**: Banco de dados PostgreSQL para dados transformados
- **api**: Serviço FastAPI para acesso aos dados de origem
- **etl**: Serviço de processamento ETL
- **db_init**: Serviço para inicialização e geração de dados de exemplo
- **dagster-dagit**: Interface web Dagster para monitoramento
- **dagster-daemon**: Daemon Dagster para execução de jobs

## Documentação

Acesse a documentação completa em: http://localhost:5000/docs
