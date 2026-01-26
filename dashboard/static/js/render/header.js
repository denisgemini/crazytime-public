export function renderHeader(data) {
    const clock = document.getElementById('clock');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    const totalSpins = document.getElementById('totalSpins');

    // Reloj Real (Hora del servidor o local)
    if (clock) {
        clock.textContent = new Date().toLocaleTimeString();
    }

    // Indicador LIVE
    const statusIndicator = document.getElementById('statusIndicator');
    if (statusIndicator && statusText) {
        const isRunning = data.status.service_running;
        const apiError = data.status.status === 'error';

        // Limpiar clases para evitar conflictos
        statusIndicator.classList.remove('online', 'offline');

        if (apiError) {
            statusIndicator.classList.add('offline');
            statusText.textContent = 'OFFLINE';
        } else if (isRunning) {
            statusIndicator.classList.add('online');
            statusText.textContent = 'LIVE';
        } else {
            // Sin clase adicional queda amarillo por defecto
            statusText.textContent = 'CONNECTING';
        }
    }

    if (totalSpins && data.status.total_spins_today !== undefined) {
        totalSpins.textContent = data.status.total_spins_today;
    }
}
