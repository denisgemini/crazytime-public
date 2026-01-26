export function renderDistanceGrid(patternId) {
    const gridContainer = document.getElementById('distanceGrid');
    if (!gridContainer) return;

    fetch(`/api/patterns/${patternId}/distances?limit=80`)
        .then(response => response.json())
        .then(data => {
            const distances = data.distances || [];
            if (distances.length === 0) {
                gridContainer.innerHTML = '<p style="color: gray; text-align: center; padding: 2rem;">No data available</p>';
                return;
            }

            const maxDist = Math.max(...distances);
            gridContainer.innerHTML = distances.map(dist => {
                let colorClass = 'low';
                if (dist > maxDist * 0.7) colorClass = 'very-high';
                else if (dist > maxDist * 0.5) colorClass = 'high';
                else if (dist > maxDist * 0.3) colorClass = 'medium';
                return `<div class="distance-cell ${colorClass}" title="${dist} spins">${dist}</div>`;
            }).join('');
        });
}
