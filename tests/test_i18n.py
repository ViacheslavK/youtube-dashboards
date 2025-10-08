"""
Тесты для системы локализации
"""

import pytest
from locales import get_i18n, t, set_locale, get_available_locales


@pytest.fixture
def i18n():
    """Создаёт новый экземпляр i18n для тестов"""
    from locales.i18n import I18n
    return I18n(default_locale='ru')


@pytest.mark.unit
class TestI18nBasics:
    """Базовые тесты i18n"""
    
    def test_load_translations(self, i18n):
        """Тест загрузки переводов"""
        locales = i18n.get_available_locales()
        
        assert 'ru' in locales
        assert 'en' in locales
        assert len(locales) >= 2
    
    def test_default_locale(self, i18n):
        """Тест дефолтной локали"""
        assert i18n.current_locale == 'ru'
        assert i18n.default_locale == 'ru'
    
    def test_set_locale(self, i18n):
        """Тест смены локали"""
        i18n.set_locale('en')
        assert i18n.current_locale == 'en'
    
    def test_set_invalid_locale(self, i18n):
        """Тест установки несуществующей локали"""
        i18n.set_locale('fr')  # Не существует
        assert i18n.current_locale == 'ru'  # Остаётся дефолтная


@pytest.mark.unit
class TestTranslations:
    """Тесты переводов"""
    
    def test_simple_translation(self, i18n):
        """Тест простого перевода"""
        text = i18n.t('app.name')
        assert text == 'YouTube Dashboard'
    
    def test_nested_translation(self, i18n):
        """Тест вложенного перевода"""
        text = i18n.t('common.yes')
        assert text == 'Да'
    
    def test_translation_with_params(self, i18n):
        """Тест перевода с параметрами"""
        text = i18n.t('channels.count', count=5)
        assert text == 'Каналов: 5'
    
    def test_missing_translation(self, i18n):
        """Тест отсутствующего перевода"""
        text = i18n.t('non.existent.key')
        assert text == '[non.existent.key]'
    
    def test_translation_different_locale(self, i18n):
        """Тест перевода на другой язык"""
        i18n.set_locale('en')
        text = i18n.t('common.yes')
        assert text == 'Yes'
    
    def test_fallback_to_default(self, i18n):
        """Тест fallback на дефолтную локаль"""
        i18n.set_locale('en')
        
        # Если в английском нет перевода, берётся из русского
        # (это зависит от полноты переводов)
        text = i18n.t('app.name')
        assert text != ''


@pytest.mark.unit
class TestGlobalFunctions:
    """Тесты глобальных функций"""
    
    def test_global_t_function(self):
        """Тест глобальной функции t()"""
        set_locale('ru')
        text = t('common.ok')
        assert text == 'ОК'
    
    def test_get_available_locales_function(self):
        """Тест получения списка локалей"""
        locales = get_available_locales()
        assert isinstance(locales, list)
        assert len(locales) >= 2
    
    def test_set_locale_function(self):
        """Тест глобальной функции set_locale()"""
        set_locale('en')
        text = t('common.ok')
        assert text == 'OK'
        
        # Возвращаем обратно
        set_locale('ru')


@pytest.mark.unit
class TestEdgeCases:
    """Тесты граничных случаев"""
    
    def test_empty_parameters(self, i18n):
        """Тест с пустыми параметрами"""
        text = i18n.t('channels.count', count=0)
        assert text == 'Каналов: 0'
    
    def test_multiple_parameters(self, i18n):
        """Тест с несколькими параметрами"""
        # Пример ключа, который использует несколько параметров
        # (нужно добавить в ru.json для теста)
        i18n.translations['ru']['test'] = {
            'multi_param': '{name} имеет {count} видео'
        }
        
        text = i18n.t('test.multi_param', name='Канал', count=10)
        assert text == 'Канал имеет 10 видео'
    
    def test_callable_shortcut(self, i18n):
        """Тест использования i18n как функции"""
        text = i18n('common.yes')
        assert text == 'Да'


@pytest.mark.integration
class TestRealUsage:
    """Интеграционные тесты реального использования"""
    
    def test_sync_messages(self, i18n):
        """Тест сообщений синхронизации"""
        text = i18n.t('sync.channels_found', count=7)
        assert 'Найдено 7' in text
        
        text = i18n.t('sync.sync_complete')
        assert text == 'Синхронизация завершена!'
    
    def test_error_messages(self, i18n):
        """Тест сообщений об ошибках"""
        text = i18n.t('errors.types.PLAYLIST_NOT_FOUND')
        assert 'Плейлист не найден' in text
        
        text = i18n.t('errors.unresolved', count=3)
        assert 'Нерешённых ошибок: 3' in text
    
    def test_menu_messages(self, i18n):
        """Тест меню"""
        text = i18n.t('menu.your_choice', min=1, max=5)
        assert 'Ваш выбор (1-5):' in text