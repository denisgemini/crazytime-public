export async function fetchDashboardData() {
    const fetchSafe = async (url) => {
        try {
            const res = await fetch(url);
            if (!res.ok) return null;
            return await res.json();
        } catch (e) {
            console.warn("Error fetching " + url, e);
            return null;
        }
    };

    const [status, patterns, alerts, recent, stats, pachinkoDist, crazyDist] = await Promise.all([
        fetchSafe('/api/status'),
        fetchSafe('/api/patterns'),
        fetchSafe('/api/alerts'),
        fetchSafe('/api/spins/recent?limit=50'),
        fetchSafe('/api/spins/stats'),
        fetchSafe('/api/patterns/pachinko/distances?limit=100'),
        fetchSafe('/api/patterns/crazytime/distances?limit=100')
    ]);

    return { 
        status: status || { status: 'error', service_running: false, last_spin_id: 0 }, 
        patterns: patterns || { patterns: [] }, 
        alerts: alerts || { alerts: [], active_count: 0 }, 
        recent: recent || { spins: [] },
        stats: stats || { today_stats: { results_distribution: {} } },
        distances: {
            pachinko: pachinkoDist || { distances: [] },
            crazytime: crazyDist || { distances: [] }
        }
    };
}
