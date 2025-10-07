"""
YouTube Dashboard - Main Package

Основной функционал приложения
"""

from .db_manager import Database
from .youtube_api import YouTubeAPI

__all__ = ['Database', 'YouTubeAPI']