/**
 * CrazyTime v2 Dashboard - Main Application Logic
 * Handles API polling and state management
 */

class CrazyTimeDashboard {
    constructor() {
        this.pollingInterval = 10000; // 10 seconds
        this.chartsInterval = 30000; // 30 seconds for charts
        this.lastSpinId = 0;
        this.isRunning = false;

        // State
        this.state = {
            status: null,
            recentSpins: [],
            patterns: [],
            alerts: [],
            analytics: null,
            gaps: []
        };

        // Initialize
        this.init();
    }

    async init() {
        console.log('[Dashboard] Initializing...');

        // Start clock
        this.startClock();

        // Initial data fetch
        await this.fetchAllData();

        // Start polling
        this.startPolling();

        // Start charts update
        this.startChartsPolling();

        console.log('[Dashboard] Ready');
    }

    // ==================== CLOCK ====================

    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('es-PE', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            document.getElementById('clock').textContent = timeStr;
        };

        updateClock();
        setInterval(updateClock, 1000);
    }

    // ==================== API ====================

    async fetch(endpoint) {
        try {
            const response = await fetch(`/api/${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`[API Error] ${endpoint}:`, error);
            return null;
        }
    }

    async fetchAllData() {
        console.log('[Dashboard] Fetching all data...');

        // Fetch in parallel
        const [status, recentSpins, spinsStats, patterns, alerts, analytics, gaps] = await Promise.all([
            this.fetch('status'),
            this.fetch('spins/recent?limit=50'),
            this.fetch('spins/stats'),
            this.fetch('patterns'),
            this.fetch('alerts'),
            this.fetch('analytics/window'),
            this.fetch('gaps?limit=20')
        ]);

        if (status) {
            this.state.status = status;
            this.state.totalSpinsToday = status.total_spins_today || 0;
            this.lastSpinId = status.last_spin_id || 0;
        }

        if (recentSpins) {
            this.state.recentSpins = recentSpins.spins || [];
        }

        if (patterns) {
            this.state.patterns = patterns.patterns || [];
        }

        if (alerts) {
            this.state.alerts = alerts.alerts || [];
        }

        if (analytics) {
            this.state.analytics = analytics.windows || [];
        }

        if (gaps) {
            this.state.gaps = gaps.gaps || [];
        }

        // Render all components
        this.renderAll();

        // Update last update time
        document.getElementById('lastUpdate').textContent =
            `Last update: ${new Date().toLocaleTimeString()}`;
    }

    async fetchUpdates() {
        console.log('[Dashboard] Fetching updates...');

        // Fetch current state
        const [status, recentSpins, patterns, alerts] = await Promise.all([
            this.fetch('status'),
            this.fetch('spins/recent?limit=50'),
            this.fetch('patterns'),
            this.fetch('alerts')
        ]);

        let hasNewSpin = false;

        if (status && status.last_spin_id > this.lastSpinId) {
            hasNewSpin = true;
            this.lastSpinId = status.last_spin_id;
            this.state.totalSpinsToday = status.total_spins_today || 0;
        }

        if (recentSpins) {
            this.state.recentSpins = recentSpins.spins || [];
        }

        if (patterns) {
            this.state.patterns = patterns.patterns || [];
        }

        if (alerts) {
            this.state.alerts = alerts.alerts || [];
        }

        // Render with animations for new data
        this.renderAll(hasNewSpin);

        // Update last update time
        document.getElementById('lastUpdate').textContent =
            `Last update: ${new Date().toLocaleTimeString()}`;
    }

    // ==================== POLLING ====================

    startPolling() {
        if (this.isRunning) return;

        this.isRunning = true;
        console.log('[Dashboard] Starting polling (10s)');

        const poll = async () => {
            await this.fetchUpdates();
        };

        // Initial poll after short delay
        setTimeout(poll, 2000);

        // Regular polling
        this.pollingTimer = setInterval(poll, this.pollingInterval);
    }

    stopPolling() {
        if (this.pollingTimer) {
            clearInterval(this.pollingTimer);
        }
        this.isRunning = false;
    }

    startChartsPolling() {
        console.log('[Dashboard] Starting charts polling (30s)');

        const updateCharts = async () => {
            await this.fetchPatternDistances();
        };

        this.chartsTimer = setInterval(updateCharts, this.chartsInterval);
    }

    async fetchPatternDistances() {
        // Fetch distances for both patterns
        const [pachinkoDist, crazyDist] = await Promise.all([
            this.fetch('patterns/pachinko/distances?limit=50'),
            this.fetch('patterns/crazytime/distances?limit=50')
        ]);

        // Update charts
        if (window.dashboardRenderer) {
            window.dashboardRenderer.updateHistogram(pachinkoDist, crazyDist);
            window.dashboardRenderer.updateAnalyticsStats(pachinkoDist, crazyDist);
        }
    }

    // ==================== RENDERING ====================

    renderAll(hasNewSpin = false) {
        this.renderStatus();
        this.renderResult();
        this.renderPatterns();
        this.renderHeatmap();
        this.renderTimeline();
        this.renderAlerts();

        // Update charts if renderer is ready
        if (window.dashboardRenderer) {
            this.fetchPatternDistances();
        }
    }

    renderStatus() {
        const status = this.state.status;

        if (!status) {
            document.getElementById('statusIndicator').className = 'status-indicator offline';
            document.querySelector('.status-text').textContent = 'OFFLINE';
            return;
        }

        const indicator = document.getElementById('statusIndicator');
        const totalSpinsEl = document.getElementById('totalSpins');

        if (status.service_running) {
            indicator.className = 'status-indicator online';
            document.querySelector('.status-text').textContent = 'LIVE';
        } else {
            indicator.className = 'status-indicator offline';
            document.querySelector('.status-text').textContent = 'OFFLINE';
        }

        // Animate counter
        if (totalSpinsEl) {
            const currentValue = parseInt(totalSpinsEl.textContent.replace(/,/g, '')) || 0;
            this.animateCounter(totalSpinsEl, currentValue, status.total_spins_today || 0);
        }
    }

    renderResult() {
        const spins = this.state.recentSpins;
        if (spins.length === 0) return;

        const lastSpin = spins[0];
        const patterns = this.state.patterns;

        // Update result display
        const resultEl = document.getElementById('currentResult');
        const spinIdEl = document.getElementById('currentSpinId');

        if (resultEl && lastSpin) {
            resultEl.textContent = this.formatResult(lastSpin.resultado);
            resultEl.className = `result-value ${this.getResultClass(lastSpin.resultado)}`;
            spinIdEl.textContent = lastSpin.id;
        }

        // Update counters from patterns
        const pachinko = patterns.find(p => p.pattern_id === 'pachinko');
        const crazytime = patterns.find(p => p.pattern_id === 'crazytime');

        const pachinkoCounter = document.getElementById('spinsWithoutPachinko');
        const crazyCounter = document.getElementById('spinsWithoutCrazyTime');

        if (pachinkoCounter && pachinko) {
            pachinkoCounter.textContent = pachinko.current_distance;
        }

        if (crazyCounter && crazytime) {
            crazyCounter.textContent = crazytime.current_distance;
        }

        // Update progress ring (using Pachinko as reference)
        if (pachinko) {
            const ring = document.getElementById('progressRing');
            const circumference = 2 * Math.PI * 52;
            const progress = Math.min(1, pachinko.current_distance / 110);
            const offset = circumference * (1 - progress);
            ring.style.strokeDashoffset = offset;
        }
    }

    renderPatterns() {
        const container = document.getElementById('patternsGrid');
        if (!container) return;

        const patterns = this.state.patterns;

        container.innerHTML = patterns.map(pattern => {
            const maxThreshold = Math.max(...pattern.thresholds, 100);
            const progress = Math.min(100, (pattern.current_distance / maxThreshold) * 100);
            const isHot = progress >= 50;

            // Get stats from analytics
            const analytics = this.state.analytics || [];
            const patternAnalytics = analytics.find(a => a.pattern_id === pattern.pattern_id);

            return `
                <div class="pattern-card" data-pattern="${pattern.pattern_id}">
                    <div class="pattern-header">
                        <span class="pattern-name">${pattern.pattern_name}</span>
                        <span class="pattern-badge ${isHot ? 'hot' : 'cold'}">
                            ${isHot ? 'HOT' : 'COLD'}
                        </span>
                    </div>
                    <div class="pattern-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                        <div class="progress-stats">
                            <span>${pattern.current_distance} spins</span>
                            <span>${maxThreshold} threshold</span>
                        </div>
                    </div>
                    <div class="pattern-stats">
                        <div class="stat-item">
                            <span class="stat-label">THRESHOLD</span>
                            <span class="stat-value">${pattern.thresholds.join(' / ')}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">HIT RATE</span>
                            <span class="stat-value">${patternAnalytics ? patternAnalytics.hit_rate.toFixed(1) + '%' : 'N/A'}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">ROI</span>
                            <span class="stat-value">${patternAnalytics ? (patternAnalytics.roi > 0 ? '+' : '') + patternAnalytics.roi.toFixed(1) + '%' : 'N/A'}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">AVG DIST</span>
                            <span class="stat-value" id="avgDist-${pattern.pattern_id}">--</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderHeatmap() {
        const container = document.getElementById('heatmap');
        if (!container) return;

        const spins = this.state.recentSpins.slice(0, 50);

        container.innerHTML = spins.map(spin => {
            const resultClass = this.getHeatmapClass(spin.resultado);
            return `<div class="heatmap-cell ${resultClass}" title="#${spin.id} - ${spin.timestamp}">${this.formatResultShort(spin.resultado)}</div>`;
        }).join('');
    }

    renderTimeline() {
        const container = document.getElementById('timeline');
        if (!container) return;

        const spins = this.state.recentSpins.slice(0, 20);

        container.innerHTML = spins.map((spin, index) => {
            const time = new Date(spin.timestamp);
            const timeStr = time.toLocaleTimeString('es-PE', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            const resultClass = spin.resultado.includes(' ') ? 'bonus' : `number-${spin.resultado}`;

            return `
                <div class="timeline-item" style="animation-delay: ${index * 0.05}s">
                    <span class="timeline-result ${resultClass}">${this.formatResult(spin.resultado)}</span>
                    <span class="timeline-time">${timeStr}</span>
                    <span class="timeline-id">#${spin.id}</span>
                </div>
            `;
        }).join('');
    }

    renderAlerts() {
        const container = document.getElementById('alertsGrid');
        if (!container) return;

        const alerts = this.state.alerts;

        if (alerts.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted);">No active alerts</p>';
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-info">
                    <span class="alert-pattern">${alert.pattern_name}</span>
                    <span class="alert-threshold">Threshold: ${alert.threshold}</span>
                </div>
                <div class="alert-wait">
                    <span class="alert-wait-value">${alert.current_wait}</span>
                    <span class="alert-wait-label">spins waiting</span>
                </div>
                <span class="alert-status ${alert.status}">${alert.status.toUpperCase()}</span>
            </div>
        `).join('');
    }

    // ==================== UTILITIES ====================

    formatResult(result) {
        if (result === 'CoinFlip') return 'COINFLIP';
        if (result === 'CashHunt') return 'CASH HUNT';
        if (result === 'Pachinko') return 'PACHINKO';
        if (result === 'CrazyTime') return 'CRAZYTIME';
        return result;
    }

    formatResultShort(result) {
        if (result === 'CoinFlip') return 'CF';
        if (result === 'CashHunt') return 'CH';
        if (result === 'Pachinko') return 'PK';
        if (result === 'CrazyTime') return 'CT';
        return result;
    }

    getResultClass(result) {
        if (result === 'Pachinko') return 'pachinko';
        if (result === 'CrazyTime') return 'crazytime';
        if (result === 'CoinFlip') return 'coinflip';
        if (result === 'CashHunt') return 'cashhunt';
        return '';
    }

    getHeatmapClass(result) {
        if (result === 'CoinFlip') return 'bonus-cf';
        if (result === 'CashHunt') return 'bonus-ch';
        if (result === 'Pachinko') return 'bonus-pk';
        if (result === 'CrazyTime') return 'bonus-ct';
        return `number-${result}`;
    }

    animateCounter(element, from, to, duration = 1000) {
        const startTime = performance.now();
        const diff = to - from;

        if (diff === 0) return;

        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(from + diff * easeOut);
            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };

        requestAnimationFrame(update);
    }

    // ==================== TICKER ====================

    updateTicker(spins) {
        if (window.dashboardTicker) {
            window.dashboardTicker.update(spins.map(s => s.resultado));
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new CrazyTimeDashboard();
});


// ==================== DISTANCE GRID ====================

function renderDistanceGrid(patternId) {
    const gridContainer = document.getElementById('distanceGrid');
    if (!gridContainer) return;

    // Fetch distances for the pattern
    fetch(`/api/patterns/${patternId}/distances?limit=80`)
        .then(response => response.json())
        .then(data => {
            const distances = data.distances || [];
            
            if (distances.length === 0) {
                gridContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No distance data available</p>';
                return;
            }

            // Calculate thresholds for color coding
            const maxDist = Math.max(...distances);
            
            gridContainer.innerHTML = distances.map(dist => {
                let colorClass = 'low';
                if (dist > maxDist * 0.7) colorClass = 'very-high';
                else if (dist > maxDist * 0.5) colorClass = 'high';
                else if (dist > maxDist * 0.3) colorClass = 'medium';
                
                return `<div class="distance-cell ${colorClass}" title="Distance: ${dist} spins">${dist}</div>`;
            }).join('');
        })
        .catch(error => {
            console.error('Error loading distances:', error);
            gridContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">Error loading data</p>';
        });
}

// Tab switching
document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.distance-tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            tab.classList.add('active');
            
            // Render grid for selected pattern
            const patternId = tab.dataset.pattern;
            renderDistanceGrid(patternId);
        });
    });
    
    // Load Pachinko by default
    renderDistanceGrid('pachinko');
});
