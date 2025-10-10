// Utility functions for SubDeck for YouTube

// Global toast manager variable
let toastManager = null;

// Toast notification system
class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create container if it doesn't exist
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'fixed top-4 right-4 z-50 space-y-2 pointer-events-none';
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} bg-white shadow-lg rounded-lg p-4 flex items-center gap-3 animate-slide-in pointer-events-auto`;

        const icon = this.getIcon(type);
        const iconColor = this.getIconColor(type);

        toast.innerHTML = `
            <i class="${icon} ${iconColor} text-xl flex-shrink-0"></i>
            <span class="flex-1">${message}</span>
            <button class="flex-shrink-0 hover:bg-gray-100 rounded p-1 transition-colors"
                    onclick="this.parentElement.remove()">
                <i class="fas fa-times text-gray-400"></i>
            </button>
        `;

        this.container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            toast.classList.add('animate-slide-out');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }, duration);
    }

    getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    getIconColor(type) {
        const colors = {
            success: 'text-green-500',
            error: 'text-red-500',
            warning: 'text-yellow-500',
            info: 'text-blue-500'
        };
        return colors[type] || colors.info;
    }
}

// Initialize toast manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    toastManager = new ToastManager();
});

// Global function for showing toasts
function showToast(message, type = 'info', duration = 3000) {
    if (toastManager) {
        toastManager.show(message, type, duration);
    } else {
        // Fallback if toast manager isn't ready yet
        console.log(`Toast (${type}): ${message}`);
    }
}

// Auto-refresh manager
class AutoRefresh {
    constructor(intervalMinutes = 5) {
        this.intervalMinutes = intervalMinutes;
        this.intervalId = null;
        this.enabled = false;
    }

    start() {
        if (this.intervalId) return;

        this.enabled = true;
        this.intervalId = setInterval(() => {
            this.refresh();
        }, this.intervalMinutes * 60 * 1000);

        console.log(`Auto-refresh started: every ${this.intervalMinutes} minutes`);
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            this.enabled = false;
            console.log('Auto-refresh stopped');
        }
    }

    async refresh() {
        console.log('Auto-refreshing data...');

        try {
            // Reload channels and videos
            await Alpine.store('channels').load();

            // Reload videos for each channel
            const channels = Alpine.store('channels').items;
            for (const channel of channels) {
                await Alpine.store('videos').loadForChannel(channel.id);
            }

            // Reload stats
            await Alpine.store('stats').load();

            // Show notification
            showToast('Data refreshed successfully', 'success');
        } catch (error) {
            console.error('Auto-refresh failed:', error);
            showToast('Failed to refresh data', 'error');
        }
    }

    setInterval(minutes) {
        this.intervalMinutes = minutes;
        if (this.enabled) {
            this.stop();
            this.start();
        }
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

function formatDuration(seconds) {
    if (!seconds || seconds === 0) return 'LIVE';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

function formatViewCount(count) {
    if (!count) return '0';

    if (count >= 1000000) {
        return (count / 1000000).toFixed(1) + 'M';
    } else if (count >= 1000) {
        return (count / 1000).toFixed(1) + 'K';
    } else {
        return count.toString();
    }
}

function truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard', 'success');
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    try {
        document.execCommand('copy');
        showToast('Copied to clipboard', 'success');
    } catch (err) {
        showToast('Failed to copy', 'error');
    }
    document.body.removeChild(textArea);
}

function openVideo(videoId, authuser = 0) {
    const url = `https://www.youtube.com/watch?v=${videoId}&authuser=${authuser}`;
    window.open(url, '_blank');
}

function getVideoThumbnail(videoId, quality = 'medium') {
    const qualities = {
        'default': `https://img.youtube.com/vi/${videoId}/default.jpg`,
        'medium': `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
        'high': `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
        'maxres': `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`
    };
    return qualities[quality] || qualities.medium;
}

// Export utilities
window.utils = {
    debounce,
    throttle,
    formatDuration,
    formatViewCount,
    truncateText,
    copyToClipboard,
    openVideo,
    getVideoThumbnail
};