export function renderTimeline(data) {
    const timeline = document.getElementById('timeline');
    if (!timeline) return;

    timeline.innerHTML = '';
    data.recent.spins.slice(0, 15).forEach(s => {
        const item = document.createElement('div');
        item.className = 'timeline-item';
        item.innerHTML = `
            <div class="timeline-marker result-${s.resultado.toLowerCase().replace(' ', '')}"></div>
            <div class="timeline-content">
                <div class="timeline-res">${s.resultado}</div>
                <div class="timeline-id">#${s.id}</div>
            </div>
        `;
        timeline.appendChild(item);
    });
}
