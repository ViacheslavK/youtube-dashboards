// Alpine.js Stores for YouTube Dashboard
document.addEventListener('alpine:init', () => {

    // === App Store - Global Application State ===
    Alpine.store('app', {
        loading: true, // Start with loading true
        locale: 'en',
        autoRefresh: true,
        refreshInterval: 5, // minutes
        lastRefresh: null,
        lastRefreshFormatted: '',
        refreshing: false, // For background refresh indicator
        i18nVersion: 0,

        setLoading(loading) {
            console.log('App store setLoading called with:', loading);
            this.loading = loading;
            console.log('App store loading is now:', this.loading);
        },

        init() {
            this.loadSettings();
            this.startAutoRefresh();
        },

        async loadSettings() {
            try {
                const settings = await api.getSettings();
                this.locale = settings.locale || 'en';
                this.autoRefresh = settings.auto_refresh !== false;
                this.refreshInterval = settings.refresh_interval || 5;
                // Load translations after settings
                await i18n.setLocale(this.locale);
                // Bump i18n version so x-t directives update even if locale didn't change
                this.i18nVersion++;
            } catch (error) {
                console.warn('Failed to load settings:', error);
            }
        },

        async setLocale(locale) {
            console.log('setLocale called with', locale);
            await i18n.setLocale(locale);
            console.log('i18n.setLocale done for', locale);
            this.locale = locale;
            // Bump i18n version so Alpine effects re-run
            this.i18nVersion++;
            console.log('store.locale set to', locale, 'i18nVersion', this.i18nVersion);
            this.saveSettings();
        },

        setAutoRefresh(enabled) {
            this.autoRefresh = enabled;
            if (enabled) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
            this.saveSettings();
        },

        setRefreshInterval(minutes) {
            this.refreshInterval = minutes;
            if (this.autoRefresh) {
                this.stopAutoRefresh();
                this.startAutoRefresh();
            }
            this.saveSettings();
        },

        startAutoRefresh() {
            if (this.autoRefreshInterval) return;

            this.autoRefreshInterval = setInterval(() => {
                this.refresh();
            }, this.refreshInterval * 60 * 1000);

            console.log(`Auto-refresh started: every ${this.refreshInterval} minutes`);
        },

        stopAutoRefresh() {
            if (this.autoRefreshInterval) {
                clearInterval(this.autoRefreshInterval);
                this.autoRefreshInterval = null;
                console.log('Auto-refresh stopped');
            }
        },

        async refresh() {
            console.log('Refreshing data...');
            this.refreshing = true;
            this.lastRefresh = new Date();
            this.lastRefreshFormatted = this.formatLastRefresh();

            try {
                // Reload channels and stats
                await Alpine.store('channels').load();
                await Alpine.store('stats').load();

                // Trigger refresh on all channel columns (components will handle their own video loading)
                // This will be handled by the main app component watching for channel changes

                showToast('Data refreshed successfully', 'success');
            } catch (error) {
                console.error('Refresh failed:', error);
                showToast('Failed to refresh data', 'error');
            } finally {
                this.refreshing = false;
            }
        },

        formatLastRefresh() {
            if (!this.lastRefresh) return '';
            return dayjs(this.lastRefresh).fromNow();
        },

        async saveSettings() {
            try {
                await api.updateSettings({
                    locale: this.locale,
                    auto_refresh: this.autoRefresh,
                    refresh_interval: this.refreshInterval
                });
            } catch (error) {
                console.warn('Failed to save settings:', error);
            }
        }
    });

    // === Channels Store ===
    Alpine.store('channels', {
        items: [],
        loading: false,

        async load() {
            this.loading = true;
            try {
                const channels = await api.getChannels();
                console.log('Channels API response:', channels);
                this.items = channels || [];
            } catch (error) {
                console.error('Failed to load channels:', error);
                this.items = [];
            } finally {
                this.loading = false;
            }
        },

        async add(channelData) {
            try {
                const newChannel = await api.addChannel(channelData);
                if (newChannel) {
                    this.items.push(newChannel);
                    showToast('Channel added successfully', 'success');
                    return newChannel;
                }
            } catch (error) {
                console.error('Failed to add channel:', error);
                throw error;
            }
        },

        async update(channelId, channelData) {
            try {
                const success = await api.updateChannel(channelId, channelData);
                if (success) {
                    const index = this.items.findIndex(c => c.id === channelId);
                    if (index !== -1) {
                        this.items[index] = { ...this.items[index], ...channelData };
                    }
                    showToast('Channel updated successfully', 'success');
                }
                return success;
            } catch (error) {
                console.error('Failed to update channel:', error);
                throw error;
            }
        },

        async delete(channelId) {
            try {
                const success = await api.deleteChannel(channelId);
                if (success) {
                    this.items = this.items.filter(c => c.id !== channelId);
                    showToast('Channel deleted successfully', 'success');
                }
                return success;
            } catch (error) {
                console.error('Failed to delete channel:', error);
                throw error;
            }
        },

        getById(channelId) {
            return this.items.find(c => c.id === channelId);
        }
    });

    // === Videos Store ===
    Alpine.store('videos', {
        byChannel: {}, // { channelId: [videos] }
        loading: {}, // { channelId: boolean }

        async loadForChannel(channelId) {
            this.loading[channelId] = true;
            try {
                const videos = await api.getChannelVideos(channelId, false); // Only unwatched
                this.byChannel[channelId] = videos;
            } catch (error) {
                console.error(`Failed to load videos for channel ${channelId}:`, error);
                this.byChannel[channelId] = [];
            } finally {
                this.loading[channelId] = false;
            }
        },

        async markWatched(videoId) {
            try {
                const success = await api.markVideoWatched(videoId);
                if (success) {
                    // Remove from all channel caches
                    for (const channelId in this.byChannel) {
                        this.byChannel[channelId] = this.byChannel[channelId].filter(v => v.id !== videoId);
                    }
                    showToast('Video marked as watched', 'success');
                }
                return success;
            } catch (error) {
                console.error('Failed to mark video as watched:', error);
                throw error;
            }
        },

        async clearWatched(channelId) {
            try {
                const success = await api.clearWatchedVideos(channelId);
                if (success) {
                    // Reload videos for this channel
                    await this.loadForChannel(channelId);
                    showToast('Watched videos cleared', 'success');
                }
                return success;
            } catch (error) {
                console.error('Failed to clear watched videos:', error);
                throw error;
            }
        },

        getForChannel(channelId) {
            return this.byChannel[channelId] || [];
        },

        isLoading(channelId) {
            return this.loading[channelId] || false;
        }
    });

    // === Subscriptions Store ===
    Alpine.store('subscriptions', {
        items: [],
        loading: false,
        filters: {
            channelId: null,
            status: 'active', // 'active', 'inactive', 'all'
            search: ''
        },

        get filtered() {
            return this.items.filter(sub => {
                if (!sub || typeof sub !== 'object') return false;

                // Channel filter
                if (this.filters.channelId && sub.personal_channel_id !== this.filters.channelId) {
                    return false;
                }

                // Status filter
                if (this.filters.status === 'active' && !sub.is_active) {
                    return false;
                }
                if (this.filters.status === 'inactive' && sub.is_active) {
                    return false;
                }

                // Search filter
                if (this.filters.search) {
                    const search = this.filters.search.toLowerCase();
                    const name = sub.channel_name ? sub.channel_name.toLowerCase() : '';
                    return name.includes(search);
                }

                return true;
            });
        },

        async load(channelId = null) {
            this.loading = true;
            try {
                const subs = await api.getSubscriptions(channelId);
                console.log('Subscriptions API response:', subs);
                this.items = subs || [];
            } catch (error) {
                console.error('Failed to load subscriptions:', error);
                this.items = [];
            } finally {
                this.loading = false;
            }
        },

        async update(subscriptionId, subscriptionData) {
            try {
                const success = await api.updateSubscription(subscriptionId, subscriptionData);
                if (success) {
                    const index = this.items.findIndex(s => s.id === subscriptionId);
                    if (index !== -1) {
                        this.items[index] = { ...this.items[index], ...subscriptionData };
                    }
                    showToast('Subscription updated successfully', 'success');
                }
                return success;
            } catch (error) {
                console.error('Failed to update subscription:', error);
                throw error;
            }
        },

        async delete(subscriptionId) {
            try {
                const success = await api.deleteSubscription(subscriptionId);
                if (success) {
                    this.items = this.items.filter(s => s.id !== subscriptionId);
                    showToast('Subscription deleted successfully', 'success');
                }
                return success;
            } catch (error) {
                console.error('Failed to delete subscription:', error);
                throw error;
            }
        },

        setFilter(key, value) {
            this.filters[key] = value;
        }
    });

    // === Stats Store ===
    Alpine.store('stats', {
        data: {
            total_channels: 0,
            total_subscriptions: 0,
            total_videos: 0,
            unwatched_videos: 0
        },
        loading: false,

        async load() {
            this.loading = true;
            try {
                const stats = await api.getStats();
                console.log('Stats API response:', stats);
                if (stats) {
                    this.data = stats;
                }
            } catch (error) {
                console.error('Failed to load stats:', error);
            } finally {
                this.loading = false;
            }
        }
    });

    // === Errors Store ===
    Alpine.store('errors', {
        items: [],
        loading: false,

        async load() {
            this.loading = true;
            try {
                this.items = await api.getErrors();
            } catch (error) {
                console.error('Failed to load errors:', error);
                this.items = [];
            } finally {
                this.loading = false;
            }
        },

        async markResolved(errorId) {
            try {
                // Note: This endpoint doesn't exist yet, will be added to backend
                const success = await api.markErrorResolved(errorId);
                if (success) {
                    const index = this.items.findIndex(e => e.id === errorId);
                    if (index !== -1) {
                        this.items.splice(index, 1);
                    }
                    showToast('Error marked as resolved', 'success');
                }
                return success;
            } catch (error) {
                console.error('Failed to mark error as resolved:', error);
                throw error;
            }
        }
    });

    // === OAuth Store ===
    Alpine.store('oauth', {
        inProgress: false,
        popup: null,

        async start(channelName) {
            this.inProgress = true;
            try {
                const authData = await api.startOAuth(channelName);
                if (authData) {
                    this.openPopup(authData.auth_url, authData.state);
                }
            } catch (error) {
                console.error('Failed to start OAuth:', error);
                this.inProgress = false;
                throw error;
            }
        },

        openPopup(url, state) {
            this.popup = window.open(
                url,
                'oauth',
                'width=600,height=700,scrollbars=yes,resizable=yes'
            );

            // Poll for completion
            this.pollOAuthCompletion(state);
        },

        pollOAuthCompletion(state) {
            const checkClosed = setInterval(() => {
                if (this.popup.closed) {
                    clearInterval(checkClosed);
                    this.inProgress = false;
                    showToast('OAuth cancelled', 'warning');
                }
            }, 1000);

            // Listen for message from popup
            window.addEventListener('message', async (event) => {
                if (event.data.type === 'oauth_complete' && event.data.state === state) {
                    clearInterval(checkClosed);
                    this.popup.close();
                    this.inProgress = false;

                    try {
                        // Complete OAuth on backend
                        const channel = await api.completeOAuth(state, event.data.code);
                        if (channel) {
                            // Add to channels store
                            Alpine.store('channels').items.push(channel);
                            showToast('Channel added successfully!', 'success');
                        }
                    } catch (error) {
                        console.error('Failed to complete OAuth:', error);
                        showToast('Failed to add channel', 'error');
                    }
                }
            }, { once: true });
        }
    });

});