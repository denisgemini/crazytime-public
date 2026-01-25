/**
 * CrazyTime v2 Dashboard - Ticker Component
 * Horizontal scrolling ticker for recent results
 */

class DashboardTicker {
    constructor(containerId = 'ticker') {
        this.container = document.getElementById(containerId);
        this.results = [];
        this.animationDuration = 30000; // 30 seconds for full loop
        this.isPaused = false;
        this.init();
    }

    init() {
        if (!this.container) {
            console.warn('[Ticker] Container not found');
            return;
        }

        console.log('[Ticker] Initializing...');

        // Pause on hover
        this.container.addEventListener('mouseenter', () => {
            this.isPaused = true;
        });

        this.container.addEventListener('mouseleave', () => {
            this.isPaused = false;
        });

        // Initial render
        this.render();
    }

    update(results) {
        this.results = results.slice(0, 30); // Keep last 30 results
        this.render();
    }

    render() {
        if (!this.container) return;

        // Duplicate results for seamless loop
        const displayResults = [...this.results, ...this.results];

        this.container.innerHTML = displayResults.map((result, index) => {
            const isNumber = !result.includes(' ') && !result.includes('Flip') && !result.includes('Hunt');
            const typeClass = isNumber ? 'number' : 'bonus';
            const displayResult = this.formatResult(result);

            return `
                <div class="ticker-item ${typeClass}" style="animation-delay: ${-index * 0.5}s">
                    ${displayResult}
                </div>
            `;
        }).join('');

        // Add separators
        this.addSeparators();
    }

    addSeparators() {
        const items = this.container.querySelectorAll('.ticker-item');

        items.forEach((item, index) => {
            if (index < items.length - 1) {
                const separator = document.createElement('span');
                separator.className = 'ticker-separator';
                separator.textContent = '|';
                item.after(separator);
            }
        });
    }

    formatResult(result) {
        if (result === 'CoinFlip') return 'COINFLIP';
        if (result === 'CashHunt') return 'CASH HUNT';
        if (result === 'Pachinko') return 'PACHINKO';
        if (result === 'CrazyTime') return 'CRAZYTIME';
        return result;
    }

    // Start the ticker animation
    start() {
        this.container.style.animation = `ticker-scroll ${this.animationDuration}ms linear infinite`;
    }

    // Pause the ticker
    pause() {
        this.container.style.animationPlayState = 'paused';
        this.isPaused = true;
    }

    // Resume the ticker
    resume() {
        this.container.style.animationPlayState = 'running';
        this.isPaused = false;
    }

    // Set custom speed
    setSpeed(duration) {
        this.animationDuration = duration;
        this.container.style.animationDuration = `${duration}ms`;
    }

    // Add new result to ticker
    addResult(result) {
        this.results.unshift(result);

        // Remove old results if too many
        if (this.results.length > 50) {
            this.results.pop();
        }

        this.render();
    }
}

// Export
window.DashboardTicker = DashboardTicker;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardTicker = new DashboardTicker();
});
