import { renderHeader } from './header.js';
import { renderTicker } from './ticker.js';
import { renderCards } from './cards.js';
import { renderPatterns } from './patterns.js';
import { renderHeatmap } from './heatmap.js';
import { renderTimeline } from './timeline.js';
import { renderHistogram } from './charts.js';

export function renderDashboard(data) {
    // Orquestación de todos los componentes visuales
    renderHeader(data);
    renderTicker(data);
    renderCards(data);
    renderPatterns(data);
    renderHeatmap(data);
    renderTimeline(data);
    renderHistogram(data);

    const lastUpdate = document.getElementById('lastUpdate');
    if (lastUpdate) {
        lastUpdate.textContent = 'Last update: ' + new Date().toLocaleTimeString();
    }
}
