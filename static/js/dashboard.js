// ==================== MENÚ HAMBURGUESA ====================
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            sidebarOverlay.classList.toggle('active');
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('active');
        });
    }

    // Cerrar menú al seleccionar una opción (en móvil)
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
                sidebarOverlay.classList.remove('active');
            }
        });
    });

    // ==================== NAVEGACIÓN ====================
    document.querySelectorAll('.nav-item[data-seccion]').forEach(item => {
        item.addEventListener('click', function() {
            const seccion = this.dataset.seccion;
            document.querySelectorAll('.nav-item[data-seccion]').forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            document.querySelectorAll('.seccion').forEach(sec => sec.classList.remove('active'));
            const target = document.getElementById(`seccion-${seccion}`);
            if (target) target.classList.add('active');
            
            const titles = {
                'dashboard': 'Dashboard de Satisfacción',
                'preguntas': 'Gestión de Preguntas',
                'qr': 'Códigos QR'
            };
            document.getElementById('titulo-seccion').textContent = titles[seccion] || seccion;
            
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
                sidebarOverlay.classList.remove('active');
            }
            
            localStorage.setItem('seccionActiva', seccion);
        });
    });

    // Restaurar sección activa
    const seccionGuardada = localStorage.getItem('seccionActiva');
    if (seccionGuardada && seccionGuardada !== 'dashboard') {
        const navItem = document.querySelector(`.nav-item[data-seccion="${seccionGuardada}"]`);
        if (navItem) navItem.click();
    }

    // ==================== INICIALIZAR GRÁFICOS ====================
    initializeCharts();

    // ==================== FORMULARIO PREGUNTA ====================
    const tipoSelect = document.getElementById('preguntaTipo');
    if (tipoSelect) {
        tipoSelect.addEventListener('change', function() {
            const container = document.getElementById('opcionesContainer');
            if (container) {
                container.style.display = this.value === 'seleccion' ? 'block' : 'none';
            }
        });
    }

    const formPregunta = document.getElementById('formPregunta');
    if (formPregunta) {
        formPregunta.onsubmit = async (e) => {
            e.preventDefault();
            const id = document.getElementById('preguntaId').value;
            const texto = document.getElementById('preguntaTexto').value.trim();
            const tipo = document.getElementById('preguntaTipo').value;
            const opciones = document.getElementById('preguntaOpciones').value;
            const orden = document.getElementById('preguntaOrden').value;
            const activa = document.getElementById('preguntaActiva').checked;
            
            if (!texto) return alert('Escribe el texto de la pregunta');
            if (tipo === 'seleccion' && !opciones.trim()) return alert('Agrega al menos una opción');
            
            const formData = new FormData();
            formData.append('texto', texto);
            formData.append('tipo', tipo);
            formData.append('opciones', opciones);
            formData.append('orden', orden);
            formData.append('activa', activa);
            
            const url = id ? `/pregunta/${id}/editar/` : '/pregunta/crear/';
            try {
                const res = await fetch(url, { 
                    method: 'POST', 
                    body: formData, 
                    headers: { 'X-CSRFToken': getCookie('csrftoken') } 
                });
                const data = await res.json();
                if (data.success) location.reload();
                else alert('Error: ' + (data.error || 'No se pudo guardar'));
            } catch (error) {
                alert('Error de conexión');
                console.error(error);
            }
        };
    }

    // ==================== FORMULARIO QR ====================
    const formQR = document.getElementById('formQR');
    if (formQR) {
        formQR.onsubmit = async (e) => {
            e.preventDefault();
            const nombre = document.getElementById('qrNombre').value.trim();
            if (!nombre) return alert('Escribe un nombre para el QR');
            
            const btn = document.getElementById('btnGenerarQR');
            btn.disabled = true;
            btn.textContent = 'Generando...';
            
            const formData = new FormData();
            formData.append('nombre', nombre);
            
            try {
                const res = await fetch('/generar-qr/', { 
                    method: 'POST', 
                    body: formData, 
                    headers: { 'X-CSRFToken': getCookie('csrftoken') } 
                });
                const data = await res.json();
                if (data.success) location.reload();
                else alert('Error: ' + (data.error || 'No se pudo generar el QR'));
            } catch (error) {
                alert('Error de conexión');
                console.error(error);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Generar QR';
            }
        };
    }

    // ==================== CERRAR MODALES ====================
    window.onclick = (e) => {
        const modalPregunta = document.getElementById('modalPregunta');
        const modalQR = document.getElementById('modalQR');
        if (e.target === modalPregunta) cerrarModalPregunta();
        if (e.target === modalQR) cerrarModalQR();
    };
});

