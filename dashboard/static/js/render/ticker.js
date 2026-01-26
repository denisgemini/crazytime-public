export function renderTicker(data) {
    const ticker = document.getElementById('ticker');
    if (!ticker) return;

    const spins = data.recent.spins || [];
    ticker.innerHTML = '';
    
    spins.slice(0, 30).forEach(s => {
        const item = document.createElement('div');
        const resClass = 'result-' + s.resultado.toLowerCase().replace(' ', '');
        item.className = 'ticker-item ' + resClass;
        item.innerHTML = `
            <span class="ticker-res">${s.resultado}</span>
            <span class="ticker-id">#${s.id}</span>
        `;
        ticker.appendChild(item);
    });
}
