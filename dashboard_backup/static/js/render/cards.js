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

    // Anillo de progreso basado en el patrón más cercano al threshold
    if (ring && pPattern && cPattern) {
        const pProg = pPattern.spins_since / 110; 
        const cProg = cPattern.spins_since / 250;
        const progress = Math.min(Math.max(pProg, cProg), 1);
        
        const circumference = 326.7; // 2 * PI * 52 aprox
        ring.style.strokeDashoffset = circumference * (1 - progress);
    }
}
