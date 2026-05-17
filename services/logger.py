import logging
import os
from logging.handlers import RotatingFileHandler
from config import Config

def setup_logger(name='SCADA_System'):
    """
    Configura um logger rotativo profissional para uso corporativo.
    Registra os eventos tanto no console quanto em arquivo.
    """
    logger = logging.getLogger(name)
    
    # Evitar múltiplos handlers se chamado várias vezes
    if not logger.handlers:
        logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
        
        # Formato de log industrial
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File Handler (Garante que a pasta existe)
        log_dir = os.path.dirname(Config.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Log de 5MB, com backup de 3 arquivos
        file_handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

# Instância global para ser importada pelos outros módulos
sys_logger = setup_logger()
