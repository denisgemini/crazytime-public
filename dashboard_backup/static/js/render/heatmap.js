export function renderHeatmap(data) {
    const heatmap = document.getElementById('heatmap');
    if (!heatmap) return;

    const spins = data.recent.spins || [];
    heatmap.innerHTML = '';
    
    spins.slice(0, 50).reverse().forEach(s => {
        const cell = document.createElement('div');
        const resClass = 'result-' + s.resultado.toLowerCase().replace(' ', '');
        cell.className = 'heatmap-cell ' + resClass;
        cell.title = `#${s.id} - ${s.resultado}`;
        heatmap.appendChild(cell);
    });
}
