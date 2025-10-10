"""
Tests for localization system
"""

import pytest
from locales import get_i18n, t, set_locale, get_available_locales


@pytest.fixture
def i18n():
    """Creates new i18n instance for tests"""
    from locales.i18n import I18n
    return I18n(default_locale='ru')


@pytest.mark.unit
class TestI18nBasics:
    """Basic i18n tests"""
    
    def test_load_translations(self, i18n):
        """Test loading translations"""
        locales = i18n.get_available_locales()
        
        assert 'ru' in locales
        assert 'en' in locales
        assert len(locales) >= 2
    
    def test_default_locale(self, i18n):
        """Test default locale"""
        assert i18n.current_locale == 'ru'
        assert i18n.default_locale == 'ru'
    
    def test_set_locale(self, i18n):
        """Test locale change"""
        i18n.set_locale('en')
        assert i18n.current_locale == 'en'
    
    def test_set_invalid_locale(self, i18n):
        """Test setting non-existent locale"""
        i18n.set_locale('fr')  # Does not exist
        assert i18n.current_locale == 'ru'  # Remains default


@pytest.mark.unit
class TestTranslations:
    """Translation tests"""
    
    def test_simple_translation(self, i18n):
        """Test simple translation"""
        text = i18n.t('app.name')
        assert text == 'SubDeck for YouTube'
    
    def test_nested_translation(self, i18n):
        """Test nested translation"""
        text = i18n.t('common.yes')
        assert text == 'Да'
    
    def test_translation_with_params(self, i18n):
        """Test translation with parameters"""
        text = i18n.t('channels.count', count=5)
        assert text == 'Каналов: 5'
    
    def test_missing_translation(self, i18n):
        """Test missing translation"""
        text = i18n.t('non.existent.key')
        assert text == '[non.existent.key]'
    
    def test_translation_different_locale(self, i18n):
        """Test translation to another language"""
        i18n.set_locale('en')
        text = i18n.t('common.yes')
        assert text == 'Yes'
    
    def test_fallback_to_default(self, i18n):
        """Test fallback to default locale"""
        i18n.set_locale('en')
        
        # If English doesn't have translation, takes from Russian
        # (this depends on translation completeness)
        text = i18n.t('app.name')
        assert text != ''


@pytest.mark.unit
class TestGlobalFunctions:
    """Global functions tests"""
    
    def test_global_t_function(self):
        """Test global t() function"""
        set_locale('ru')
        text = t('common.ok')
        assert text == 'ОК'
    
    def test_get_available_locales_function(self):
        """Test getting list of locales"""
        locales = get_available_locales()
        assert isinstance(locales, list)
        assert len(locales) >= 2
    
    def test_set_locale_function(self):
        """Test global set_locale() function"""
        set_locale('en')
        text = t('common.ok')
        assert text == 'OK'
        
        # Return back
        set_locale('ru')


@pytest.mark.unit
class TestEdgeCases:
    """Edge cases tests"""
    
    def test_empty_parameters(self, i18n):
        """Test with empty parameters"""
        text = i18n.t('channels.count', count=0)
        assert text == 'Каналов: 0'
    
    def test_multiple_parameters(self, i18n):
        """Test with multiple parameters"""
        # Example key that uses multiple parameters
        # (need to add to ru.json for test)
        i18n.translations['ru']['test'] = {
            'multi_param': '{name} имеет {count} видео'
        }
        
        text = i18n.t('test.multi_param', name='Канал', count=10)
        assert text == 'Канал имеет 10 видео'
    
    def test_callable_shortcut(self, i18n):
        """Test using i18n as function"""
        text = i18n('common.yes')
        assert text == 'Да'


@pytest.mark.integration
class TestRealUsage:
    """Real usage integration tests"""
    
    def test_sync_messages(self, i18n):
        """Test sync messages"""
        text = i18n.t('sync.channels_found', count=7)
        assert 'Найдено 7' in text
        
        text = i18n.t('sync.sync_complete')
        assert text == 'Синхронизация завершена!'
    
    def test_error_messages(self, i18n):
        """Test error messages"""
        text = i18n.t('errors.types.PLAYLIST_NOT_FOUND')
        assert 'Плейлист не найден' in text
        
        text = i18n.t('errors.unresolved', count=3)
        assert 'Нерешённых ошибок: 3' in text
    
    def test_menu_messages(self, i18n):
        """Test menu"""
        text = i18n.t('menu.your_choice', min=1, max=5)
        assert 'Ваш выбор (1-5):' in text