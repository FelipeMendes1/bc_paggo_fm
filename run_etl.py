"""
ETL Runner - Executa o processo ETL completo
Suporta execução em ambiente Replit (modo Python) e com Docker Compose em outros ambientes

Modo de uso:
1. Ambiente Replit: python run_etl.py
2. Ambiente Docker: python run_etl.py --docker
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Adaptações para o ambiente Replit
# Em vez de fazer imports diretos dos módulos de ETL,
# vamos usar funções definidas diretamente aqui
from init_db import generate_random_data, process_etl_data

def run_data_generation():
    """
    Simula a geração de dados que seria feita pelo serviço db_init
    """
    try:
        from main import app
        
        with app.app_context():
            from models import Data
            
            # Verifica se já existem dados
            if Data.query.count() > 0:
                logger.info("Dados já existem no banco de dados de origem. Pulando geração.")
                return
            
            # Gera dados para os últimos 10 dias
            logger.info("Gerando dados para o banco de dados de origem...")
            start_date = datetime.now() - timedelta(days=10)
            df = generate_random_data(start_date, days=10, frequency='1min')
            
            # Insere dados no banco de dados
            from main import db
            for _, row in df.iterrows():
                data = Data(
                    timestamp=row['timestamp'],
                    wind_speed=row['wind_speed'],
                    power=row['power'],
                    ambient_temperature=row['ambient_temperature']
                )
                db.session.add(data)
            
            db.session.commit()
            logger.info(f"Gerados {len(df)} registros de dados para o banco de origem")
    except Exception as e:
        logger.error(f"Erro na geração de dados: {str(e)}")
        return False
    
    return True

def run_etl_process(days=1):
    """
    Executa o processo ETL para os últimos 'days' dias
    Simula os serviços de ETL e Dagster jobs
    
    Usa a função process_etl_data de init_db.py que já contém toda a lógica
    """
    try:
        logger.info(f"Executando processo ETL para os últimos {days} dias...")
        
        # Usa a função ETL já definida no arquivo init_db.py
        from main import app
        
        with app.app_context():
            for day in range(days):
                process_date = datetime.now().date() - timedelta(days=day)
                logger.info(f"Processando dados para a data: {process_date}")
                
                records_processed = process_etl_data(days=1)
                
                if records_processed > 0:
                    logger.info(f"Processados {records_processed} registros para a data {process_date}")
                else:
                    logger.warning(f"Nenhum registro processado para a data {process_date}")
        
        return True
    
    except Exception as e:
        logger.error(f"Erro no processo ETL: {str(e)}")
        return False

def run_dagster_process():
    """
    Simula a execução do Dagster usando as definições criadas
    """
    try:
        logger.info("Configurando ambiente Dagster...")
        os.environ["DAGSTER_HOME"] = "./dagster_home"
        
        # Como o Dagster pode não estar disponível no ambiente Replit,
        # vamos simular a execução do job
        logger.info("Simulando job Dagster ETL...")
        
        # Usar process_etl_data novamente para processar o dia anterior
        from main import app
        
        with app.app_context():
            # Processar o dia anterior
            yesterday = datetime.now() - timedelta(days=1)
            logger.info(f"Simulando job Dagster para a data: {yesterday.date()}")
            
            # Executa ETL para o dia anterior
            records_processed = process_etl_data(days=1)
            
            if records_processed > 0:
                logger.info(f"Job Dagster: processados {records_processed} registros")
                return True
            else:
                logger.warning("Job Dagster: nenhum registro processado")
                return False
    
    except Exception as e:
        logger.error(f"Erro na execução do Dagster: {str(e)}")
        return False

def run_complete_etl_pipeline():
    """
    Executa todo o pipeline ETL em ordem
    """
    logger.info("Iniciando pipeline ETL completo...")
    
    # 1. Geração de dados
    logger.info("=== ETAPA 1: GERAÇÃO DE DADOS ===")
    if not run_data_generation():
        logger.error("Falha na geração de dados. Continuando mesmo assim...")
    
    # 2. Processo ETL básico
    logger.info("=== ETAPA 2: PROCESSAMENTO ETL ===")
    if not run_etl_process(days=3):
        logger.error("Falha no processo ETL básico")
        return False
    
    # 3. Processo Dagster (orquestração)
    logger.info("=== ETAPA 3: ORQUESTRAÇÃO DAGSTER ===")
    if not run_dagster_process():
        logger.error("Falha no processo Dagster")
        return False
    
    logger.info("Pipeline ETL completo executado com sucesso!")
    return True

def run_docker_compose():
    """
    Executa o ETL usando Docker Compose
    """
    try:
        logger.info("Iniciando serviços Docker Compose...")
        
        # Executar docker-compose up
        import subprocess
        
        # Primeiro, verifica se o Docker Compose está instalado
        try:
            subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Docker Compose não está instalado ou não está no PATH.")
            return False
        
        # Iniciar serviços em segundo plano
        logger.info("Iniciando serviços com docker-compose up -d...")
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            check=False,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Erro ao iniciar Docker Compose: {result.stderr}")
            return False
        
        logger.info("Serviços Docker Compose iniciados com sucesso")
        
        # Aguardar inicialização dos serviços
        logger.info("Aguardando inicialização dos serviços (30 segundos)...")
        import time
        time.sleep(30)
        
        # Verificar saúde dos serviços
        logger.info("Verificando saúde da API...")
        health_check = subprocess.run(
            ["curl", "http://localhost:8000/health"],
            check=False,
            capture_output=True,
            text=True
        )
        
        if health_check.returncode != 0:
            logger.warning(f"Aviso: API pode não estar disponível: {health_check.stderr}")
        else:
            logger.info(f"API respondeu: {health_check.stdout}")
        
        # Verificar logs dos serviços (opcional)
        logger.info("Obtendo logs dos serviços...")
        logs = subprocess.run(
            ["docker-compose", "logs", "--tail=10"],
            check=False,
            capture_output=True,
            text=True
        )
        
        if logs.returncode == 0:
            logger.info("Últimos logs dos serviços:")
            for line in logs.stdout.splitlines()[-10:]:
                logger.info(f"  {line}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao executar Docker Compose: {str(e)}")
        return False

def stop_docker_compose():
    """
    Para os serviços Docker Compose
    """
    try:
        logger.info("Parando serviços Docker Compose...")
        import subprocess
        
        result = subprocess.run(
            ["docker-compose", "down"],
            check=False,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.warning(f"Aviso ao parar Docker Compose: {result.stderr}")
        else:
            logger.info("Serviços Docker Compose parados com sucesso")
        
        return True
    
    except Exception as e:
        logger.error(f"Erro ao parar Docker Compose: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ETL Runner - Executa o processo ETL completo')
    parser.add_argument('--docker', action='store_true', help='Executa o ETL usando Docker Compose')
    parser.add_argument('--stop', action='store_true', help='Para os serviços Docker Compose')
    args = parser.parse_args()
    
    if args.docker:
        if args.stop:
            stop_docker_compose()
        else:
            run_docker_compose()
    else:
        # Execução padrão usando Python
        run_complete_etl_pipeline()