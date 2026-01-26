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
    if (statusDot && statusText) {
        const isRunning = data.status.service_running;
        statusDot.className = 'status-dot ' + (isRunning ? 'status-online' : 'status-offline');
        statusText.textContent = isRunning ? 'LIVE' : 'OFFLINE';
    }

    if (totalSpins && data.status.total_spins_today !== undefined) {
        totalSpins.textContent = data.status.total_spins_today;
    }
}
