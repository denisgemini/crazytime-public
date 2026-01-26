/**
 * CrazyTime v2 Dashboard - UI Animations
 * Handles CSS animations and transitions
 */

const DashboardAnimations = {
    // Neon glow pulse animation
    createGlowPulse(element, color, duration = 2000) {
        element.classList.add('glow-pulse');
        element.style.setProperty('--glow-color', color);
    },

    // Fade in animation
    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.transition = `opacity ${duration}ms ease`;

        requestAnimationFrame(() => {
            element.style.opacity = '1';
        });
    },

    // Fade out animation
    fadeOut(element, duration = 300) {
        return new Promise(resolve => {
            element.style.transition = `opacity ${duration}ms ease`;
            element.style.opacity = '0';

            setTimeout(() => {
                element.style.display = 'none';
                resolve();
            }, duration);
        });
    },

    // Flash animation for updates
    flash(element, color = 'rgba(0, 212, 255, 0.3)') {
        element.classList.add('flash-update');
        element.style.backgroundColor = color;

        setTimeout(() => {
            element.classList.remove('flash-update');
            element.style.backgroundColor = '';
        }, 500);
    },

    // Scale bounce animation
    scaleBounce(element, scale = 1.1, duration = 200) {
        element.style.transition = `transform ${duration}ms cubic-bezier(0.175, 0.885, 0.32, 1.275)`;
        element.style.transform = `scale(${scale})`;

        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, duration);
    },

    // Slide in animation
    slideIn(element, direction = 'left', duration = 400) {
        const transforms = {
            left: { x: -50, y: 0 },
            right: { x: 50, y: 0 },
            top: { x: 0, y: -30 },
            bottom: { x: 0, y: 30 }
        };

        const transform = transforms[direction] || transforms.left;

        element.style.opacity = '0';
        element.style.transform = `translate(${transform.x}px, ${transform.y}px)`;
        element.style.transition = `all ${duration}ms ease`;

        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'translate(0, 0)';
        });
    },

    // Number counter animation
    animateCounter(element, from, to, duration = 1000, prefix = '', suffix = '') {
        const startTime = performance.now();
        const diff = to - from;

        if (diff === 0) {
            element.textContent = `${prefix}${from.toLocaleString()}${suffix}`;
            return;
        }

        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out cubic
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(from + diff * easeOut);

            element.textContent = `${prefix}${current.toLocaleString()}${suffix}`;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };

        requestAnimationFrame(update);
    },

    // Progress bar animation
    animateProgressBar(element, to, duration = 1000) {
        const from = parseFloat(element.style.width) || 0;

        element.style.transition = `width ${duration}ms ease`;
        element.style.width = `${to}%`;
    },

    // Ring progress animation
    animateRing(element, to, duration = 1000) {
        const circumference = 2 * Math.PI * 52;
        const fromOffset = parseFloat(element.style.strokeDashoffset) || circumference;

        element.style.transition = `stroke-dashoffset ${duration}ms ease`;
        element.style.strokeDashoffset = circumference * (1 - to / 100);
    },

    // Stagger children animation
    staggerIn(container, childSelector, delay = 50) {
        const children = container.querySelectorAll(childSelector);

        children.forEach((child, index) => {
            child.style.opacity = '0';
            child.style.transform = 'translateY(20px)';
            child.style.transition = 'all 0.4s ease';

            setTimeout(() => {
                child.style.opacity = '1';
                child.style.transform = 'translateY(0)';
            }, index * delay);
        });
    },

    // Shake animation for alerts
    shake(element, intensity = 10, duration = 500) {
        element.style.animation = `shake ${duration}ms ease-in-out`;

        setTimeout(() => {
            element.style.animation = '';
        }, duration);
    },

    // Add shake keyframes dynamically
    addShakeKeyframes() {
        if (document.querySelector('#shake-keyframes')) return;

        const style = document.createElement('style');
        style.id = 'shake-keyframes';
        style.textContent = `
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
                20%, 40%, 60%, 80% { transform: translateX(5px); }
            }
        `;
        document.head.appendChild(style);
    },

    // Celebration animation
    celebrate(element, color = '#00ff88') {
        // Add particles or glow effect
        element.style.boxShadow = `0 0 50px ${color}, 0 0 100px ${color}50`;

        setTimeout(() => {
            element.style.boxShadow = '';
        }, 1000);
    },

    // Parallax effect
    parallax(element, mouseX, mouseY, intensity = 10) {
        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const deltaX = (mouseX - centerX) / centerX;
        const deltaY = (mouseY - centerY) / centerY;

        element.style.transform = `translate(${deltaX * intensity}px, ${deltaY * intensity}px)`;
    }
};

// Add shake keyframes on load
DashboardAnimations.addShakeKeyframes();

// Export
window.DashboardAnimations = DashboardAnimations;
