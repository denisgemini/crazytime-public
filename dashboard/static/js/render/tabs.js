export function renderDistanceGrid(patternId) {
    const gridContainer = document.getElementById('distanceGrid');
    if (!gridContainer) return;

    fetch(`/api/patterns/${patternId}/distances?limit=80`)
        .then(response => response.json())
        .then(data => {
            const distances = (data.distances || []).reverse();
            if (distances.length === 0) {
                gridContainer.innerHTML = '<p style="color: gray; text-align: center; padding: 2rem;">No data available</p>';
                return;
            }

            const maxDist = Math.max(...distances);
            gridContainer.innerHTML = distances.map(dist => {
                let colorClass = 'dist-cold';
                
                if (patternId === 'pachinko') {
                    if (dist <= 60) colorClass = 'dist-cold';
                    else if (dist <= 90) colorClass = 'dist-window'; // Ventana Verde
                    else if (dist <= 150) colorClass = 'dist-warm';
                    else if (dist <= 200) colorClass = 'dist-hot';
                    else colorClass = 'dist-extreme'; // Azul
                } else {
                    // Lógica por defecto para otros (CrazyTime) o usar maxDist
                    if (dist > 200) colorClass = 'dist-extreme';
                    else if (dist > 100) colorClass = 'dist-hot';
                    else if (dist > 50) colorClass = 'dist-warm';
                }

                return `<div class="distance-cell ${colorClass}" title="${dist} tiros">${dist}</div>`;
            }).join('');
        });
}
