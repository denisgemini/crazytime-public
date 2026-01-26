export function renderTicker(data) {
    const ticker = document.getElementById('ticker');
    if (!ticker) return;

    const spins = data.recent.spins || [];
    ticker.innerHTML = '';
    
    // Mostrar solo los últimos 40 resultados únicos, sin duplicar
    const displaySpins = spins.slice(0, 40);

    displaySpins.forEach(s => {
        const item = document.createElement('div');
        let resClass = 'result-' + s.resultado.toLowerCase().replace(' ', '');
        
        // Mapear números a clases de billetes específicos
        if (['1', '2', '5', '10'].includes(s.resultado)) {
            resClass = 'bill-' + s.resultado;
        } else {
            // Simplificar nombres de bonos para CSS
            if (s.resultado === 'CoinFlip') resClass = 'badge-cf';
            if (s.resultado === 'CashHunt') resClass = 'badge-ch';
            if (s.resultado === 'Pachinko') resClass = 'badge-pk';
            if (s.resultado === 'CrazyTime') resClass = 'badge-ct';
        }

        item.className = 'ticker-item ' + resClass;
        
        // Formatear texto corto para bonos
        let displayText = s.resultado;
        if (s.resultado === 'CoinFlip') displayText = 'COIN';
        if (s.resultado === 'CashHunt') displayText = 'CASH';
        if (s.resultado === 'Pachinko') displayText = 'PACHINKO';
        if (s.resultado === 'CrazyTime') displayText = 'CRAZY';

        item.innerHTML = `<span class="ticker-res">${displayText}</span>`;
        ticker.appendChild(item);
    });
}
