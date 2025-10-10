"""
Internationalization (i18n) system for SubDeck for YouTube
"""

import json
import os
from typing import Dict, Optional


class I18n:
    """Localization system"""
    
    def __init__(self, default_locale: str = 'ru'):
        self.default_locale = default_locale
        self.current_locale = default_locale
        self.locales_dir = os.path.join(os.path.dirname(__file__))
        self.translations: Dict[str, Dict] = {}
        
        # Load translations
        self._load_translations()
    
    def _load_translations(self):
        """Load all available translations"""
        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                locale = filename.replace('.json', '')
                file_path = os.path.join(self.locales_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[locale] = json.load(f)
                except Exception as e:
                    print(f"Warning: Failed to load locale '{locale}': {e}")
    
    def set_locale(self, locale: str):
        """Set current locale"""
        if locale in self.translations:
            self.current_locale = locale
        else:
            print(f"Warning: Locale '{locale}' not found, using '{self.default_locale}'")
            self.current_locale = self.default_locale
    
    def get_available_locales(self) -> list:
        """Get list of available locales"""
        return list(self.translations.keys())
    
    def t(self, key: str, **kwargs) -> str:
        """
        Translate key

        Args:
            key: Translation key (e.g., 'app.title' or 'errors.not_found')
            **kwargs: Parameters for substitution (e.g., count=5)

        Returns:
            Translated string

        Example:
            i18n.t('channels.count', count=5)  # "Channels: 5"
        """
        # Get translations for current locale
        translations = self.translations.get(self.current_locale, {})
        
        # Split key by dots for nested objects
        keys = key.split('.')
        value = translations
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        
        # If translation not found, try default locale
        if value is None and self.current_locale != self.default_locale:
            default_translations = self.translations.get(self.default_locale, {})
            value = default_translations
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break
        
        # If still not found, return key
        if value is None:
            return f"[{key}]"
        
        # Substitute parameters
        if kwargs:
            try:
                value = value.format(**kwargs)
            except KeyError as e:
                print(f"Warning: Missing parameter {e} for key '{key}'")
        
        return value
    
    def __call__(self, key: str, **kwargs) -> str:
        """Shortcut for t()"""
        return self.t(key, **kwargs)


# Global instance
_i18n_instance: Optional[I18n] = None


def get_i18n(locale: Optional[str] = None) -> I18n:
    """
    Get global i18n instance

    Args:
        locale: Locale to set (optional)

    Returns:
        I18n instance
    """
    global _i18n_instance
    
    if _i18n_instance is None:
        _i18n_instance = I18n()
    
    if locale:
        _i18n_instance.set_locale(locale)
    
    return _i18n_instance


def t(key: str, **kwargs) -> str:
    """
    Shortcut function for translation

    Example:
        from locales.i18n import t
        print(t('app.title'))
    """
    return get_i18n().t(key, **kwargs)


def set_locale(locale: str):
    """Set global locale"""
    get_i18n().set_locale(locale)


def get_available_locales() -> list:
    """Get list of available locales"""
    return get_i18n().get_available_locales()


def load_locale_from_config():
    """
    Load locale from config/settings.json

    Returns:
        str: Locale code (e.g., 'ru', 'en')
    """
    import json
    
    # Path to settings
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    settings_path = os.path.join(project_root, 'config', 'settings.json')
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            locale = settings.get('locale', 'ru')
            set_locale(locale)
            return locale
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or parsing error - use default
        return 'ru'