// ==================== COOKIES ====================
function getCookie(name) {
    let value = "; " + document.cookie;
    let parts = value.split("; " + name + "=");
    if (parts.length === 2) return parts.pop().split(";").shift();
}

// En la función aplicarFiltros()
function aplicarFiltros() {
    const fechaDesde = document.getElementById('fecha_desde').value;
    const fechaHasta = document.getElementById('fecha_hasta').value;
    
    fetch(`/estadisticas-filtradas/?desde=${fechaDesde}&hasta=${fechaHasta}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Actualizar las estadísticas
                document.getElementById('total_encuestas').textContent = data.total_encuestas || data.respuestas_periodo;
                document.getElementById('total_respuestas').textContent = data.total_respuestas;
                document.getElementById('respuestas_periodo').textContent = data.respuestas_periodo;
                document.getElementById('promedio_general').textContent = data.promedio_general + '/5';
                
                if (window.trendChart) {
                    window.trendChart.data.labels = data.fechas;
                    window.trendChart.data.datasets[0].data = data.totales;
                    window.trendChart.update();
                }
                
                for (let i = 0; i < data.preguntas_stats.length; i++) {
                    const stat = data.preguntas_stats[i];
                    if (window.preguntaCharts && window.preguntaCharts[i]) {
                        if (stat.tipo === 'estrella') {
                            window.preguntaCharts[i].data.datasets[0].data = stat.distribucion;
                        } else if (stat.tipo === 'seleccion') {
                            const labels = Object.keys(stat.distribucion);
                            const values = Object.values(stat.distribucion);
                            window.preguntaCharts[i].data.labels = labels;
                            window.preguntaCharts[i].data.datasets[0].data = values;
                        }
                        window.preguntaCharts[i].update();
                    }
                }
            }
        })
        .catch(error => console.error('Error al aplicar filtros:', error));
}

function limpiarFiltros() {
    document.getElementById('fecha_desde').value = '';
    document.getElementById('fecha_hasta').value = '';
    aplicarFiltros();
}

// ==================== GRÁFICOS ====================
function initializeCharts() {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js no está cargado');
        return;
    }

    // Gráfico de evolución
    const trendCanvas = document.getElementById('trendChart');
    if (trendCanvas && window.fechasData && window.fechasData.length > 0) {
        const labels = window.fechasData.map(d => d.fecha);
        const totals = window.fechasData.map(d => d.total);
        
        window.trendChart = new Chart(trendCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Respuestas por día',
                    data: totals,
                    borderColor: '#ff6b00',
                    backgroundColor: 'rgba(255,107,0,0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    // Gráficos de preguntas
    if (window.preguntasStatsData && window.preguntasStatsData.length > 0) {
        window.preguntaCharts = {};
        
        window.preguntasStatsData.forEach((stat, index) => {
            const canvas = document.getElementById(`chart_${index + 1}`);
            if (!canvas) return;
            
            let chartLabels = [];
            let chartData = [];
            let backgroundColors = [];
            
            if (stat.tipo === 'estrella') {
                chartLabels = ['1★', '2★', '3★', '4★', '5★'];
                chartData = [
                    stat.distribucion['1'] || 0,
                    stat.distribucion['2'] || 0,
                    stat.distribucion['3'] || 0,
                    stat.distribucion['4'] || 0,
                    stat.distribucion['5'] || 0
                ];
                backgroundColors = ['#ff6b6b', '#f39c12', '#ffc107', '#2ecc71', '#3498db'];
            } else if (stat.tipo === 'seleccion') {
                chartLabels = Object.keys(stat.distribucion);
                chartData = Object.values(stat.distribucion);
                const colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c', '#e67e22', '#34495e'];
                backgroundColors = chartLabels.map((_, i) => colors[i % colors.length]);
            }
            
            if (chartLabels.length > 0 && chartData.length > 0) {
                window.preguntaCharts[index] = new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: chartLabels,
                        datasets: [{
                            label: 'Cantidad de respuestas',
                            data: chartData,
                            backgroundColor: backgroundColors.length > 0 ? backgroundColors : '#ff6b00',
                            borderRadius: 10
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { stepSize: 1 }
                            }
                        }
                    }
                });
            } else {
                canvas.parentElement.innerHTML = '<p style="text-align: center; color: #64748b; padding: 20px;">No hay datos para mostrar</p>';
            }
        });
    }
}

// ==================== PREGUNTAS ====================
function abrirModalPregunta() {
    document.getElementById('modalPreguntaTitulo').textContent = 'Nueva Pregunta';
    document.getElementById('preguntaId').value = '';
    document.getElementById('preguntaTexto').value = '';
    document.getElementById('preguntaTipo').value = 'estrella';
    document.getElementById('preguntaOpciones').value = '';
    document.getElementById('preguntaOrden').value = '0';
    document.getElementById('preguntaActiva').checked = true;
    document.getElementById('opcionesContainer').style.display = 'none';
    document.getElementById('modalPregunta').style.display = 'flex';
}

function cerrarModalPregunta() {
    document.getElementById('modalPregunta').style.display = 'none';
}

function editarPregunta(id) {
    fetch(`/pregunta/${id}/datos/`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('modalPreguntaTitulo').textContent = 'Editar Pregunta';
            document.getElementById('preguntaId').value = data.id;
            document.getElementById('preguntaTexto').value = data.texto;
            document.getElementById('preguntaTipo').value = data.tipo || 'estrella';
            document.getElementById('preguntaOpciones').value = data.opciones || '';
            document.getElementById('preguntaOrden').value = data.orden;
            document.getElementById('preguntaActiva').checked = data.activa;
            document.getElementById('opcionesContainer').style.display = data.tipo === 'seleccion' ? 'block' : 'none';
            document.getElementById('modalPregunta').style.display = 'flex';
        })
        .catch(error => console.error('Error al editar pregunta:', error));
}

function eliminarPregunta(id) {
    if (!confirm('¿Eliminar esta pregunta permanentemente?')) return;
    fetch(`/pregunta/${id}/eliminar/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => { 
        if (data.success) location.reload(); 
    })
    .catch(error => console.error('Error al eliminar pregunta:', error));
}

function toggleActiva(id, activaActual) {
    fetch(`/pregunta/${id}/toggle-activa/`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded', 
            'X-CSRFToken': getCookie('csrftoken') 
        },
        body: `activa=${!activaActual}`
    })
    .then(res => res.json())
    .then(data => { 
        if (data.success) location.reload(); 
    })
    .catch(error => console.error('Error al toggle activa:', error));
}

// ==================== QR ====================
function abrirModalQR() {
    document.getElementById('modalQR').style.display = 'flex';
    document.getElementById('qrNombre').value = '';
}

function cerrarModalQR() {
    document.getElementById('modalQR').style.display = 'none';
}

async function eliminarQR(id) {
    if (!confirm('¿Eliminar este código QR?')) return;
    try {
        const res = await fetch(`/eliminar-qr/${id}/`, { 
            method: 'POST', 
            headers: { 'X-CSRFToken': getCookie('csrftoken') } 
        });
        const data = await res.json();
        if (data.success) location.reload();
        else alert('Error al eliminar');
    } catch (error) {
        alert('Error de conexión');
        console.error(error);
    }
}