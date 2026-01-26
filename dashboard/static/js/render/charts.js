export function renderHistogram(data) {
    const canvas = document.getElementById('histogramChart');
    const statsEl = document.getElementById('analyticsStats');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    // Ajustar tamaño al contenedor
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = canvas.parentElement.clientHeight;

    const distribution = data.stats.today_stats.results_distribution || {};

    // Limpiar canvas
    ctx.fillStyle = '#0a0a12';
    ctx.fillRect(0, 0, width, height);

    // Datos a mostrar ordenados
    const categories = ['1', '2', '5', '10', 'Pachinko', 'CashHunt', 'CoinFlip', 'CrazyTime'];
    const labels = ['1', '2', '5', '10', 'PK', 'CH', 'CF', 'CT'];
    
    const values = categories.map(cat => distribution[cat] || 0);
    const maxValue = Math.max(...values, 10); // Escala mínima de 10

    // Configuración de Gráfico
    const padding = { top: 30, right: 20, bottom: 30, left: 40 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;
    const barWidth = (chartW / categories.length) - 10;

    // Colores por categoría
    const colors = {
        '1': '#4299e1', // Azul
        '2': '#ecc94b', // Amarillo
        '5': '#ed64a6', // Rosa
        '10': '#9f7aea', // Morado
        'Pachinko': '#d53f8c',
        'CashHunt': '#38a169',
        'CoinFlip': '#e53e3e',
        'CrazyTime': '#f56565'
    };

    // Dibujar Ejes
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;

    // Líneas horizontales
    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartH / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();

        // Etiquetas Y
        ctx.fillStyle = '#718096';
        ctx.font = '10px Rajdhani';
        ctx.textAlign = 'right';
        const val = Math.round(maxValue * (1 - i / 5));
        ctx.fillText(val, padding.left - 5, y + 3);
    }

    // Dibujar Barras
    categories.forEach((cat, i) => {
        const val = distribution[cat] || 0;
        if (val === 0) return; // No dibujar barras vacías

        const barH = (val / maxValue) * chartH;
        const x = padding.left + (chartW / categories.length) * i + 5;
        const y = padding.top + chartH - barH;
        
        const color = colors[cat] || '#cbd5e0';

        // Barra
        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = 10; // Efecto Neón
        ctx.fillRect(x, y, barWidth, barH);
        
        ctx.shadowBlur = 0; // Reset sombra

        // Valor encima de la barra
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'center';
        ctx.font = 'bold 12px Rajdhani';
        ctx.fillText(val, x + barWidth / 2, y - 5);

        // Etiqueta X (Abajo)
        ctx.fillStyle = '#a0aec0';
        ctx.font = '11px Rajdhani';
        ctx.fillText(labels[i], x + barWidth / 2, height - 10);
    });

    // Actualizar Texto de Estadísticas (AnalyticsStats)
    if (statsEl) {
        const total = values.reduce((a, b) => a + b, 0);
        // Mostrar top 3 resultados más frecuentes
        const sorted = [...categories].sort((a, b) => (distribution[b] || 0) - (distribution[a] || 0));
        
        statsEl.innerHTML = `
            <div class="analytic-stat">
                <span class="stat-label">MÁS FRECUENTE</span>
                <span class="stat-value" style="color: ${colors[sorted[0]]}">${sorted[0]} (${distribution[sorted[0]] || 0})</span>
            </div>
            <div class="analytic-stat">
                <span class="stat-label">MENOS FRECUENTE</span>
                <span class="stat-value" style="color: ${colors[sorted[7]]}">${sorted[7]} (${distribution[sorted[7]] || 0})</span>
            </div>
        `;
    }
}