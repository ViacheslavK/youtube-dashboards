// Main application logic for YouTube Dashboard
// Note: initializeApp is now called from index.html on alpine:init

async function initializeApp() {
    // Load settings and initialize stores
    await Alpine.store('app').init();

    // Load initial data
    try {
        console.log('Starting to load channels and stats...');
        await Promise.all([
            Alpine.store('channels').load(),
            Alpine.store('stats').load()
        ]);
        console.log('Channels and stats loaded successfully');

        // Set up channel column creation when channels change
        setupChannelColumns();

        // Also create columns immediately after loading
        const channels = Alpine.store('channels').items;
        console.log('Channels loaded:', channels.length, 'channels');
        if (channels && channels.length > 0) {
            createChannelColumns(channels);
        }
    } catch (error) {
        console.error('Error during initial data loading:', error);
    } finally {
        // Always set loading to false, even if there were errors
        Alpine.store('app').setLoading(false);
    }

    // Set up global error handling
    window.addEventListener('error', (event) => {
        console.error('Global error:', event.error);
        if (typeof showToast === 'function') {
            showToast('An unexpected error occurred', 'error');
        }
    });

    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        if (typeof showToast === 'function') {
            showToast('An unexpected error occurred', 'error');
        }
    });

    // Set up keyboard shortcuts
    setupKeyboardShortcuts();

    // Initialize auto-refresh
    if (Alpine.store('app').autoRefresh) {
        Alpine.store('app').startAutoRefresh();
    }

}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
        // Don't interfere when user is typing in inputs
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.isContentEditable) {
            return;
        }

        // Global shortcuts
        switch(event.key) {
            case 'r':
            case 'R':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    Alpine.store('app').refresh();
                    showToast('Refreshing data...', 'info');
                }
                break;

            case 'l':
            case 'L':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    const langSelector = document.querySelector('select[x-model="$store.app.locale"]');
                    if (langSelector) {
                        langSelector.focus();
                    }
                }
                break;

            case '?':
                if (event.shiftKey) {
                    event.preventDefault();
                    showKeyboardShortcutsHelp();
                }
                break;

            case 'Escape':
                event.preventDefault();
                closeAllModals();
                break;

            case ' ': // Spacebar - mark focused video as watched
                event.preventDefault();
                handleGlobalVideoWatch();
                break;

            case 'w':
            case 'W':
                event.preventDefault();
                handleGlobalVideoWatch();
                break;

            case 'Enter':
                event.preventDefault();
                handleGlobalVideoOpen();
                break;

            case 'ArrowUp':
                event.preventDefault();
                focusPreviousVideo();
                break;

            case 'ArrowDown':
                event.preventDefault();
                focusNextVideo();
                break;

            case 'ArrowLeft':
                event.preventDefault();
                focusPreviousColumn();
                break;

            case 'ArrowRight':
                event.preventDefault();
                focusNextColumn();
                break;
        }
    });
}

// Global video interaction handlers
function handleGlobalVideoWatch() {
    const focusedVideo = document.querySelector('.video-card.focused');
    if (focusedVideo) {
        const watchBtn = focusedVideo.querySelector('.watch-btn');
        if (watchBtn && !watchBtn.disabled) {
            watchBtn.click();
        }
    }
}

function handleGlobalVideoOpen() {
    const focusedVideo = document.querySelector('.video-card.focused');
    if (focusedVideo) {
        const openBtn = focusedVideo.querySelector('.open-btn');
        if (openBtn) {
            openBtn.click();
        }
    }
}

function focusPreviousVideo() {
    const focusedVideo = document.querySelector('.video-card.focused');
    if (focusedVideo) {
        const prevVideo = focusedVideo.previousElementSibling;
        if (prevVideo && prevVideo.classList.contains('video-card')) {
            focusedVideo.classList.remove('focused');
            prevVideo.classList.add('focused');
            prevVideo.focus();
        }
    }
}

function focusNextVideo() {
    const focusedVideo = document.querySelector('.video-card.focused');
    if (!focusedVideo) {
        // Focus first video if none focused
        const firstVideo = document.querySelector('.video-card');
        if (firstVideo) {
            firstVideo.classList.add('focused');
            firstVideo.focus();
        }
    } else {
        const nextVideo = focusedVideo.nextElementSibling;
        if (nextVideo && nextVideo.classList.contains('video-card')) {
            focusedVideo.classList.remove('focused');
            nextVideo.classList.add('focused');
            nextVideo.focus();
        }
    }
}

function focusPreviousColumn() {
    // Column navigation logic would go here
    console.log('Focus previous column');
}

