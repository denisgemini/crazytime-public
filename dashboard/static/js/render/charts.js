export function renderHistogram(data) {
    const canvas = document.getElementById('histogramChart');
    const statsEl = document.getElementById('analyticsStats');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    // Ajustar tamaño al contenedor
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = canvas.parentElement.clientHeight;

    const distribution = data.stats.today_stats.results_distribution || {};
    const sequences = data.stats.today_stats.sequences || {};

    // Limpiar canvas
    ctx.fillStyle = '#0a0a12';
    ctx.fillRect(0, 0, width, height);

    // Configuración de categorías: 10 barras (Números + Bonus Individuales + Secuencias)
    const categories = ['1', '2', '5', '10', 'Pachinko', 'CashHunt', 'CoinFlip', 'CrazyTime', '2-5', '5-2'];
    const labels = ['1', '2', '5', '10', 'PK', 'CH', 'CF', 'CT', '2→5', '5→2'];
    
    // Mapeo de valores
    const valuesMap = {
        '1': distribution['1'] || 0,
        '2': distribution['2'] || 0,
        '5': distribution['5'] || 0,
        '10': distribution['10'] || 0,
        'Pachinko': distribution['Pachinko'] || 0,
        'CashHunt': distribution['CashHunt'] || 0,
        'CoinFlip': distribution['CoinFlip'] || 0,
        'CrazyTime': distribution['CrazyTime'] || 0,
        '2-5': sequences['2-5'] || 0,
        '5-2': sequences['5-2'] || 0
    };
    
    const values = categories.map(cat => valuesMap[cat]);
    const maxValue = Math.max(...values, 10); 

    // Configuración de Gráfico
    const padding = { top: 30, right: 20, bottom: 30, left: 40 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;
    const barWidth = (chartW / categories.length) - 8; // Ajustado para 10 barras

    // Colores Neón
    const colors = {
        '1': '#4299e1', 
        '2': '#ecc94b', 
        '5': '#ed64a6', 
        '10': '#9f7aea', 
        'Pachinko': '#d53f8c', // Magenta Oscuro
        'CashHunt': '#38a169', // Verde Bosque
        'CoinFlip': '#e53e3e', // Rojo
        'CrazyTime': '#f56565', // Rojo Claro
        '2-5': '#00ff88',      // Esmeralda
        '5-2': '#00d4ff'       // Cyan
    };

    // Dibujar Ejes
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;

    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartH / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();

        ctx.fillStyle = '#718096';
        ctx.font = '10px Rajdhani';
        ctx.textAlign = 'right';
        const val = Math.round(maxValue * (1 - i / 5));
        ctx.fillText(val, padding.left - 5, y + 3);
    }

    // Dibujar las 10 Barras
    categories.forEach((cat, i) => {
        const val = valuesMap[cat];
        const barH = (val / maxValue) * chartH;
        const x = padding.left + (chartW / categories.length) * i + 4;
        const y = padding.top + chartH - barH;
        
        const color = colors[cat] || '#cbd5e0';

        // Dibujo de barra
        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = 12; 
        ctx.fillRect(x, y, barWidth, barH);
        ctx.shadowBlur = 0; 

        // Valor
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'center';
        ctx.font = 'bold 11px Orbitron'; // Fuente un poco más chica para que quepan
        ctx.fillText(val, x + barWidth / 2, y - 5);

        // Etiqueta
        ctx.fillStyle = '#a0aec0';
        ctx.font = 'bold 10px Rajdhani';
        ctx.fillText(labels[i], x + barWidth / 2, height - 10);
    });

    if (statsEl) { statsEl.innerHTML = ''; }
}