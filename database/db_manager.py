import sqlite3
from datetime import datetime
from config import Config
from services.logger import sys_logger

class DatabaseManager:
    """
    Gerenciador de Conexão com o Banco de Dados SQLite.
    Suporta o armazenamento de múltiplas máquinas simultaneamente.
    """
    def __init__(self, db_path=Config.DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        """Retorna uma conexão Thread-Safe."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Inicializa o Schema do banco de dados."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tabela atualizada para suportar múltiplas máquinas (machine_id)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    machine_id INTEGER NOT NULL,
                    temperature REAL,
                    pressure REAL,
                    speed REAL,
                    status TEXT,
                    is_alarm INTEGER DEFAULT 0
                )
            ''')
            
            # Cria um índice para otimizar a busca por máquina e timestamp (para gráficos)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_machine_time ON sensor_logs(machine_id, timestamp)')
            
            conn.commit()
            sys_logger.info("Banco de dados inicializado com sucesso.")
        except Exception as e:
            sys_logger.error(f"Erro ao inicializar o banco de dados: {str(e)}")
        finally:
            conn.close()

    def insert_log(self, machine_id, temp, pressure, speed, status, is_alarm):
        """Grava a leitura de uma máquina no banco."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO sensor_logs (timestamp, machine_id, temperature, pressure, speed, status, is_alarm)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, machine_id, temp, pressure, speed, status, is_alarm))
            
            conn.commit()
        except Exception as e:
            sys_logger.error(f"Erro ao inserir log para Máquina {machine_id}: {str(e)}")
        finally:
            conn.close()

    def get_recent_logs(self, limit=100, machine_id=None):
        """
        Retorna as últimas leituras para o histórico.
        Se machine_id for fornecido, filtra por máquina.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if machine_id is not None:
                cursor.execute('''
                    SELECT * FROM sensor_logs 
                    WHERE machine_id = ? 
                    ORDER BY id DESC LIMIT ?
                ''', (machine_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM sensor_logs 
                    ORDER BY id DESC LIMIT ?
                ''', (limit,))
                
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            sys_logger.error(f"Erro ao buscar histórico: {str(e)}")
            return []
        finally:
            conn.close()

# Instância Singleton do gerenciador
db = DatabaseManager()
