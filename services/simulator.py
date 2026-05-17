import threading
import time
import random
from config import Config
from database.db_manager import db
from services.logger import sys_logger

class SimulatorService:
    """
    Serviço Corporativo de Simulação Industrial.
    Gerencia e atualiza o estado de N máquinas simultaneamente com perfis realistas.
    """
    def __init__(self, num_machines=Config.MACHINES_COUNT):
        self.num_machines = num_machines
        self.running = False
        self.machines = {}
        
        # Inicializa as máquinas com perfis físicos diferentes e valores aleatórios na faixa
        for i in range(1, num_machines + 1):
            if i <= 6:
                m_type = 'EXTRUSORA'
                name = f'Extrusora_{i:02d}'
                t = round(random.uniform(180.0, 210.0), 1)
                p = round(random.uniform(10.0, 20.0), 2)
                s = random.randint(120, 180)
            elif i <= 8:
                m_type = 'INJETORA'
                name = f'Injetora_{i-6:02d}'
                t = round(random.uniform(80.0, 120.0), 1)
                p = round(random.uniform(150.0, 200.0), 2)
                s = random.choice([0, 10, 20, 30])
            else:
                m_type = 'MISTURADOR'
                name = f'Misturador_{i-8:02d}'
                t = round(random.uniform(25.0, 40.0), 1)
                p = round(random.uniform(1.0, 2.5), 2)
                s = random.randint(1500, 2500)
                
            self.machines[i] = {
                'id': i,
                'name': name,
                'type': m_type,
                'temperature': t,
                'pressure': p,
                'speed': s,
                'status': 'ONLINE',
                'alarms': [],
                'is_stopped': False,
                'stop_counter': 0
            }
            
    def start(self):
        """Inicia a thread do simulador."""
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._run_loop, daemon=True)
            thread.start()
            sys_logger.info(f"Simulador industrial iniciado com {self.num_machines} máquinas (Perfis Variados).")
            
    def stop(self):
        self.running = False

    def get_all_states(self):
        return self.machines

    def _run_loop(self):
        while self.running:
            try:
                for machine_id, state in self.machines.items():
                    self._update_machine(state)
            except Exception as e:
                sys_logger.error(f"Erro no loop de simulação: {str(e)}")
            time.sleep(2)

    def _update_machine(self, state):
        """Lógica de simulação estabilizada (Mean Reversion) e paradas."""
        
        # 1. Gerenciamento de Paradas (OFFLINE / Manutenção)
        if state['is_stopped']:
            state['stop_counter'] -= 1
            state['temperature'] = max(25.0, state['temperature'] - 2.0) # Resfriando
            state['pressure'] = max(0.0, state['pressure'] - 1.0) # Perdendo pressão
            state['speed'] = 0
            state['status'] = 'OFFLINE'
            state['alarms'] = ['Máquina em Manutenção']
            
            if state['stop_counter'] <= 0:
                state['is_stopped'] = False # Terminou a manutenção
                state['status'] = 'ONLINE'
                state['alarms'] = []
                
            self._save_log(state, is_alarm=0)
            return

        # 2% de chance da máquina parar do nada (simulando falha grave/manutenção)
        if random.random() < 0.02:
            state['is_stopped'] = True
            state['stop_counter'] = random.randint(10, 20) # Fica parada de 10 a 20 ciclos
            return

        # 2. Algoritmo de Mean Reversion (mantém os valores estáveis na maioria do tempo)
        def get_next_val(current, ideal, max_diff, min_limit, max_limit):
            # O "pull" puxa o valor de volta para o ideal, evitando que ele fuja muito e alarme o tempo todo
            pull = (ideal - current) * 0.1 
            diff = random.uniform(-max_diff, max_diff) + pull
            return max(min_limit, min(max_limit, current + diff))

        m_type = state['type']
        alarms = []
        is_alarm = 0
        
        # Perfil: EXTRUSORA
        if m_type == 'EXTRUSORA':
            state['temperature'] = get_next_val(state['temperature'], 195.0, 3.0, 150.0, 240.0)
            state['pressure'] = get_next_val(state['pressure'], 15.0, 0.5, 5.0, 25.0)
            state['speed'] = get_next_val(state['speed'], 150.0, 10.0, 80.0, 220.0)
            
            if state['temperature'] > 225.0: alarms.append('Extrusora: Alta Temperatura'); is_alarm = 1
            if state['speed'] < 100: alarms.append('Extrusora: Obstrução Detectada'); is_alarm = 1

        # Perfil: INJETORA
        elif m_type == 'INJETORA':
            state['temperature'] = get_next_val(state['temperature'], 100.0, 2.0, 50.0, 140.0)
            state['pressure'] = get_next_val(state['pressure'], 180.0, 5.0, 100.0, 220.0)
            state['speed'] = random.choice([0, 0, 10, 20])
            
            if state['pressure'] < 120.0: alarms.append('Injetora: Perda de Pressão Hidráulica'); is_alarm = 1
            if state['pressure'] > 210.0: alarms.append('Injetora: Sobrepressão'); is_alarm = 1

        # Perfil: MISTURADOR
        elif m_type == 'MISTURADOR':
            state['temperature'] = get_next_val(state['temperature'], 35.0, 1.0, 20.0, 60.0)
            state['pressure'] = get_next_val(state['pressure'], 1.5, 0.2, 0.5, 3.0)
            state['speed'] = get_next_val(state['speed'], 2000.0, 50.0, 1000.0, 3000.0)
            
            if state['speed'] < 1500: alarms.append('Misturador: Travamento do Rotor'); is_alarm = 1
            if state['temperature'] > 45.0: alarms.append('Misturador: Fricção Alta'); is_alarm = 1

        # 3. Injeção de Falhas Raras (1% de chance de forçar um pico para alarmar a máquina)
        if random.random() < 0.01:
            if m_type == 'EXTRUSORA': state['temperature'] = 230.0
            elif m_type == 'INJETORA': state['pressure'] = 110.0
            elif m_type == 'MISTURADOR': state['speed'] = 1200.0

        # 4. Atualiza Status (apenas se a máquina não estiver OFFLINE)
        state['alarms'] = alarms
        if is_alarm:
            state['status'] = 'ALARM'
        else:
            if random.random() < 0.05:
                state['status'] = 'WARNING'
            else:
                state['status'] = 'ONLINE'
                
        self._save_log(state, is_alarm)

    def _save_log(self, state, is_alarm):
        """Persiste no banco de dados."""
        db.insert_log(
            machine_id=state['id'],
            temp=state['temperature'],
            pressure=state['pressure'],
            speed=state['speed'],
            status=state['status'],
            is_alarm=is_alarm
        )

simulator = SimulatorService()
