import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Configurações base da aplicação."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    
    # Caminho do banco de dados (absoluto para evitar erros de diretório)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'database', 'scada.db')
    
    # Configurações do Sistema SCADA
    MACHINES_COUNT = int(os.environ.get('MACHINES_COUNT', 10))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'system.log')
    PORT = int(os.environ.get('PORT', 5050))
