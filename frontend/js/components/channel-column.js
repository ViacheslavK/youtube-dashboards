// Channel Column Component for SubDeck for YouTube
// Simple HTML escape to safely inject dynamic strings into innerHTML/attributes
function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&')
        .replace(/</g, '<')
        .replace(/>/g, '>')
        .replace(/"/g, '"')
        .replace(/'/g, '"');
}

class ChannelColumn {
    constructor(channelData, onVideoWatch, onVideoOpen, onClearWatched) {
        this.channel = channelData;
        this.onVideoWatch = onVideoWatch;
        this.onVideoOpen = onVideoOpen;
        this.onClearWatched = onClearWatched;
        this.videos = [];
        this.loading = false;
        this.element = null;
        this.videoCards = new Map(); // Store video card instances
        this.searchTerm = '';
        this.sortBy = 'date';
        this.sortOrder = 'desc'; // newest first
        this.searchDebounceTimer = null;
        this.render();
    }

    render() {
        // Create the channel column element
        this.element = document.createElement('div');
        this.element.className = 'flex-shrink-0 w-96 bg-white rounded-lg shadow-sm border overflow-hidden channel-column';
        this.element.innerHTML = this.getTemplate();

        // Add event listeners
        this.attachEventListeners();

        return this.element;
    }

    getTemplate() {
        return `
            <!-- Channel Header -->
            <div class="p-4 border-b bg-gray-50">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3 flex-1">
                        <!-- Drag Handle -->
                        <div class="drag-handle cursor-move text-gray-400 hover:text-gray-600 p-1"
                             title="Drag to reorder column"
                             draggable="true"
                             role="button"
                             aria-label="Drag to reorder column"
                             aria-describedby="column-reorder-help"
                             tabindex="0">
                            <i class="fas fa-grip-vertical text-sm"></i>
                        </div>

                        <div class="w-4 h-4 rounded-full flex-shrink-0"
                             style="background-color: ${this.channel.color}"></div>
                        <div class="min-w-0 flex-1">
                            <h3 class="font-semibold text-gray-900 truncate text-sm"
                                title="${escapeHtml(this.channel.name)}">
                                ${escapeHtml(this.channel.name)}
                            </h3>
                            <p class="text-xs text-gray-600">
                                ${this.channel.stats ? `${this.channel.stats.unwatched_videos} unwatched` : 'Loading...'}
                            </p>
                        </div>
                    </div>
                    <div class="flex items-center space-x-1">
                        <button class="text-gray-400 hover:text-gray-600 p-1 refresh-btn"
                                title="Refresh videos">
                            <i class="fas fa-sync-alt text-xs"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Search and Sort Controls -->
            <div class="px-4 py-2 bg-gray-50 border-b">
                <div class="flex gap-2">
                    <!-- Search Input -->
                    <div class="flex-1 relative flex items-center">
                        <input type="text"
                               class="w-full pl-8 pr-8 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 search-input"
                               placeholder="${t('videos.search_placeholder')}"
                               value="${this.searchTerm}">
                        <i class="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xs"></i>
                        <button class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 clear-search-btn ${this.searchTerm ? '' : 'hidden'}"
                                title="Clear search"
                                type="button">
                            <i class="fas fa-times text-xs"></i>
                        </button>
                    </div>

                    <!-- Sort Dropdown -->
                    <div class="relative">
                        <select class="appearance-none bg-white border border-gray-300 rounded-md px-3 py-2 pr-8 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sort-select">
                            <option value="date-desc" ${this.sortBy === 'date' && this.sortOrder === 'desc' ? 'selected' : ''} data-i18n-key="videos.sort_date_newest">${t('videos.sort_date_newest')}</option>
                            <option value="date-asc" ${this.sortBy === 'date' && this.sortOrder === 'asc' ? 'selected' : ''} data-i18n-key="videos.sort_date_oldest">${t('videos.sort_date_oldest')}</option>
                            <option value="title-asc" ${this.sortBy === 'title' && this.sortOrder === 'asc' ? 'selected' : ''} data-i18n-key="videos.sort_title_az">${t('videos.sort_title_az')}</option>
                            <option value="title-desc" ${this.sortBy === 'title' && this.sortOrder === 'desc' ? 'selected' : ''} data-i18n-key="videos.sort_title_za">${t('videos.sort_title_za')}</option>
                            <option value="views-desc" ${this.sortBy === 'views' && this.sortOrder === 'desc' ? 'selected' : ''} data-i18n-key="videos.sort_views_most">${t('videos.sort_views_most')}</option>
                            <option value="views-asc" ${this.sortBy === 'views' && this.sortOrder === 'asc' ? 'selected' : ''} data-i18n-key="videos.sort_views_least">${t('videos.sort_views_least')}</option>
                            <option value="duration-desc" ${this.sortBy === 'duration' && this.sortOrder === 'desc' ? 'selected' : ''} data-i18n-key="videos.sort_duration_longest">${t('videos.sort_duration_longest')}</option>
                            <option value="duration-asc" ${this.sortBy === 'duration' && this.sortOrder === 'asc' ? 'selected' : ''} data-i18n-key="videos.sort_duration_shortest">${t('videos.sort_duration_shortest')}</option>
                        </select>
                        <i class="fas fa-chevron-down absolute right-3 top-3 text-gray-400 text-xs pointer-events-none"></i>
                    </div>
                </div>
            </div>

            <!-- Videos Container -->
            <div class="flex-1 overflow-y-auto max-h-[32rem] custom-scrollbar videos-container">
                <!-- Loading State -->
                <div class="loading-state flex justify-center items-center py-8 ${this.loading ? '' : 'hidden'}">
                    <div class="text-center">
                        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
                        <p class="text-sm text-gray-600">Loading videos...</p>
                    </div>
                </div>

                <!-- Videos List -->
                <div class="videos-list">
                    ${this.videos.length === 0 && !this.loading ? this.getEmptyState() : ''}
                </div>
            </div>

            <!-- Footer -->
            <div class="p-3 bg-gray-50 border-t">
                <button class="w-full text-sm text-red-600 hover:text-red-800 font-medium py-2 px-3 rounded-md hover:bg-red-50 transition-colors duration-200 clear-btn ${this.getUnwatchedCount() === 0 ? 'opacity-50 cursor-not-allowed' : ''}"
                        ${this.getUnwatchedCount() === 0 ? 'disabled' : ''}
                        title="Clear all watched videos">
                    <i class="fas fa-trash mr-1"></i>
                    <span x-t="'videos.clear_watched'">Clear Watched</span>
                    ${this.getUnwatchedCount() > 0 ? ` (${this.getUnwatchedCount()})` : ''}
                </button>
            </div>
        `;
    }

    getEmptyState() {
        return `
            <div class="text-center py-12 px-4">
                <i class="fas fa-inbox text-4xl text-gray-300 mb-3"></i>
                <h4 class="text-sm font-medium text-gray-900 mb-1" x-t="'videos.no_videos'">No videos</h4>
                <p class="text-xs text-gray-500" x-t="'videos.no_videos_desc'">New videos will appear here</p>
            </div>
        `;
    }

    attachEventListeners() {
        // Drag handle for column reordering
        const dragHandle = this.element.querySelector('.drag-handle');
        if (dragHandle) {
            this.attachDragListeners(dragHandle);
        }

        // Refresh button
        const refreshBtn = this.element.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshVideos();
            });
        }

        // Clear watched button
        const clearBtn = this.element.querySelector('.clear-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.handleClearWatched();
            });
        }

        // Search input with debounce
        const searchInput = this.element.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });

            // Update placeholder when language changes
            Alpine.effect(() => {
                const locale = Alpine.store('app').locale;
                const version = Alpine.store('app').i18nVersion;
                void locale; void version; // ensure dependencies
                searchInput.placeholder = t('videos.search_placeholder');
            });
        }

        // Sort select
        const sortSelect = this.element.querySelector('.sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.handleSortChange(e.target.value);
            });

            // Update option texts when language changes
            Alpine.effect(() => {
                const locale = Alpine.store('app').locale;
                const version = Alpine.store('app').i18nVersion;
                void locale; void version;
                const options = sortSelect.querySelectorAll('option');
                options.forEach(option => {
                    const key = option.getAttribute('data-i18n-key');
                    if (key) {
                        option.textContent = t(key);
                    }
                });
            });
        }

        // Clear search button
        const clearSearchBtn = this.element.querySelector('.clear-search-btn');
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', () => {
                this.handleSearchInput('');
                const input = this.element.querySelector('.search-input');
                if (input) input.value = '';
            });
        }
    }

    attachDragListeners(dragHandle) {
        // Desktop drag and drop
        dragHandle.addEventListener('dragstart', (e) => {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', this.channel.id);

            // Add visual feedback
            this.element.classList.add('dragging');
            dragHandle.classList.add('text-blue-600');

            // Set drag image to the entire column for better UX
            const dragImage = this.element.cloneNode(true);
            dragImage.style.transform = 'rotate(-2deg)';
            dragImage.style.opacity = '0.8';
            e.dataTransfer.setDragImage(dragImage, e.offsetX, e.offsetY);

        });

        dragHandle.addEventListener('dragend', () => {
            this.element.classList.remove('dragging');
            dragHandle.classList.remove('text-blue-600');
        });

        // Mobile touch support
        this.attachTouchListeners(dragHandle);

        // Keyboard accessibility
        this.attachKeyboardListeners(dragHandle);

        // Prevent default drag behavior on the column itself
        this.element.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            e.stopPropagation(); // Prevent event bubbling to container
        });
    }

    attachTouchListeners(dragHandle) {
        let isDragging = false;
        let startX, startY;
        let currentX, currentY;
        let dragOverlay = null;

        // Touch start
        dragHandle.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
            isDragging = false;

            // Add visual feedback
            dragHandle.classList.add('text-blue-600');

            // Prevent scrolling while touching drag handle
            e.preventDefault();
        }, { passive: false });

        // Touch move
        dragHandle.addEventListener('touchmove', (e) => {
            if (!startX || !startY) return;

            const touch = e.touches[0];
            currentX = touch.clientX;
            currentY = touch.clientY;

            // If moved more than 10px, consider it a drag
            const deltaX = Math.abs(currentX - startX);
            const deltaY = Math.abs(currentY - startY);

            if (deltaX > 10 || deltaY > 10) {
                if (!isDragging) {
                    isDragging = true;
                    this.startMobileDrag(dragHandle);
                }

                // Update drag overlay position
                if (dragOverlay) {
                    dragOverlay.style.left = (currentX - 50) + 'px';
                    dragOverlay.style.top = (currentY - 25) + 'px';
                }

                // Find drop target
                this.updateMobileDropTarget(e.target, currentX, currentY);
            }

            e.preventDefault();
        }, { passive: false });

        // Touch end
        dragHandle.addEventListener('touchend', (e) => {
            if (isDragging) {
                this.endMobileDrag();
            }

            // Remove visual feedback
            dragHandle.classList.remove('text-blue-600');
            startX = startY = null;
            isDragging = false;

            e.preventDefault();
        }, { passive: false });
    }

    startMobileDrag(dragHandle) {

        // Create drag overlay
        const dragOverlay = document.createElement('div');
        dragOverlay.className = 'fixed pointer-events-none z-50 bg-white rounded-lg shadow-lg border p-2 opacity-90';
        dragOverlay.style.width = '200px';
        dragOverlay.style.height = '100px';
        dragOverlay.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-grip-vertical text-gray-400"></i>
                <div class="w-3 h-3 rounded-full" style="background-color: ${this.channel.color}"></div>
                <span class="text-sm font-medium truncate">${this.escapeHtml(this.channel.name)}</span>
            </div>
        `;

        document.body.appendChild(dragOverlay);
        this.dragOverlay = dragOverlay;

        // Add dragging class to column
        this.element.classList.add('dragging');
    }

    updateMobileDropTarget(touchTarget, x, y) {
        // Find the column we're hovering over
        const columns = Array.from(document.querySelectorAll('.channel-column'));
        let targetColumn = null;

        for (const column of columns) {
            const rect = column.getBoundingClientRect();
            if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
                targetColumn = column;
                break;
            }
        }

        // Update visual feedback
        columns.forEach(col => col.classList.remove('drag-over'));
        if (targetColumn && targetColumn !== this.element) {
            targetColumn.classList.add('drag-over');
        }
    }

    endMobileDrag() {

        // Remove drag overlay
        if (this.dragOverlay) {
            this.dragOverlay.remove();
            this.dragOverlay = null;
        }

        // Remove dragging class
        this.element.classList.remove('dragging');

        // Remove all drag-over classes
        document.querySelectorAll('.channel-column.drag-over').forEach(col => {
            col.classList.remove('drag-over');
        });

        // Trigger column reordering if we were over a valid drop target
        // This would need to be implemented with the main drag and drop logic
        // For now, just show a message
        showToast('Mobile drag and drop completed - full implementation coming soon!', 'info');
    }

    attachKeyboardListeners(dragHandle) {
        dragHandle.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    this.enterReorderMode();
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.exitReorderMode();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.moveColumn(-1);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.moveColumn(1);
                    break;
            }
        });
    }

    enterReorderMode() {
        this.inReorderMode = true;
        this.element.classList.add('reorder-mode');

        // Add visual indication
        const dragHandle = this.element.querySelector('.drag-handle');
        dragHandle.classList.add('ring-2', 'ring-blue-500');

        // Announce to screen readers
        this.announceToScreenReader(`Entered reorder mode for ${this.channel.name}. Use arrow keys to move, Enter to confirm, Escape to cancel.`);

    }

    exitReorderMode() {
        this.inReorderMode = false;
        this.element.classList.remove('reorder-mode');

        // Remove visual indication
        const dragHandle = this.element.querySelector('.drag-handle');
        dragHandle.classList.remove('ring-2', 'ring-blue-500');

        // Announce to screen readers
        this.announceToScreenReader(`Exited reorder mode for ${this.channel.name}`);

    }

    moveColumn(direction) {
        if (!this.inReorderMode) return;

        const container = document.getElementById('channels-container');
        const columns = Array.from(container.querySelectorAll('.channel-column'));
        const currentIndex = columns.indexOf(this.element);

        if (currentIndex === -1) return;

        const newIndex = Math.max(0, Math.min(columns.length - 1, currentIndex + direction));

        if (newIndex !== currentIndex) {
            // Move column in DOM
            if (direction > 0) {
                // Moving right
                if (columns[newIndex]) {
                    container.insertBefore(this.element, columns[newIndex].nextSibling);
                }
            } else {
                // Moving left
                container.insertBefore(this.element, columns[newIndex]);
            }

            // Update order in store and backend
            if (window.updateColumnOrder) {
                window.updateColumnOrder();
            }

            // Announce movement to screen readers
            const position = newIndex + 1;
            const total = columns.length;
            this.announceToScreenReader(`Moved ${this.channel.name} to position ${position} of ${total}`);

            showToast(`Moved column to position ${position}`, 'success');
        }
    }

    announceToScreenReader(message) {
        // Create a live region for screen reader announcements
        let liveRegion = document.getElementById('drag-drop-announcements');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'drag-drop-announcements';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }

        liveRegion.textContent = message;

        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    }

    escapeHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&')
            .replace(/</g, '<')
            .replace(/>/g, '>')
            .replace(/"/g, '"')
            .replace(/'/g, '&#039;');
    }

    // Load videos for this channel
    async loadVideos() {
        if (this.loading) return;

        this.loading = true;
        this.updateLoadingState();

        try {
            const videos = await api.getChannelVideos(this.channel.id, false); // Don't include watched

            // API client already processes response and returns data array directly
            this.videos = videos || [];
            this.renderVideos();
        } catch (error) {
            console.error('Error loading videos for channel', this.channel.id, error);
            this.showError('Failed to load videos');
        } finally {
            this.loading = false;
            this.updateLoadingState();
        }
    }

    // Filter videos based on search term
    getFilteredVideos() {
        if (!this.searchTerm) {
            return this.videos;
        }

        return this.videos.filter(video => {
            if (!video) return false;

            const title = (video.title || '').toLowerCase();
            const channelName = (video.channel_name || '').toLowerCase();

            return title.includes(this.searchTerm) || channelName.includes(this.searchTerm);
        });
    }

    // Sort videos based on current sort settings
    getSortedVideos(videos) {
        return [...videos].sort((a, b) => {
            let aValue, bValue;

            switch (this.sortBy) {
                case 'date':
                    aValue = new Date(a.published_at || 0);
                    bValue = new Date(b.published_at || 0);
                    break;
                case 'title':
                    aValue = (a.title || '').toLowerCase();
                    bValue = (b.title || '').toLowerCase();
                    break;
                case 'views':
                    aValue = parseInt(a.view_count) || 0;
                    bValue = parseInt(b.view_count) || 0;
                    break;
                case 'duration':
                    aValue = parseInt(a.duration) || 0;
                    bValue = parseInt(b.duration) || 0;
                    break;
                default:
                    return 0;
            }

            if (this.sortOrder === 'asc') {
                return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
            } else {
                return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
            }
        });
    }

    // Render videos in the container
    renderVideos() {
        const videosContainer = this.element.querySelector('.videos-list');
        if (!videosContainer) return;

        // Clear existing video cards
        this.clearVideoCards();

        // Remove empty state if it exists
        const emptyState = videosContainer.querySelector('.text-center');
        if (emptyState) {
            emptyState.remove();
        }

        // Get filtered and sorted videos
        const filteredVideos = this.getFilteredVideos();
        const sortedVideos = this.getSortedVideos(filteredVideos);

        // Add video cards with null checking
        sortedVideos.forEach(video => {
            // Skip null or invalid videos
            if (!video || !video.id || !video.youtube_video_id) {
                console.warn('Skipping invalid video:', video);
                return;
            }

            try {
                const videoCard = createVideoCard(
                    video,
                    (videoId) => this.handleVideoWatch(videoId),
                    (videoId) => this.handleVideoOpen(videoId)
                );

                if (videoCard && videoCard.element) {
                    videosContainer.appendChild(videoCard.element);
                    this.videoCards.set(video.id, videoCard);
                }
            } catch (error) {
                console.error('Error creating video card:', error, video);
            }
        });

        // Show empty state if no videos match filter
        if (sortedVideos.length === 0 && this.videos.length > 0) {
            videosContainer.innerHTML = `
                <div class="text-center py-12 px-4">
                    <i class="fas fa-search text-4xl text-gray-300 mb-3"></i>
                    <h4 class="text-sm font-medium text-gray-900 mb-1">No videos found</h4>
                    <p class="text-xs text-gray-500">Try adjusting your search or sort options</p>
                </div>
            `;
        } else if (sortedVideos.length === 0 && this.videos.length === 0 && !this.loading) {
            videosContainer.innerHTML = this.getEmptyState();
        }

        // Update stats
        this.updateStats();
    }

    // Handle video watch
    async handleVideoWatch(videoId) {
        try {
            const success = await api.markVideoWatched(videoId);

            if (success) {
                // Update local video data
                const videoCard = this.videoCards.get(videoId);
                if (videoCard) {
                    const video = videoCard.video;
                    if (video) {
                        video.is_watched = true;

                        // Check if video card is still in DOM
                        if (videoCard.element && videoCard.element.parentNode) {
                            // Element exists, update it to show watched state
                            try {
                                videoCard.updateVideo(video);
                                console.log('Video card updated to watched state');
                            } catch (updateError) {
                                console.error('Error updating video card:', updateError);
                                // If update fails, remove the video instead
                                this.removeVideo(videoId);
                            }
                        } else {
                            // Element not in DOM, just remove from internal data
                            console.log('Video element removed from DOM, removing from internal data');
                            this.removeVideo(videoId);
                        }
                    }
                } else {
                    // Video card not found in our collection
                    console.log('Video card not found in collection, removing from videos array');
                    this.videos = this.videos.filter(v => v.id !== videoId);
                }

                // Update stats (with error handling)
                try {
                    this.updateStats();
                } catch (error) {
                    console.error('Error updating stats:', error);
                }

                return true;
            }
            return false;
        } catch (error) {
            console.error('Error marking video as watched:', error);
            return false;
        }
    }

    // Handle video open
    async handleVideoOpen(videoId) {
        const videoCard = this.videoCards.get(videoId);
        if (videoCard) {
            return videoCard.handleOpen();
        }
    }

    // Handle clear watched videos
    async handleClearWatched() {
        const unwatchedCount = this.getUnwatchedCount();
        if (unwatchedCount === 0) return;

        if (!confirm(`Clear ${unwatchedCount} watched videos from ${this.channel.name}?`)) {
            return;
        }

        try {
            const success = await api.clearWatchedVideos(this.channel.id);

            if (success) {
                // Remove all watched videos from the UI
                const videosToRemove = [];
                this.videoCards.forEach((card, videoId) => {
                    if (card.video.is_watched) {
                        videosToRemove.push(videoId);
                    }
                });

                videosToRemove.forEach(videoId => {
                    this.removeVideo(videoId);
                });

                // Update stats
                this.updateStats();

                showToast(`Cleared ${videosToRemove.length} watched videos`, 'success');
            }
        } catch (error) {
            console.error('Error clearing watched videos:', error);
            showToast('Failed to clear watched videos', 'error');
        }
    }

    // Handle search input with debounce
    handleSearchInput(value) {
        this.searchTerm = value.trim().toLowerCase();

        // Update clear button visibility
        const clearBtn = this.element.querySelector('.clear-search-btn');
        if (clearBtn) {
            clearBtn.classList.toggle('hidden', !this.searchTerm);
        }

        // Clear existing timer
        if (this.searchDebounceTimer) {
            clearTimeout(this.searchDebounceTimer);
        }

        // Set new timer for 300ms debounce
        this.searchDebounceTimer = setTimeout(() => {
            this.renderVideos();
        }, 300);
    }

    // Handle sort change
    handleSortChange(value) {
        const [sortBy, sortOrder] = value.split('-');
        this.sortBy = sortBy;
        this.sortOrder = sortOrder;
        this.renderVideos();
    }

    // Refresh videos
    async refreshVideos() {
        await this.loadVideos();
        showToast(`Refreshed videos for ${this.channel.name}`, 'success');
    }

    // Remove a video from the column
    removeVideo(videoId) {
        const videoCard = this.videoCards.get(videoId);
        if (videoCard) {
            videoCard.destroy();
            this.videoCards.delete(videoId);

            // Remove from videos array
            this.videos = this.videos.filter(v => v.id !== videoId);
        }

        // Show empty state if no videos left
        if (this.videos.length === 0) {
            const videosContainer = this.element.querySelector('.videos-list');
            if (videosContainer) {
                videosContainer.innerHTML = this.getEmptyState();
            }
        }
    }

    // Update loading state
    updateLoadingState() {
        const loadingState = this.element.querySelector('.loading-state');
        if (loadingState) {
            loadingState.classList.toggle('hidden', !this.loading);
        }
    }

    // Update channel stats
    updateStats() {
        const filteredVideos = this.getFilteredVideos();
        const filteredUnwatchedCount = filteredVideos.filter(v => !v.is_watched).length;
        const totalUnwatchedCount = this.getUnwatchedCount();

        // Update header stats - show filtered count if searching, otherwise total
        const statsElement = this.element.querySelector('.text-xs.text-gray-600');
        if (statsElement) {
            if (this.searchTerm) {
                statsElement.textContent = `${filteredUnwatchedCount} unwatched (${this.videos.length} total)`;
            } else {
                statsElement.textContent = `${totalUnwatchedCount} unwatched`;
            }
        }

        // Update clear button - always based on total unwatched (clearing watched affects all)
        const clearBtn = this.element.querySelector('.clear-btn');
        if (clearBtn) {
            const span = clearBtn.querySelector('span');
            if (span) {
                span.nextSibling.textContent = totalUnwatchedCount > 0 ? ` (${totalUnwatchedCount})` : '';
            }

            clearBtn.classList.toggle('opacity-50', totalUnwatchedCount === 0);
            clearBtn.classList.toggle('cursor-not-allowed', totalUnwatchedCount === 0);
            clearBtn.disabled = totalUnwatchedCount === 0;
        }
    }

    // Get count of unwatched videos
    getUnwatchedCount() {
        return this.videos.filter(v => !v.is_watched).length;
    }

    // Show error state
    showError(message) {
        const videosContainer = this.element.querySelector('.videos-list');
        if (videosContainer) {
            videosContainer.innerHTML = `
                <div class="text-center py-8 px-4">
                    <i class="fas fa-exclamation-triangle text-3xl text-red-400 mb-2"></i>
                    <p class="text-sm text-red-600">${message}</p>
                    <button class="mt-2 text-xs text-blue-600 hover:text-blue-800" onclick="this.closest('.channel-column').querySelector('.refresh-btn').click()">
                        Try again
                    </button>
                </div>
            `;
        }
    }

    // Clear all video cards
    clearVideoCards() {
        this.videoCards.forEach(card => card.destroy());
        this.videoCards.clear();
    }

    // Update channel data
    updateChannel(newChannelData) {
        this.channel = { ...this.channel, ...newChannelData };
        // Re-render header if needed
        this.updateStats();
    }

    // Destroy the component
    destroy() {
        this.clearVideoCards();
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

// Factory function to create channel columns
function createChannelColumn(channelData, onVideoWatch, onVideoOpen, onClearWatched) {
    return new ChannelColumn(channelData, onVideoWatch, onVideoOpen, onClearWatched);
}

// Export for use in other modules
window.ChannelColumn = ChannelColumn;
window.createChannelColumn = createChannelColumn;