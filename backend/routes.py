import csv
from flask import Blueprint, render_template, jsonify, Response, request, session, redirect, url_for
from services.simulator import simulator
from database.db_manager import db
from services.logger import sys_logger

routes_bp = Blueprint('routes', __name__)

# Middleware de Segurança para Frontend
@routes_bp.before_request
def require_auth():
    if request.path.startswith('/api/') and 'Authorization' in request.headers:
        pass
    
    # Proteção simples baseada em sessão para as views
    public_routes = ['routes.login', 'static']
    if request.endpoint not in public_routes and 'logged_in' not in session:
        return redirect(url_for('routes.login'))

# --- VIEWS (Frontend Render) ---

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            sys_logger.info("Admin realizou login com sucesso.")
            return redirect(url_for('routes.dashboard'))
        else:
            error = 'Acesso Negado.'
            sys_logger.warning("Tentativa de login falha.")
    return render_template('login.html', error=error)

@routes_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('routes.login'))

@routes_bp.route('/')
def dashboard():
    return render_template('dashboard.html', num_machines=simulator.num_machines)

@routes_bp.route('/history')
def history():
    # Carrega histórico da primeira máquina por padrão para não pesar
    logs = db.get_recent_logs(limit=200)
    return render_template('history.html', logs=logs)

@routes_bp.route('/alarms')
def alarms():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM sensor_logs 
            WHERE is_alarm = 1 
            ORDER BY id DESC LIMIT 100
        ''')
        alarm_logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        sys_logger.error(f"Erro ao buscar alarmes: {e}")
        alarm_logs = []
        
    return render_template('alarms.html', logs=alarm_logs)

# --- APIs REST Industriais ---

@routes_bp.route('/api/status/all')
def get_all_status():
    """Retorna o estado de todas as máquinas cadastradas no SCADA."""
    try:
        return jsonify({
            'success': True,
            'machines': list(simulator.get_all_states().values())
        })
    except Exception as e:
        sys_logger.error(f"Erro ao servir API de status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@routes_bp.route('/api/status/machine/<int:machine_id>')
def get_machine_status(machine_id):
    """Retorna o estado de uma máquina específica."""
    states = simulator.get_all_states()
    if machine_id in states:
        return jsonify({'success': True, 'data': states[machine_id]})
    return jsonify({'success': False, 'error': 'Máquina não encontrada'}), 404

@routes_bp.route('/api/export')
def export_csv():
    """Serviço de Exportação Profissional (Relatório de Big Data)."""
    try:
        logs = db.get_recent_logs(limit=1000) # Limite para não sobrecarregar a RAM
        
        def generate():
            yield 'ID,Timestamp,MachineID,Temperature,Pressure,Speed,Status,IsAlarm\n'
            for log in logs:
                yield f"{log['id']},{log['timestamp']},{log['machine_id']},{log['temperature']},{log['pressure']},{log['speed']},{log['status']},{log['is_alarm']}\n"

        headers = {
            'Content-Disposition': 'attachment; filename=scada_report.csv',
            'Content-Type': 'text/csv'
        }
        sys_logger.info("Relatório CSV gerado e exportado.")
        return Response(generate(), headers=headers)
    except Exception as e:
        sys_logger.error(f"Falha na exportação CSV: {e}")
        return jsonify({'error': 'Falha interna na exportação'}), 500
