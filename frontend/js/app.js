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
        // Ctrl/Cmd + R to refresh data
        if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
            event.preventDefault();
            Alpine.store('app').refresh();
            showToast('Refreshing data...', 'info');
        }

        // Ctrl/Cmd + L to focus language selector
        if ((event.ctrlKey || event.metaKey) && event.key === 'l') {
            event.preventDefault();
            const langSelector = document.querySelector('select[x-model="$store.app.locale"]');
            if (langSelector) {
                langSelector.focus();
            }
        }
    });
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