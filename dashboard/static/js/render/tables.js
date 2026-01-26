export function renderTables(root, data) {
    if (!data) return;

    // --- Tabla de Patrones ---
    const patternsContainer = document.createElement("div");
    patternsContainer.innerHTML = "<h2>Estado de Patrones</h2>";
    const pTable = document.createElement("table");
    pTable.innerHTML = `
        <thead>
            <tr>
                <th>Patrón</th>
                <th>Distancia</th>
                <th>Último Resultado</th>
                <th>Thresholds</th>
            </tr>
        </thead>
    `;
    const pBody = document.createElement("tbody");
    data.patterns.patterns.forEach(p => {
        const tr = document.createElement("tr");
        const statusClass = p.spins_since > 100 ? 'warning' : '';
        tr.innerHTML = `
            <td>${p.pattern_name}</td>
            <td class="${statusClass}">${p.spins_since}</td>
            <td>${p.last_result || '-'}</td>
            <td>${Object.entries(p.thresholds_status).map(([t, s]) => `[${t}: ${s.status}]`).join(' ')}</td>
        `;
        pBody.appendChild(tr);
    });
    pTable.appendChild(pBody);
    patternsContainer.appendChild(pTable);
    root.appendChild(patternsContainer);

    // --- Tabla de Tiros Recientes ---
    const recentContainer = document.createElement("div");
    recentContainer.innerHTML = "<h2>Últimos 20 Tiros</h2>";
    const rTable = document.createElement("table");
    rTable.innerHTML = `
        <thead>
            <tr>
                <th>ID</th>
                <th>Resultado</th>
                <th>Top Slot</th>
                <th>Hora</th>
            </tr>
        </thead>
    `;
    const rBody = document.createElement("tbody");
    data.recent.spins.forEach(s => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${s.id}</td>
            <td class="result-${s.resultado.toLowerCase()}">${s.resultado}</td>
            <td>${s.top_slot_result || '-'} (x${s.top_slot_multiplier || 1})</td>
            <td>${s.timestamp.split('T')[1] || s.timestamp}</td>
        `;
        rBody.appendChild(tr);
    });
    rTable.appendChild(rBody);
    recentContainer.appendChild(rTable);
    root.appendChild(recentContainer);
}
