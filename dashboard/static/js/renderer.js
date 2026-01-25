/**
 * CrazyTime v2 Dashboard - Chart Renderer
 * Handles Canvas/SVG charts and data visualizations
 */

class DashboardRenderer {
    constructor() {
        this.histogramChart = null;
        this.colors = {
            blue: '#00d4ff',
            purple: '#b947ff',
            pink: '#ff00aa',
            green: '#00ff88',
            yellow: '#ffdd00',
            red: '#ff3366',
            text: '#e0e0ff',
            grid: 'rgba(255, 255, 255, 0.1)'
        };
        this.init();
    }

    init() {
        console.log('[Renderer] Initializing...');
        this.initHistogramChart();
        window.dashboardRenderer = this;
    }

    initHistogramChart() {
        const canvas = document.getElementById('histogramChart');
        if (!canvas) {
            console.warn('[Renderer] Histogram canvas not found');
            return;
        }

        const ctx = canvas.getContext('2d');

        // Make canvas responsive
        const resizeCanvas = () => {
            const container = canvas.parentElement;
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;
            this.drawHistogram(ctx, canvas.width, canvas.height);
        };

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
    }

    drawHistogram(ctx, width, height) {
        // Clear canvas
        ctx.fillStyle = '#0a0a12';
        ctx.fillRect(0, 0, width, height);

        // Default empty state
        ctx.fillStyle = this.colors.text;
        ctx.font = '14px Rajdhani';
        ctx.textAlign = 'center';
        ctx.fillText('Loading distance data...', width / 2, height / 2);
    }

