from flask import Flask
from config import Config
from backend.routes import routes_bp
from backend.errors import errors_bp
from services.logger import sys_logger

def create_app():
    """Application Factory Pattern para o SCADA Web."""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Carrega configurações
    app.config.from_object(Config)
    
    # Registra Blueprints (Módulos)
    app.register_blueprint(routes_bp)
    app.register_blueprint(errors_bp)
    
    sys_logger.info(f"Instância do Flask criada no modo {Config.FLASK_ENV}")
    return app
