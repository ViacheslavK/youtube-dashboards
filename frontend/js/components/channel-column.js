// Channel Column Component for YouTube Dashboard
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
                    <div class="flex items-center space-x-3">
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

        // Add video cards
        this.videos.forEach(video => {
            const videoCard = createVideoCard(
                video,
                (videoId) => this.handleVideoWatch(videoId),
                (videoId) => this.handleVideoOpen(videoId)
            );

            videosContainer.appendChild(videoCard.element);
            this.videoCards.set(video.id, videoCard);
        });

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
                    video.is_watched = true;
                    videoCard.updateVideo(video);
                }

                // Remove from unwatched list after a delay
                setTimeout(() => {
                    this.removeVideo(videoId);
                }, 1000);

                // Update stats
                this.updateStats();

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
        // Update header stats
        const statsElement = this.element.querySelector('.text-xs.text-gray-600');
        if (statsElement) {
            const unwatchedCount = this.getUnwatchedCount();
            statsElement.textContent = `${unwatchedCount} unwatched`;
        }

        // Update clear button
        const clearBtn = this.element.querySelector('.clear-btn');
        if (clearBtn) {
            const unwatchedCount = this.getUnwatchedCount();
            const span = clearBtn.querySelector('span');
            if (span) {
                span.nextSibling.textContent = unwatchedCount > 0 ? ` (${unwatchedCount})` : '';
            }

            clearBtn.classList.toggle('opacity-50', unwatchedCount === 0);
            clearBtn.classList.toggle('cursor-not-allowed', unwatchedCount === 0);
            clearBtn.disabled = unwatchedCount === 0;
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