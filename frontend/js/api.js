// API Client for YouTube Dashboard
class APIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.axios = axios.create({
            baseURL: baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        this.setupInterceptors();
    }

    setupInterceptors() {
        // Response interceptor for error handling
        this.axios.interceptors.response.use(
            response => response,
            error => {
                const message = error.response?.data?.error || error.message;

                // Show user-friendly error
                if (error.response?.status === 401) {
                    showToast('Authentication required', 'error');
                } else if (error.response?.status === 403) {
                    showToast('Access denied', 'error');
                } else if (error.response?.status === 404) {
                    showToast('Resource not found', 'error');
                } else if (error.response?.status >= 500) {
                    showToast('Server error. Please try again later.', 'error');
                } else {
                    showToast(message, 'error');
                }

                return Promise.reject(error);
            }
        );
    }

    // === Channels ===

    async getChannels() {
        const response = await this.axios.get('/channels');
        return response.data.success ? response.data.data : [];
    }

    async addChannel(channelData) {
        const response = await this.axios.post('/channels', channelData);
        return response.data.success ? response.data.data : null;
    }

    async updateChannel(channelId, channelData) {
        const response = await this.axios.put(`/channels/${channelId}`, channelData);
        return response.data.success;
    }

    async deleteChannel(channelId) {
        const response = await this.axios.delete(`/channels/${channelId}`);
        return response.data.success;
    }

    // === Videos ===

    async getChannelVideos(channelId, includeWatched = false) {
        const params = new URLSearchParams({ include_watched: includeWatched });
        const response = await this.axios.get(`/channels/${channelId}/videos?${params}`);
        return response.data.success ? response.data.data : [];
    }

    async markVideoWatched(videoId) {
        const response = await this.axios.post(`/videos/${videoId}/watch`);
        return response.data.success;
    }

    async clearWatchedVideos(channelId) {
        const response = await this.axios.post(`/channels/${channelId}/clear`);
        return response.data.success;
    }

    async getVideo(videoId) {
        const response = await this.axios.get(`/videos/${videoId}`);
        return response.data.success ? response.data.data : null;
    }

    // === Subscriptions ===

    async getSubscriptions(channelId = null) {
        const url = channelId ? `/channels/${channelId}/subscriptions` : '/subscriptions';
        const response = await this.axios.get(url);
        return response.data.success ? response.data.data : [];
    }

    async updateSubscription(subscriptionId, subscriptionData) {
        const response = await this.axios.put(`/subscriptions/${subscriptionId}`, subscriptionData);
        return response.data.success;
    }

    async deleteSubscription(subscriptionId) {
        const response = await this.axios.delete(`/subscriptions/${subscriptionId}`);
        return response.data.success;
    }

    // === Sync Operations ===

    async syncSubscriptions(channelId = null) {
        const url = channelId ? `/sync/channels/${channelId}/subscriptions` : '/sync/subscriptions';
        const response = await this.axios.post(url);
        return response.data.success;
    }

    async syncVideos(channelId = null, maxVideos = 5) {
        const url = channelId ? `/sync/channels/${channelId}/videos` : '/sync/videos';
        const response = await this.axios.post(url, { max_videos: maxVideos });
        return response.data.success;
    }

    // === Stats & Errors ===

    async getStats() {
        const response = await this.axios.get('/stats');
        return response.data.success ? response.data.data : null;
    }

    async getErrors() {
        const response = await this.axios.get('/errors');
        return response.data.success ? response.data.data : [];
    }

    // === Settings ===

    async getSettings() {
        const response = await this.axios.get('/settings');
        return response.data.success ? response.data.data : {};
    }

    async updateSettings(settings) {
        const response = await this.axios.put('/settings', settings);
        return response.data.success;
    }

    // === i18n ===

    async getTranslations(locale) {
        try {
            console.log(`API: Fetching translations for ${locale}`);
            const response = await this.axios.get(`/i18n/${locale}`);
            const translations = response.data.success ? response.data.data : {};
            console.log(`API: Received ${Object.keys(translations).length} translation keys for ${locale}`);
            return translations;
        } catch (error) {
            console.warn(`Failed to load translations for ${locale}:`, error);
            return {};
        }
    }

    // === OAuth ===

    async startOAuth(channelName) {
        const response = await this.axios.post('/auth/start', { channel_name: channelName });
        return response.data.success ? response.data.data : null;
    }

    async completeOAuth(state, code) {
        const response = await this.axios.get('/auth/callback', {
            params: { state, code }
        });
        return response.data.success ? response.data.data : null;
    }
}

// Global API instance
const api = new APIClient();