    updateHistogram(pachinkoData, crazyData) {
        const canvas = document.getElementById('histogramChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        const pachinkoDist = pachinkoData?.distances || [];
        const crazyDist = crazyData?.distances || [];

        // Clear canvas
        ctx.fillStyle = '#0a0a12';
        ctx.fillRect(0, 0, width, height);

        if (pachinkoDist.length === 0 && crazyDist.length === 0) {
            ctx.fillStyle = this.colors.text;
            ctx.font = '14px Rajdhani';
            ctx.textAlign = 'center';
            ctx.fillText('No distance data available', width / 2, height / 2);
            return;
        }

        // Calculate bins
        const allDistances = [...pachinkoDist, ...crazyDist];
        const maxDist = Math.max(...allDistances, 50);
        const binCount = 15;
        const binSize = Math.ceil(maxDist / binCount);

        // Create bins
        const pachinkoBins = new Array(binCount).fill(0);
        const crazyBins = new Array(binCount).fill(0);

        pachinkoDist.forEach(d => {
            const bin = Math.min(Math.floor(d / binSize), binCount - 1);
            pachinkoBins[bin]++;
        });

        crazyDist.forEach(d => {
            const bin = Math.min(Math.floor(d / binSize), binCount - 1);
            crazyBins[bin]++;
        });

        const maxCount = Math.max(...pachinkoBins, ...crazyBins, 1);

        // Chart dimensions
        const padding = { top: 30, right: 20, bottom: 40, left: 50 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;

        // Draw grid
        ctx.strokeStyle = this.colors.grid;
        ctx.lineWidth = 1;

        // Horizontal grid lines
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (chartHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();

            // Y-axis labels
            const value = Math.round(maxCount * (1 - i / 4));
            ctx.fillStyle = this.colors.text;
            ctx.font = '11px Rajdhani';
            ctx.textAlign = 'right';
            ctx.fillText(value.toString(), padding.left - 10, y + 4);
        }

        // X-axis labels
        ctx.textAlign = 'center';
        for (let i = 0; i < binCount; i += 3) {
            const x = padding.left + (chartWidth / binCount) * i + (chartWidth / binCount) / 2;
            const value = i * binSize;
            ctx.fillText(value.toString(), x, height - padding.bottom + 20);
        }

        // Axis labels
        ctx.fillStyle = this.colors.text;
        ctx.font = '12px Rajdhani';
        ctx.textAlign = 'center';
        ctx.fillText('Distance (spins)', width / 2, height - 5);

        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Frequency', 0, 0);
        ctx.restore();

        // Bar dimensions
        const barWidth = (chartWidth / binCount) / 2 - 2;

        // Draw bars - Pachinko
        pachinkoBins.forEach((count, i) => {
            if (count === 0) return;

            const barHeight = (count / maxCount) * chartHeight;
            const x = padding.left + (chartWidth / binCount) * i + 2;
            const y = padding.top + chartHeight - barHeight;

            // Bar fill
            ctx.fillStyle = this.colors.purple;
            ctx.globalAlpha = 0.7;
            ctx.fillRect(x, y, barWidth, barHeight);

            // Bar glow
            ctx.shadowColor = this.colors.purple;
            ctx.shadowBlur = 10;
            ctx.fillRect(x, y, barWidth, barHeight);
            ctx.shadowBlur = 0;
            ctx.globalAlpha = 1;
        });

        // Draw bars - CrazyTime
        crazyBins.forEach((count, i) => {
            if (count === 0) return;

            const barHeight = (count / maxCount) * chartHeight;
            const x = padding.left + (chartWidth / binCount) * i + (chartWidth / binCount) / 2 + 2;
            const y = padding.top + chartHeight - barHeight;

            // Bar fill
            ctx.fillStyle = this.colors.pink;
            ctx.globalAlpha = 0.7;
            ctx.fillRect(x, y, barWidth, barHeight);

            // Bar glow
            ctx.shadowColor = this.colors.pink;
            ctx.shadowBlur = 10;
            ctx.fillRect(x, y, barWidth, barHeight);
            ctx.shadowBlur = 0;
            ctx.globalAlpha = 1;
        });

        // Legend
        this.drawLegend(ctx, width, [
            { color: this.colors.purple, label: 'Pachinko' },
            { color: this.colors.pink, label: 'CrazyTime' }
        ]);
    }

    drawLegend(ctx, width, items) {
        const legendX = width - 120;
        const legendY = 10;

        items.forEach((item, i) => {
            const y = legendY + i * 20;

            // Color box
            ctx.fillStyle = item.color;
            ctx.fillRect(legendX, y, 12, 12);

            // Label
            ctx.fillStyle = this.colors.text;
            ctx.font = '11px Rajdhani';
            ctx.textAlign = 'left';
            ctx.fillText(item.label, legendX + 18, y + 10);
        });
    }

    updateAnalyticsStats(pachinkoData, crazyData) {
        const statsEl = document.getElementById('analyticsStats');
        if (!statsEl) return;

        const pStats = pachinkoData?.statistics || {};
        const cStats = crazyData?.statistics || {};

        // Update pattern average distances
        const pachinkoAvg = document.getElementById('avgDist-pachinko');
        const crazyAvg = document.getElementById('avgDist-crazytime');

        if (pachinkoAvg && pStats.mean_distance) {
            pachinkoAvg.textContent = pStats.mean_distance.toFixed(1);
        }

        if (crazyAvg && cStats.mean_distance) {
            crazyAvg.textContent = cStats.mean_distance.toFixed(1);
        }

        // Update analytics stats panel
        const totalOps = (pachinkoData?.distances?.length || 0) + (crazyData?.distances?.length || 0);
        const avgPachinko = pStats.mean_distance?.toFixed(1) || '--';
        const avgCrazy = cStats.mean_distance?.toFixed(1) || '--';

        statsEl.innerHTML = `
            <div class="analytic-stat">
                <span class="stat-label">TOTAL DATA</span>
                <span class="stat-value">${totalOps}</span>
            </div>
            <div class="analytic-stat">
                <span class="stat-label">AVG PACHINKO</span>
                <span class="stat-value">${avgPachinko}</span>
            </div>
            <div class="analytic-stat">
                <span class="stat-label">AVG CRAZYTIME</span>
                <span class="stat-value">${avgCrazy}</span>
            </div>
        `;
    }

    // ==================== SVG PROGRESS RING ====================

    updateProgressRing(elementId, current, max) {
        const ring = document.getElementById(elementId);
        if (!ring) return;

        const circumference = 2 * Math.PI * 52;
        const progress = Math.min(current / max, 1);
        const offset = circumference * (1 - progress);

        ring.style.strokeDashoffset = offset;
    }

    // ==================== ANIMATED COUNTER ====================

    animateCounter(element, from, to, duration = 1000) {
        const startTime = performance.now();
        const diff = to - from;

        if (diff === 0) return;

        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(from + diff * easeOut);
            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };

        requestAnimationFrame(update);
    }
}

// Initialize renderer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DashboardRenderer();
});
