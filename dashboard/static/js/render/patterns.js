export function renderPatterns(data) {
    const container = document.getElementById('patternsGrid');
    if (!container) return;

    const patterns = data.patterns.patterns || [];
    if (patterns.length === 0) {
        container.innerHTML = '<p class="loading-text">Cargando ventanas estratégicas...</p>';
        return;
    }

    container.innerHTML = patterns.map(pattern => {
        const name = pattern.pattern_name || "Unknown";
        const currentDist = pattern.current_distance || 0;
        
        // Lógica de Ventana (Tomamos la primera ventana disponible o activa)
        // betting_windows viene como [[61, 90], [121, 150]]
        const windows = pattern.betting_windows || [];
        let activeWindow = windows.find(w => currentDist <= w[1]) || windows[windows.length - 1]; // La siguiente o la última
        
        if (!activeWindow) activeWindow = [0, 0];
        
        const [wStart, wEnd] = activeWindow;
        
        // ESTADOS:
        // 1. PREVIA: Distancia < Inicio
        // 2. ZONA: Inicio <= Distancia <= Fin
        // 3. PASADO: Distancia > Fin
        
        let statusClass = 'cold';
        let statusText = 'ESPERANDO';
        let progress = 0;
        let barClass = '';

        if (currentDist < wStart) {
            // Fase de Espera
            const totalToWait = wStart;
            progress = Math.min(100, (currentDist / totalToWait) * 100);
            statusClass = 'cold';
            statusText = `FALTAN ${wStart - currentDist}`;
            
            // Aviso de calentamiento (10 tiros antes)
            if (wStart - currentDist <= 10) {
                statusClass = 'warm'; // Naranja/Amarillo
                statusText = 'PREPARAR';
                barClass = 'warm';
            }
            
        } else if (currentDist <= wEnd) {
            // ¡ZONA DE JUEGO!
            progress = 100;
            statusClass = 'hot'; // Verde Neón / Rojo Parpadeante
            statusText = 'EN ZONA';
            barClass = 'hot-glow'; // Efecto visual fuerte
            
        } else {
            // Pasado (Zona de Pérdida o Esperando siguiente)
            progress = 100;
            statusClass = 'miss'; // Rojo oscuro
            statusText = 'PASADO';
            barClass = 'miss';
        }

        return `
            <div class="pattern-card ${statusClass === 'hot' ? 'hot-glow-card' : ''}" data-pattern="${pattern.pattern_id}">
                <div class="pattern-header">
                    <span class="pattern-name">${name}</span>
                    <span class="pattern-badge ${statusClass}">
                        ${statusText}
                    </span>
                </div>
                
                <div class="pattern-progress">
                    <div class="progress-bar">
                        <div class="progress-fill ${barClass}" style="width: ${progress}%"></div>
                    </div>
                    <div class="progress-stats">
                        <span class="dist-val">${currentDist}</span>
                        <span class="window-target">VENTANA [${wStart} - ${wEnd}]</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}
