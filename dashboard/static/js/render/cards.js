export function renderCards(data) {
    const currentResult = document.getElementById('currentResult');
    const currentSpinId = document.getElementById('currentSpinId');
    const ring = document.getElementById('progressRing');
    
    const pachinkoVal = document.getElementById('spinsWithoutPachinko');
    const crazyVal = document.getElementById('spinsWithoutCrazyTime');

    if (data.status.last_result) {
        currentResult.textContent = data.status.last_result.toUpperCase();
        currentResult.className = 'result-value result-' + data.status.last_result.toLowerCase().replace(' ', '');
        currentSpinId.textContent = data.status.last_spin_id;
    }

    // Buscar distancias en el array de patterns
    const patterns = data.patterns.patterns || [];
    const pPattern = patterns.find(p => p.pattern_id === 'pachinko');
    const cPattern = patterns.find(p => p.pattern_id === 'crazytime');

    if (pPattern && pachinkoVal) pachinkoVal.textContent = pPattern.spins_since;
    if (cPattern && crazyVal) crazyVal.textContent = cPattern.spins_since;

    // Anillo de progreso basado EXCLUSIVAMENTE en Crazy Time (Umbral 190)
    if (ring && cPattern) {
        const threshold = 190;
        const progress = Math.min(cPattern.spins_since / threshold, 1);
        
        const circumference = 326.7; // 2 * PI * 52 aprox
        ring.style.strokeDashoffset = circumference * (1 - progress);
        
        // Cambio de color: Azul celeste neón si supera el umbral (¡A jugar!)
        if (cPattern.spins_since >= threshold) {
            ring.style.stroke = "#00f2ff"; // Azul celeste neón
            ring.style.filter = "drop-shadow(0 0 12px #00f2ff)";
        } else {
            ring.style.stroke = "#00ff88"; // Verde neón original
            ring.style.filter = "drop-shadow(0 0 5px #00ff88)";
        }
    }
}
