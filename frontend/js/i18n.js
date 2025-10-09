// Internationalization (i18n) System for YouTube Dashboard
class I18n {
    constructor() {
        this.locale = 'en';
        this.fallbackLocale = 'en';
        this.translations = {
            'en': {
                'app': { 'name': 'YouTube Dashboard' },
                'common': {
                    'loading': 'Loading...',
                    'sync': 'Sync',
                    'admin': 'Admin',
                    'error': 'Error'
                },
                'channels': {
                    'add_channel': 'Add Channel',
                    'no_channels': 'No configured channels',
                    'setup_prompt': 'Run: python src/setup_channels.py'
                },
                'videos': {
                    'clear_watched': 'Clear watched',
                    'mark_watched': 'Mark as watched',
                    'open': 'Open',
                    'no_videos': 'No videos',
                    'no_videos_desc': 'New videos will appear here'
                },
                'admin': {
                    'title': 'Admin Panel',
                    'back_to_dashboard': 'Back to Dashboard',
                    'channels': {
                        'title': 'Channels',
                        'add': 'Add Channel'
                    },
                    'subscriptions': {
                        'title': 'Subscriptions',
                        'no_subscriptions': 'No subscriptions found'
                    },
                    'errors': {
                        'title': 'Sync Errors',
                        'no_errors': 'No errors'
                    },
                    'settings': {
                        'title': 'Settings',
                        'auto_refresh': 'Auto-refresh',
                        'auto_refresh_desc': 'Automatically refresh data',
                        'refresh_interval': 'Refresh Interval',
                        'language': 'Language'
                    }
                }
            }
        };
        this.loadedLocales = new Set(['en']);
    }

    async setLocale(locale) {
        console.log(`i18n.setLocale called for ${locale}, current locale: ${this.locale}, loaded: ${this.loadedLocales.has(locale)}`);

        if (this.locale === locale && this.loadedLocales.has(locale)) {
            console.log(`Already loaded translations for ${locale}`);
            return; // Already loaded
        }

        // Load translations first if not already loaded
        if (!this.loadedLocales.has(locale)) {
            try {
                console.log(`Loading translations for ${locale}...`);
                const translations = await api.getTranslations(locale);
                console.log(`Received translations object:`, translations);
                if (translations && Object.keys(translations).length > 0) {
                    this.translations[locale] = translations;
                    this.loadedLocales.add(locale);
                    console.log(`Successfully loaded ${Object.keys(translations).length} translation keys for ${locale}`);
                } else {
                    console.warn(`Empty translations received for ${locale}`);
                }
            } catch (error) {
                console.warn(`Failed to load translations for ${locale}:`, error);
                // Fallback to English if available
                if (locale !== 'en' && this.loadedLocales.has('en')) {
                    this.locale = 'en';
                }
                return;
            }
        } else {
            console.log(`Translations for ${locale} already loaded`);
        }

        // Finally switch active locale after translations are present
        this.locale = locale;
    }

    t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations[this.locale];

        // Navigate through nested object
        for (const k of keys) {
            value = value?.[k];
        }

        // If not found in current locale, try fallback
        if (value === undefined && this.locale !== this.fallbackLocale) {
            value = this.translations[this.fallbackLocale];
            for (const k of keys) {
                value = value?.[k];
            }
        }

        // If still not found, return key as fallback
        if (value === undefined) {
            console.warn(`Translation missing for key: ${key}`);
            return `[${key}]`;
        }

        // Replace parameters
        return this.interpolate(value, params);
    }

    interpolate(text, params) {
        if (typeof text !== 'string') {
            return text;
        }

        return text.replace(/\{(\w+)\}/g, (match, key) => {
            return params[key] !== undefined ? params[key] : match;
        });
    }

    // Get available locales (this would come from backend)
    getAvailableLocales() {
        return ['en', 'ru']; // Hardcoded for now, could be fetched from API
    }

    // Format date using dayjs
    formatDate(dateString, format = 'MMM D, YYYY') {
        if (!dateString) return '';
        return dayjs(dateString).format(format);
    }

    // Format relative time
    formatRelative(dateString) {
        if (!dateString) return '';
        return dayjs(dateString).fromNow();
    }

    // Format number
    formatNumber(num, locale = this.locale) {
        return new Intl.NumberFormat(locale).format(num);
    }
}

// Global i18n instance
const i18n = new I18n();

// Alpine.js directive for translations
document.addEventListener('alpine:init', () => {
    Alpine.directive('t', (el, { expression }, { evaluate }) => {
        const key = evaluate(expression);
        // Initial render (may run before translations load)
        el.textContent = i18n.t(key);

        // Watch both locale and a version counter to re-render when translations finish loading
        Alpine.effect(() => {
            const currentLocale = Alpine.store('app').locale;
            const version = Alpine.store('app').i18nVersion; // increments after translations load
            void currentLocale; // ensure dependency
            void version;       // ensure dependency
            el.textContent = i18n.t(key);
        });
    });

    // Directive for HTML content with translations
    Alpine.directive('html-t', (el, { expression }, { evaluate }) => {
        const key = evaluate(expression);
        el.innerHTML = i18n.t(key);
    });
});

// Utility functions for templates
function t(key, params = {}) {
    return i18n.t(key, params);
}

function formatDate(dateString, format) {
    return i18n.formatDate(dateString, format);
}

function formatRelative(dateString) {
    return i18n.formatRelative(dateString);
}

function formatNumber(num) {
    return i18n.formatNumber(num);
}