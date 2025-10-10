"""
SubDeck for YouTube - Main Package

Main application functionality
"""

from .db_manager import Database
from .youtube_api import YouTubeAPI
from locales.i18n import load_locale_from_config

# Load locale when importing package
load_locale_from_config()

__all__ = ['Database', 'YouTubeAPI']
