import { state } from "./state.js";
import { fetchDashboardData } from "./api.js";
import { renderDashboard } from "../render/dashboard.js";
import { renderDistanceGrid } from "../render/tabs.js";

async function updateDashboard() {
    try {
        const data = await fetchDashboardData();
        state.data = data;
        renderDashboard(state.data);
    } catch (err) {
        console.error("Dashboard error:", err);
    }
}

function startClock() {
    const clock = document.getElementById('clock');
    if (!clock) return;
    setInterval(() => {
        clock.textContent = new Date().toLocaleTimeString();
    }, 1000);
}

export function startController() {
    if (state.initialized) return;
    state.initialized = true;

    startClock();
    updateDashboard();

    // Polling de datos cada 3 segundos
    state.timers.refresh = setInterval(updateDashboard, 3000);

    // Inicializar listeners de pestañas (Pachinko/CrazyTime)
    const tabs = document.querySelectorAll('.distance-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            renderDistanceGrid(tab.dataset.pattern);
        });
    });
    
    // Cargar Pachinko por defecto en el grid
    setTimeout(() => renderDistanceGrid('pachinko'), 1000);
}
