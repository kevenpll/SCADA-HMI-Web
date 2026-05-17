// Configuração Global Chart.js (Tema Escuro e Tipografia)
Chart.defaults.color = '#71717a';
Chart.defaults.font.family = 'Inter';
Chart.defaults.scale.grid.color = '#27272a';

let plantChart;

// Inicializa Gráfico Agregador
function initPlantChart() {
    const ctx = document.getElementById('plantChart');
    if (!ctx) return;

    plantChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Temperatura Média Planta (°C)',
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.4, // Curva suave (Bézier)
                fill: true,
                data: []
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 }, // Para fluidez no real-time
            plugins: {
                legend: { display: false },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: { 
                    beginAtZero: false,
                    suggestedMin: 20,
                    suggestedMax: 200
                }
            }
        }
    });
}

// Cria/Atualiza cards no DOM baseados no template HTML
function updateMachinesGrid(machinesData) {
    const container = document.getElementById('machines-container');
    if (!container) return;

    // Se é a primeira vez e ainda tem skeleton loader, limpamos
    if (container.querySelector('.skeleton')) {
        container.innerHTML = '';
    }

    const template = document.getElementById('machine-card-template');

    // Array machinesData. Variavel global com objetos da máquina.
    machinesData.forEach(data => {
        // Tenta achar card existente
        let card = container.querySelector(`.machine-card[data-id="${data.id}"]`);
        
        // Cria se não existir
        if (!card) {
            const clone = template.content.cloneNode(true);
            card = clone.querySelector('.machine-card');
            card.dataset.id = data.id;
            card.querySelector('.name-text').innerText = data.name;
            container.appendChild(clone);
            // Atualiza ref local após append
            card = container.querySelector(`.machine-card[data-id="${data.id}"]`);
        }

        // Atualiza Valores Textuais
        card.querySelector('.temp-val').innerText = data.temperature.toFixed(1);
        card.querySelector('.press-val').innerText = data.pressure.toFixed(2);
        card.querySelector('.speed-val').innerText = Number(data.speed).toFixed(1);

        // Atualiza Status Badge
        const badge = card.querySelector('.mc-status');
        badge.className = `mc-status badge b-${data.status.toLowerCase()}`;
        badge.innerText = data.status;

        const getBarColor = (val, max_crit) => {
            return (val >= max_crit) ? 'var(--status-alarm)' : 'var(--color-primary)';
        };

        const type = data.name.split('_')[0];

        // Atualiza Barras de Progresso adaptativas por máquina
        const tempFill = card.querySelector('.temp-fill');
        let tempMax = (type === 'Extrusora') ? 250 : (type === 'Injetora') ? 150 : 60;
        let tempCrit = (type === 'Extrusora') ? 230 : (type === 'Injetora') ? 130 : 45;
        let tempPct = (data.temperature / tempMax) * 100;
        tempFill.style.width = `${Math.min(tempPct, 100)}%`;
        tempFill.style.backgroundColor = getBarColor(data.temperature, tempCrit);

        const pressFill = card.querySelector('.press-fill');
        let pressMax = (type === 'Injetora') ? 250 : 30;
        let pressCrit = (type === 'Injetora') ? 210 : 25;
        let pressPct = (data.pressure / pressMax) * 100;
        if(type === 'Misturador') pressPct = (data.pressure / 5) * 100; // Ajuste misturador
        pressFill.style.width = `${Math.min(pressPct, 100)}%`;
        pressFill.style.backgroundColor = getBarColor(data.pressure, pressCrit);

        const speedFill = card.querySelector('.speed-fill');
        let speedMax = (type === 'Misturador') ? 3500 : 300;
        let speedPct = (data.speed / speedMax) * 100;
        speedFill.style.width = `${Math.min(speedPct, 100)}%`;
        // Velocidade o critico é para baixo
        speedFill.style.backgroundColor = (data.status === 'OFFLINE') ? 'var(--status-offline)' : 'var(--color-primary)';

        // Atualiza Alarmes
        const alarmsContainer = card.querySelector('.alarms-container');
        alarmsContainer.innerHTML = '';
        if (data.alarms.length > 0) {
            data.alarms.forEach(alarm => {
                const tag = document.createElement('span');
                tag.className = 'alarm-tag';
                tag.innerHTML = `<i class="ph-fill ph-warning"></i> ${alarm}`;
                alarmsContainer.appendChild(tag);
            });
        }
    });
}

// Atualiza o gráfico agregado de planta
function updatePlantChart(machinesData) {
    if (!plantChart) return;

    // Calcula Média
    let totalTemp = 0;
    machinesData.forEach(m => totalTemp += m.temperature);
    let avgTemp = totalTemp / machinesData.length;

    const now = new Date();
    const timeLabel = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

    plantChart.data.labels.push(timeLabel);
    plantChart.data.datasets[0].data.push(avgTemp);

    if (plantChart.data.labels.length > 30) {
        plantChart.data.labels.shift();
        plantChart.data.datasets[0].data.shift();
    }

    plantChart.update();
}

// Controle de Conexão Frontend
function setConnectionState(isOnline) {
    const statusDiv = document.getElementById('server-connection');
    if (!statusDiv) return;

    if (isOnline) {
        statusDiv.style.color = 'var(--status-online)';
        statusDiv.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
        statusDiv.innerHTML = '<i class="ph-fill ph-wifi-high"></i> <span id="conn-text">Conectado ao Servidor PLC</span>';
    } else {
        statusDiv.style.color = 'var(--status-offline)';
        statusDiv.style.backgroundColor = 'rgba(82, 82, 91, 0.3)';
        statusDiv.innerHTML = '<i class="ph-fill ph-wifi-none"></i> <span id="conn-text">Falha de Conexão</span>';
    }
}

// Polling Core
async function fetchScadaState() {
    try {
        // Chama API de status all
        const response = await fetch('/api/status/all');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                setConnectionState(true);
                updateMachinesGrid(data.machines);
                updatePlantChart(data.machines);
            }
        } else {
            setConnectionState(false);
        }
    } catch (error) {
        console.error("Erro comunicação API:", error);
        setConnectionState(false);
    }
}

// Boot do frontend
document.addEventListener('DOMContentLoaded', () => {
    initPlantChart();
    
    // Inicia loop se estiver na tela correta
    if(document.getElementById('machines-container')) {
        fetchScadaState(); // primeira vez
        setInterval(fetchScadaState, 2000); // Poll a cada 2s
    }
});
