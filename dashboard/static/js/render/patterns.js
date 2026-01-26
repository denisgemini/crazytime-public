export function renderPatterns(data) {
    const container = document.getElementById('patternsGrid');
    if (!container) return;

    const patterns = data.patterns.patterns || [];
    if (patterns.length === 0) {
        container.innerHTML = '<p class="loading-text">Waiting for pattern data...</p>';
        return;
    }

    container.innerHTML = patterns.map(pattern => {
        // Obtenemos los valores limpios
        const name = pattern.pattern_name || "Unknown";
        const currentDist = pattern.current_distance || 0;
        const thresholds = pattern.thresholds || [100];
        const maxThreshold = Math.max(...thresholds);
        
        // Calculo de progreso y estado HOT/COLD
        const progress = Math.min(100, (currentDist / maxThreshold) * 100);
        const isHot = currentDist >= thresholds[0]; // Hot si supera el primer threshold

        return `
            <div class="pattern-card ${isHot ? 'hot-glow' : ''}" data-pattern="${pattern.pattern_id}">
                <div class="pattern-header">
                    <span class="pattern-name">${name}</span>
                    <span class="pattern-badge ${isHot ? 'hot' : 'cold'}">
                        ${isHot ? 'READY' : 'WAITING'}
                    </span>
                </div>
                <div class="pattern-progress">
                    <div class="progress-bar">
                        <div class="progress-fill ${isHot ? 'hot' : ''}" style="width: ${progress}%"></div>
                    </div>
                    <div class="progress-stats">
                        <span>${currentDist} spins</span>
                        <span>${maxThreshold} threshold</span>
                    </div>
                </div>
                <div class="pattern-footer-simple">
                    <span class="t-label">THRESHOLDS:</span>
                    <span class="t-values">${thresholds.join(' / ')}</span>
                </div>
            </div>
        `;
    }).join('');
}
