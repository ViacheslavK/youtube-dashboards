"""
Internationalization (i18n) system для YouTube Dashboard
"""

import json
import os
from typing import Dict, Optional


class I18n:
    """Система локализации"""
    
    def __init__(self, default_locale: str = 'ru'):
        self.default_locale = default_locale
        self.current_locale = default_locale
        self.locales_dir = os.path.join(os.path.dirname(__file__))
        self.translations: Dict[str, Dict] = {}
        
        # Загружаем переводы
        self._load_translations()
    
    def _load_translations(self):
        """Загрузить все доступные переводы"""
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
        """Установить текущую локаль"""
        if locale in self.translations:
            self.current_locale = locale
        else:
            print(f"Warning: Locale '{locale}' not found, using '{self.default_locale}'")
            self.current_locale = self.default_locale
    
    def get_available_locales(self) -> list:
        """Получить список доступных локалей"""
        return list(self.translations.keys())
    
    def t(self, key: str, **kwargs) -> str:
        """
        Перевести ключ
        
        Args:
            key: Ключ перевода (например, 'app.title' или 'errors.not_found')
            **kwargs: Параметры для подстановки (например, count=5)
        
        Returns:
            Переведённая строка
        
        Example:
            i18n.t('channels.count', count=5)  # "Каналов: 5"
        """
        # Получаем переводы для текущей локали
        translations = self.translations.get(self.current_locale, {})
        
        # Разделяем ключ по точкам для вложенных объектов
        keys = key.split('.')
        value = translations
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        
        # Если перевод не найден, пробуем дефолтную локаль
        if value is None and self.current_locale != self.default_locale:
            default_translations = self.translations.get(self.default_locale, {})
            value = default_translations
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break
        
        # Если всё равно не найден, возвращаем ключ
        if value is None:
            return f"[{key}]"
        
        # Подставляем параметры
        if kwargs:
            try:
                value = value.format(**kwargs)
            except KeyError as e:
                print(f"Warning: Missing parameter {e} for key '{key}'")
        
        return value
    
    def __call__(self, key: str, **kwargs) -> str:
        """Shortcut для t()"""
        return self.t(key, **kwargs)


# Глобальный экземпляр
_i18n_instance: Optional[I18n] = None


def get_i18n(locale: Optional[str] = None) -> I18n:
    """
    Получить глобальный экземпляр i18n
    
    Args:
        locale: Локаль для установки (опционально)
    
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
    Shortcut функция для перевода
    
    Example:
        from locales.i18n import t
        print(t('app.title'))
    """
    return get_i18n().t(key, **kwargs)


def set_locale(locale: str):
    """Установить глобальную локаль"""
    get_i18n().set_locale(locale)


def get_available_locales() -> list:
    """Получить список доступных локалей"""
    return get_i18n().get_available_locales()


def load_locale_from_config():
    """
    Загрузить локаль из config/settings.json
    
    Returns:
        str: Код локали (например, 'ru', 'en')
    """
    import json
    
    # Путь к настройкам
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
        # Если файла нет или ошибка парсинга - используем дефолт
        return 'ru'