// Video Card Component for YouTube Dashboard
class VideoCard {
    constructor(videoData, onWatch, onOpen) {
        this.video = videoData;
        this.onWatch = onWatch;
        this.onOpen = onOpen;
        this.element = null;
        this.render();
    }

    render() {
        // Create the video card element
        this.element = document.createElement('div');
        this.element.className = `bg-white rounded-lg shadow-sm border overflow-hidden hover:shadow-md transition-all duration-200 video-card ${this.video.is_watched ? 'opacity-60' : ''}`;
        this.element.innerHTML = this.getTemplate();

        // Add event listeners
        this.attachEventListeners();

        return this.element;
    }

    getTemplate() {
        const thumbnailUrl = getVideoThumbnail(this.video.youtube_video_id);
        const formattedDate = formatRelative(this.video.published_at);
        const duration = formatDuration(this.video.duration);

        return `
            <div class="p-4">
                <!-- Thumbnail -->
                <div class="relative mb-3">
                    <img src="${thumbnailUrl}"
                         alt="${this.video.title}"
                         class="w-full h-32 object-cover rounded-md video-thumbnail"
                         loading="lazy"
                         onerror="this.src='/assets/icons/video-placeholder.png'">
                    <div class="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                        ${duration}
                    </div>
                    ${this.video.is_watched ? '<div class="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded">✓ Watched</div>' : ''}
                </div>

                <!-- Content -->
                <div class="space-y-2">
                    <!-- Title -->
                    <h4 class="font-medium text-gray-900 text-sm line-clamp-2 leading-tight"
                        title="${this.video.title}">
                        ${this.video.title}
                    </h4>

                    <!-- Channel and metadata -->
                    <div class="text-xs text-gray-600 space-y-1">
                        <div class="font-medium text-gray-800">${this.video.channel_name}</div>
                        <div class="flex items-center justify-between">
                            <span>${formattedDate}</span>
                            ${this.video.view_count ? `<span>${formatViewCount(this.video.view_count)} views</span>` : ''}
                        </div>
                    </div>
                </div>

                <!-- Actions -->
                <div class="flex gap-2 mt-3">
                    <button class="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-2 px-3 rounded-md transition-colors duration-200 flex items-center justify-center gap-1 open-btn"
                            title="Open video">
                        <i class="fas fa-external-link-alt text-xs"></i>
                        <span x-t="'videos.open'">Open</span>
                    </button>
                    ${!this.video.is_watched ? `
                        <button class="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-3 rounded-md transition-colors duration-200 flex items-center justify-center gap-1 watch-btn"
                                title="Mark as watched">
                            <i class="fas fa-check text-xs"></i>
                            <span x-t="'videos.mark_watched'">Watch</span>
                        </button>
                    ` : `
                        <button class="flex-1 bg-gray-300 text-gray-500 text-sm py-2 px-3 rounded-md cursor-not-allowed flex items-center justify-center gap-1"
                                disabled
                                title="Already watched">
                            <i class="fas fa-check text-xs"></i>
                            <span>Watched</span>
                        </button>
                    `}
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // Open video button
        const openBtn = this.element.querySelector('.open-btn');
        if (openBtn) {
            openBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleOpen();
            });
        }

        // Watch video button
        const watchBtn = this.element.querySelector('.watch-btn');
        if (watchBtn) {
            watchBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleWatch();
            });
        }

        // Keyboard shortcuts
        this.element.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                if (!this.video.is_watched) {
                    this.handleWatch();
                } else {
                    this.handleOpen();
                }
            }
        });

        // Make focusable for accessibility
        this.element.setAttribute('tabindex', '0');

        // Add focus styles
        this.element.addEventListener('focus', () => {
            this.element.classList.add('focused');
        });

        this.element.addEventListener('blur', () => {
            this.element.classList.remove('focused');
        });
    }

    async handleWatch() {
        if (this.video.is_watched) return;

        try {
            // Show loading state
            const watchBtn = this.element?.querySelector('.watch-btn');
            if (!watchBtn) {
                console.log('Watch button not found, video may have been removed');
                return;
            }

            const originalText = watchBtn.innerHTML;
            watchBtn.innerHTML = '<i class="fas fa-spinner fa-spin text-xs"></i> <span>Marking...</span>';
            watchBtn.disabled = true;

            // Call the watch function
            const success = await this.onWatch(this.video.id);

            if (success) {
                // Check if element is still in DOM before updating
                if (!this.element || !this.element.parentNode) {
                    console.log('Video element removed from DOM during watch operation');
                    return;
                }

                // Update UI immediately for better user feedback
                this.video.is_watched = true;
                this.element.classList.add('opacity-60');

                // Add watched badge
                const thumbnail = this.element.querySelector('.video-thumbnail')?.parentElement;
                if (thumbnail) {
                    const watchedBadge = document.createElement('div');
                    watchedBadge.className = 'absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded';
                    watchedBadge.textContent = '✓ Watched';
                    thumbnail.appendChild(watchedBadge);
                }

                // Update buttons
                const actionsDiv = this.element.querySelector('.flex.gap-2');
                if (actionsDiv) {
                    actionsDiv.innerHTML = `
                        <button class="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-2 px-3 rounded-md transition-colors duration-200 flex items-center justify-center gap-1 open-btn">
                            <i class="fas fa-external-link-alt text-xs"></i>
                            <span>Open</span>
                        </button>
                        <button class="flex-1 bg-gray-300 text-gray-500 text-sm py-2 px-3 rounded-md cursor-not-allowed flex items-center justify-center gap-1" disabled>
                            <i class="fas fa-check text-xs"></i>
                            <span>Watched</span>
                        </button>
                    `;

                    // Re-attach event listeners
                    this.attachEventListeners();
                }

                showToast('Video marked as watched', 'success');
            } else {
                throw new Error('Failed to mark video as watched');
            }

        } catch (error) {
            console.error('Error marking video as watched:', error);
            showToast('Failed to mark video as watched', 'error');

            // Reset button state only if element still exists
            if (this.element) {
                const watchBtn = this.element.querySelector('.watch-btn');
                if (watchBtn) {
                    watchBtn.innerHTML = originalText;
                    watchBtn.disabled = false;
                }
            }
        }
    }

    async handleOpen() {
        try {
            // Get video details to ensure we have the authuser index
            const video = await api.getVideo(this.video.id);

            if (video) {
                const authuser = video.authuser_index || 0;
                const url = `https://www.youtube.com/watch?v=${video.youtube_video_id}&authuser=${authuser}`;

                // Open in new tab
                window.open(url, '_blank');

                showToast('Video opened in new tab', 'info');
            } else {
                throw new Error('Failed to get video details');
            }

        } catch (error) {
            console.error('Error opening video:', error);
            showToast('Failed to open video', 'error');

            // Fallback: try to open with basic URL
            const fallbackUrl = `https://www.youtube.com/watch?v=${this.video.youtube_video_id}`;
            window.open(fallbackUrl, '_blank');
        }
    }

    // Update the video data
    updateVideo(newVideoData) {
        // Check if element is still in DOM before updating
        if (!this.element || !this.element.parentNode) {
            console.warn('Video element no longer in DOM, skipping update');
            return;
        }

        // Safely update video data
        if (newVideoData && typeof newVideoData === 'object') {
            this.video = { ...this.video, ...newVideoData };
        }

        try {
            // Re-render if needed
            const newElement = this.render();
            if (this.element.parentNode) {
                this.element.parentNode.replaceChild(newElement, this.element);
                this.element = newElement;
            }
        } catch (error) {
            console.error('Error updating video element:', error);
            // Don't throw - gracefully handle the error
        }
    }

    // Destroy the component
    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

// Factory function to create video cards
function createVideoCard(videoData, onWatch, onOpen) {
    return new VideoCard(videoData, onWatch, onOpen);
}

// Export for use in other modules
window.VideoCard = VideoCard;
window.createVideoCard = createVideoCard;