function focusNextColumn() {
    // Column navigation logic would go here
    console.log('Focus next column');
}

function closeAllModals() {
    // Close any open modals or dropdowns
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.classList.add('hidden');
    });
}

function showKeyboardShortcutsHelp() {
    const shortcuts = [
        { key: 'Space / W', description: 'Mark video as watched' },
        { key: 'Enter', description: 'Open video' },
        { key: 'Ctrl+R', description: 'Refresh all data' },
        { key: 'Ctrl+L', description: 'Focus language selector' },
        { key: '↑/↓', description: 'Navigate between videos' },
        { key: '←/→', description: 'Navigate between columns' },
        { key: 'Esc', description: 'Close modals/dropdowns' },
        { key: 'Shift+?', description: 'Show this help' }
    ];

    const helpContent = `
        <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-md mx-4">
                <h3 class="text-lg font-semibold mb-4">Keyboard Shortcuts</h3>
                <div class="space-y-2">
                    ${shortcuts.map(shortcut => `
                        <div class="flex justify-between">
                            <span class="font-mono text-sm bg-gray-100 px-2 py-1 rounded">${shortcut.key}</span>
                            <span class="text-sm text-gray-600">${shortcut.description}</span>
                        </div>
                    `).join('')}
                </div>
                <div class="mt-6 text-center">
                    <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', helpContent);
}

// Utility functions for templates
function getVideoThumbnail(videoId, quality = 'medium') {
    const qualities = {
        'default': `https://img.youtube.com/vi/${videoId}/default.jpg`,
        'medium': `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
        'high': `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
        'maxres': `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`
    };
    return qualities[quality] || qualities.medium;
}

function formatDate(dateString, format = 'MMM D, YYYY') {
    if (!dateString) return '';
    return dayjs(dateString).format(format);
}

function formatRelative(dateString) {
    if (!dateString) return '';
    return dayjs(dateString).fromNow();
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

// Channel column management
let channelColumns = new Map(); // Store ChannelColumn instances

function setupChannelColumns() {
    // Watch for changes in channels store
    Alpine.effect(() => {
        const channels = Alpine.store('channels').items;

        if (channels && channels.length > 0) {
            createChannelColumns(channels);
        } else {
            clearChannelColumns();
        }
    });
}

function createChannelColumns(channels) {
    const container = document.getElementById('channels-container');
    if (!container) {
        console.error('Channels container not found');
        return;
    }

    console.log(`Creating ${channels.length} channel columns`);

    // Clear existing columns
    clearChannelColumns();

    // Create column for each channel
    channels.forEach(channel => {
        console.log(`Creating column for channel: ${channel.name} (ID: ${channel.id})`);

        const column = createChannelColumn(
            channel,
            (videoId) => handleVideoWatch(videoId),
            (videoId) => handleVideoOpen(videoId),
            (channelId) => handleClearWatched(channelId)
        );

        container.appendChild(column.element);
        channelColumns.set(channel.id, column);

        // Load videos for this channel
        column.loadVideos();
    });
}

function clearChannelColumns() {
    console.log('Clearing channel columns');

    channelColumns.forEach(column => {
        column.destroy();
    });
    channelColumns.clear();

    const container = document.getElementById('channels-container');
    if (container) {
        container.innerHTML = '';
    }
}

// Video event handlers
async function handleVideoWatch(videoId) {
    console.log(`Handling video watch: ${videoId}`);

    // Find the column that contains this video
    for (const [channelId, column] of channelColumns) {
        if (column.videos.some(v => v.id === videoId)) {
            return await column.handleVideoWatch(videoId);
        }
    }
    return false;
}

async function handleVideoOpen(videoId) {
    console.log(`Handling video open: ${videoId}`);

    // Get video details and open in YouTube
    try {
        const response = await api.getVideo(videoId);
        if (response.success) {
            const video = response.data;
            const url = `https://www.youtube.com/watch?v=${video.youtube_video_id}&authuser=${video.authuser_index || 0}`;
            window.open(url, '_blank');
            showToast('Video opened in new tab', 'success');
        } else {
            showToast('Failed to open video', 'error');
        }
    } catch (error) {
        console.error('Error opening video:', error);
        showToast('Failed to open video', 'error');
    }
}

async function handleClearWatched(channelId) {
    console.log(`Handling clear watched for channel: ${channelId}`);

    const column = channelColumns.get(channelId);
    if (column) {
        return await column.handleClearWatched();
    }
    return false;
}

// Make functions globally available
window.appUtils = {
    getVideoThumbnail,
    formatDate,
    formatRelative,
    formatDuration,
    formatViewCount
};