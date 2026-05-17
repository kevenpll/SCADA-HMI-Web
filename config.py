import os
from dotenv import load_dotenv

# Carrega variáveis do .env (apenas rodando local)
load_dotenv()

class Config:
    # Diretório Base
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Identifica ambiente Serverless (Vercel)
    IS_VERCEL = os.environ.get('VERCEL') == '1'
    
    # Caminhos seguros para banco e log (Vercel usa file-system Read-Only, exceto /tmp)
    if IS_VERCEL:
        LOG_FILE = '/tmp/system.log'
        DB_PATH = '/tmp/scada.db'
    else:
        LOG_FILE = os.path.join(BASE_DIR, 'logs', 'system.log')
        DB_PATH = os.path.join(BASE_DIR, 'database', 'scada.db')
        
    # Configurações do Sistema SCADA
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super_secret_industrial_key_2026')
    MACHINES_COUNT = int(os.environ.get('MACHINES_COUNT', 10))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    PORT = int(os.environ.get('PORT', 5050))
