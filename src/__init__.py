"""
YouTube Dashboard - Main Package

Основной функционал приложения
"""

from .db_manager import Database
from .youtube_api import YouTubeAPI
from locales.i18n import load_locale_from_config

# Загружаем локаль при импорте пакета
load_locale_from_config()

__all__ = ['Database', 'YouTubeAPI']
