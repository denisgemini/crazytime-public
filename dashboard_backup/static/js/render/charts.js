export function renderHistogram(data) {
    const canvas = document.getElementById('histogramChart');
    const statsEl = document.getElementById('analyticsStats');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = canvas.parentElement.clientHeight;

    const colors = {
        purple: '#b947ff',
        pink: '#ff00aa',
        text: '#e0e0ff',
        grid: 'rgba(255, 255, 255, 0.1)'
    };

    const pachinkoDist = data.distances.pachinko?.distances || [];
    const crazyDist = data.distances.crazytime?.distances || [];

    // Clear
    ctx.fillStyle = '#0a0a12';
    ctx.fillRect(0, 0, width, height);

    if (pachinkoDist.length === 0 && crazyDist.length === 0) {
        ctx.fillStyle = colors.text;
        ctx.font = '14px Rajdhani';
        ctx.textAlign = 'center';
        ctx.fillText('No distance data available', width / 2, height / 2);
        return;
    }

    // Dibujo del histograma (Lógica original recuperada)
    const allDistances = [...pachinkoDist, ...crazyDist];
    const maxDist = Math.max(...allDistances, 50);
    const binCount = 15;
    const binSize = Math.ceil(maxDist / binCount);

    const pachinkoBins = new Array(binCount).fill(0);
    const crazyBins = new Array(binCount).fill(0);

    pachinkoDist.forEach(d => pachinkoBins[Math.min(Math.floor(d / binSize), binCount - 1)]++);
    crazyDist.forEach(d => crazyBins[Math.min(Math.floor(d / binSize), binCount - 1)]++);

    const maxCount = Math.max(...pachinkoBins, ...crazyBins, 1);
    const padding = { top: 20, right: 10, bottom: 30, left: 40 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    // Dibujar barras Pachinko
    const barW = (chartW / binCount) / 2 - 2;
    pachinkoBins.forEach((count, i) => {
        if (count === 0) return;
        const h = (count / maxCount) * chartH;
        ctx.fillStyle = colors.purple;
        ctx.fillRect(padding.left + (chartW / binCount) * i + 1, padding.top + chartH - h, barW, h);
    });

    // Dibujar barras Crazy
    crazyBins.forEach((count, i) => {
        if (count === 0) return;
        const h = (count / maxCount) * chartH;
        ctx.fillStyle = colors.pink;
        ctx.fillRect(padding.left + (chartW / binCount) * i + barW + 2, padding.top + chartH - h, barW, h);
    });

    // Actualizar Estadísticas de Texto (AnalyticsStats)
    if (statsEl) {
        const pStats = data.distances.pachinko?.statistics || {};
        const cStats = data.distances.crazytime?.statistics || {};
        
        statsEl.innerHTML = `
            <div class="analytic-stat">
                <span class="stat-label">AVG PACHINKO</span>
                <span class="stat-value">${pStats.mean_distance?.toFixed(1) || '--'}</span>
            </div>
            <div class="analytic-stat">
                <span class="stat-label">AVG CRAZYTIME</span>
                <span class="stat-value">${cStats.mean_distance?.toFixed(1) || '--'}</span>
            </div>
            <div class="analytic-stat">
                <span class="stat-label">SAMPLES</span>
                <span class="stat-value">${pachinkoDist.length + crazyDist.length}</span>
            </div>
        `;
    }
}
