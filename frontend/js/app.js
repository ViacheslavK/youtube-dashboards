// Main application logic for SubDeck for YouTube
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

    // Global function to safely check if value includes substring
    window.safeIncludes = function(value, searchString) {
        if (value === null || value === undefined) {
            return false;
        }
        return String(value).includes(searchString);
    };

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

// Column navigation for keyboard shortcuts
let currentColumnIndex = 0;

function focusPreviousColumn() {
    const columns = document.querySelectorAll('.channel-column');
    if (columns.length === 0) return;

    currentColumnIndex = Math.max(0, currentColumnIndex - 1);
    focusColumn(columns[currentColumnIndex]);
}

function focusNextColumn() {
    const columns = document.querySelectorAll('.channel-column');
    if (columns.length === 0) return;

    currentColumnIndex = Math.min(columns.length - 1, currentColumnIndex + 1);
    focusColumn(columns[currentColumnIndex]);
}

function focusColumn(column) {
    // Remove focus from all videos
    document.querySelectorAll('.video-card.focused').forEach(video => {
        video.classList.remove('focused');
    });

    // Focus the first video in the target column
    const firstVideo = column.querySelector('.video-card');
    if (firstVideo) {
        firstVideo.classList.add('focused');
        firstVideo.focus();
        // Scroll column into view if needed
        column.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
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

    // Set up drag and drop for column reordering
    setupColumnDragAndDrop();
}

function createChannelColumns(channels) {
    const container = document.getElementById('channels-container');
    if (!container) {
        // Admin panel doesn't have channels container - skip video column creation
        console.log('Channels container not found - skipping video column creation (likely admin panel)');
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

        // Store channel ID on the element for drag and drop
        column.element.setAttribute('data-channel-id', channel.id);
        column.element.__channelId = channel.id;

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

// === Drag and Drop Column Reordering ===

function setupColumnDragAndDrop() {
    const container = document.getElementById('channels-container');
    if (!container) return;

    let draggedColumnId = null;
    let dropIndicator = null;

    // Create drop indicator element
    function createDropIndicator() {
        if (!dropIndicator) {
            dropIndicator = document.createElement('div');
            dropIndicator.className = 'drop-indicator absolute top-0 bottom-0 w-1 bg-blue-500 transition-all duration-200 pointer-events-none z-50';
            dropIndicator.style.display = 'none';
            container.appendChild(dropIndicator);
        }
        return dropIndicator;
    }

    // Drag over handler for the container
    container.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        const columns = Array.from(container.querySelectorAll('.channel-column'));
        const mouseX = e.clientX;

        // Find the column we're hovering over
        let insertBeforeColumn = null;
        let insertPosition = 0;

        for (let i = 0; i < columns.length; i++) {
            const column = columns[i];
            const rect = column.getBoundingClientRect();

            // Check if mouse is over this column
            if (mouseX >= rect.left && mouseX <= rect.right) {
                // Determine if we should insert before or after this column
                const columnCenter = rect.left + rect.width / 2;

                if (mouseX < columnCenter) {
                    insertBeforeColumn = column;
                    insertPosition = i;
                } else {
                    insertBeforeColumn = columns[i + 1] || null;
                    insertPosition = i + 1;
                }
                break;
            }
        }

        // Position the drop indicator
        const indicator = createDropIndicator();
        if (insertBeforeColumn) {
            const rect = insertBeforeColumn.getBoundingClientRect();
            indicator.style.left = rect.left + 'px';
            indicator.style.display = 'block';
        } else {
            // Insert at the end
            const lastColumn = columns[columns.length - 1];
            if (lastColumn) {
                const rect = lastColumn.getBoundingClientRect();
                indicator.style.left = rect.right + 'px';
                indicator.style.display = 'block';
            }
        }
    });

    // Drag leave handler
    container.addEventListener('dragleave', (e) => {
        // Only hide indicator if we're leaving the container entirely
        if (!container.contains(e.relatedTarget)) {
            if (dropIndicator) {
                dropIndicator.style.display = 'none';
            }
        }
    });

    // Drop handler
    container.addEventListener('drop', async (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (dropIndicator) {
            dropIndicator.style.display = 'none';
        }

        const draggedChannelId = e.dataTransfer.getData('text/plain');
        if (!draggedChannelId) return;

        // Find the column being dragged
        const draggedColumn = container.querySelector(`[data-channel-id="${draggedChannelId}"]`);
        if (!draggedColumn) return;

        const columns = Array.from(container.querySelectorAll('.channel-column'));
        const mouseX = e.clientX;

        // Calculate new position
        let newIndex = columns.length; // Default to end

        for (let i = 0; i < columns.length; i++) {
            const column = columns[i];
            const rect = column.getBoundingClientRect();

            // Check if mouse is over this column
            if (mouseX >= rect.left && mouseX <= rect.right) {
                // Determine if we should insert before or after this column
                const columnCenter = rect.left + rect.width / 2;
                newIndex = mouseX < columnCenter ? i : i + 1;
                break;
            }
        }

        // Reorder columns in DOM
        reorderColumnsInDOM(draggedChannelId, newIndex);

        // Update order in Alpine store and persist to backend
        try {
            await updateColumnOrder();
            showToast('Column order updated', 'success');
        } catch (error) {
            console.error('Error updating column order:', error);
            showToast('Failed to save column order', 'error');
        }
    });
}

function reorderColumnsInDOM(draggedChannelId, newIndex) {
    const container = document.getElementById('channels-container');
    const columns = Array.from(container.querySelectorAll('.channel-column'));
    const draggedColumn = container.querySelector(`[data-channel-id="${draggedChannelId}"]`);

    if (!draggedColumn) return;

    // Remove dragged column from current position
    draggedColumn.remove();

    // Insert at new position
    if (newIndex >= columns.length) {
        container.appendChild(draggedColumn);
    } else {
        const referenceColumn = columns[newIndex];
        container.insertBefore(draggedColumn, referenceColumn);
    }
}

async function updateColumnOrder() {
    const container = document.getElementById('channels-container');
    if (!container) return;

    const columns = Array.from(container.querySelectorAll('.channel-column'));

    // Extract channel IDs in new order
    const newOrder = columns.map(column => {
        return column.getAttribute('data-channel-id');
    }).filter(Boolean);

    if (newOrder.length === 0) return;

    // Update Alpine store
    const channelsStore = Alpine.store('channels');
    if (!channelsStore) return;

    const currentChannels = [...channelsStore.items];

    // Reorder channels array to match DOM order
    const reorderedChannels = newOrder.map(id => currentChannels.find(c => c.id == id)).filter(Boolean);

    // Update order_position for each channel
    const updatedChannels = reorderedChannels.map((channel, index) => ({
        ...channel,
        order_position: index
    }));

    // Update store
    channelsStore.items = updatedChannels;

    // Persist to backend
    try {
        for (const channel of updatedChannels) {
            await api.updateChannel(channel.id, { order_position: channel.order_position });
        }
    } catch (error) {
        console.error('Failed to persist column order:', error);
        showToast('Failed to save column order', 'error');
        throw error;
    }
}

// Make functions globally available
window.appUtils = {
    getVideoThumbnail,
    formatDate,
    formatRelative,
    formatDuration,
    formatViewCount
};

// Make updateColumnOrder globally available for testing
window.updateColumnOrder = updateColumnOrder;