from backend import create_app
from database.db_manager import db
from services.simulator import simulator
from services.logger import sys_logger
import os

# Inicializa App
app = create_app()

if __name__ == '__main__':
    # 1. Configura Banco de Dados antes de subir a rede
    sys_logger.info("Verificando integridade do banco de dados SQLite...")
    
    # Cria diretório do BD caso não exista (sanity check)
    db_dir = os.path.dirname(db.db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    db.init_db()
    
    # 2. Inicializa os serviços em Background (Simulador, possível cliente MQTT)
    simulator.start()
    
    # 3. Sobe o servidor web WSGI (Werkzeug para dev, recomendado Gunicorn para Prod)
    port = app.config.get('PORT', 5050)
    sys_logger.info(f"Iniciando servidor SCADA Web HMI na porta {port}...")
    app.run(host='0.0.0.0', port=port, debug=(app.config['FLASK_ENV'] == 'development'), use_reloader=False)
