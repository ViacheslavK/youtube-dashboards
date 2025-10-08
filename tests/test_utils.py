"""
Тесты для утилит (utils/)
"""

import pytest
from io import StringIO
import sys


@pytest.mark.unit
class TestViewStats:
    """Тесты для utils/view_stats.py"""
    
    def test_view_channels_stats_empty(self, db, capsys):
        """Тест статистики при пустой БД"""
        # Импортируем функцию
        # (в реальных тестах лучше рефакторить utils для тестируемости)
        channels = db.get_all_personal_channels()
        assert len(channels) == 0
    
    def test_view_channels_stats_with_data(self, populated_db):
        """Тест статистики с данными"""
        db = populated_db['db']
        
        channels = db.get_all_personal_channels()
        assert len(channels) == 1
        
        videos = db.get_videos_by_personal_channel(channels[0]['id'])
        assert len(videos) == 1


@pytest.mark.unit
class TestManageSubscriptions:
    """Тесты для utils/manage_subscriptions.py"""
    
    def test_view_inactive_subscriptions_none(self, populated_db):
        """Тест: нет неактивных подписок"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        # Все подписки активны
        all_subs = db.get_subscriptions_by_channel(channel_id, include_inactive=True)
        inactive = [s for s in all_subs if not s['is_active']]
        
        assert len(inactive) == 0
    
    def test_view_inactive_subscriptions_with_inactive(self, populated_db):
        """Тест: есть неактивные подписки"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        subscription_id = populated_db['subscription_id']
        
        # Деактивируем подписку
        db.deactivate_subscription(subscription_id)
        
        # Проверяем
        all_subs = db.get_subscriptions_by_channel(channel_id, include_inactive=True)
        inactive = [s for s in all_subs if not s['is_active']]
        
        assert len(inactive) == 1
        assert inactive[0]['channel_name'] == 'Test Subscription Channel'
    
    def test_delete_inactive_subscription(self, populated_db):
        """Тест удаления неактивной подписки из истории"""
        db = populated_db['db']
        subscription_id = populated_db['subscription_id']
        
        # Деактивируем
        db.deactivate_subscription(subscription_id)
        
        # Удаляем из истории
        db.mark_subscription_deleted(subscription_id)
        
        # Проверяем
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT deleted_by_user FROM subscriptions WHERE id = ?', (subscription_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result['deleted_by_user'] == 1


@pytest.mark.unit
class TestViewErrors:
    """Тесты для utils/view_errors.py"""
    
    def test_view_errors_empty(self, db):
        """Тест: нет ошибок"""
        errors = db.get_unresolved_errors()
        assert len(errors) == 0
    
    def test_view_errors_with_data(self, populated_db):
        """Тест: есть ошибки"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        # Логируем ошибку
        db.log_sync_error(
            personal_channel_id=channel_id,
            subscription_id=None,
            channel_name='Test Channel',
            error_type='TEST_ERROR',
            error_message='Test error message'
        )
        
        errors = db.get_unresolved_errors()
        
        assert len(errors) == 1
        assert errors[0]['error_type'] == 'TEST_ERROR'
    
    def test_view_errors_by_channel(self, populated_db):
        """Тест получения ошибок для конкретного канала"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        # Добавляем второй канал
        channel2_id = db.add_personal_channel(
            name='Channel 2',
            youtube_channel_id='UC_2',
            oauth_token_path='token2.pickle'
        )
        
        # Логируем ошибки для разных каналов
        db.log_sync_error(channel_id, None, 'Ch1', 'ERROR1', 'Msg1')
        db.log_sync_error(channel2_id, None, 'Ch2', 'ERROR2', 'Msg2')
        
        # Получаем только для первого канала
        errors_ch1 = db.get_unresolved_errors(channel_id)
        
        assert len(errors_ch1) == 1
        assert errors_ch1[0]['error_type'] == 'ERROR1'


@pytest.mark.integration
class TestUtilsIntegration:
    """Интеграционные тесты утилит"""
    
    def test_full_subscription_management_workflow(self, db):
        """Тест полного workflow управления подписками"""
        # 1. Создаём канал
        channel_id = db.add_personal_channel(
            name='Test',
            youtube_channel_id='UC_test',
            oauth_token_path='token.pickle'
        )
        
        # 2. Добавляем подписки
        sub1_id = db.add_subscription(channel_id, 'UC_sub1', 'Sub 1', 'thumb1.jpg')
        sub2_id = db.add_subscription(channel_id, 'UC_sub2', 'Sub 2', 'thumb2.jpg')
        
        # 3. Синхронизация статусов (первая подписка пропала)
        stats = db.sync_subscriptions_status(channel_id, ['UC_sub2'])
        
        assert stats['deactivated'] == 1
        assert stats['unchanged'] == 1
        
        # 4. Просмотр неактивных
        all_subs = db.get_subscriptions_by_channel(channel_id, include_inactive=True)
        inactive = [s for s in all_subs if not s['is_active']]
        
        assert len(inactive) == 1
        assert inactive[0]['youtube_channel_id'] == 'UC_sub1'
        
        # 5. Удаление из истории
        db.mark_subscription_deleted(sub1_id)
        
        # 6. Проверка
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT deleted_by_user FROM subscriptions WHERE id = ?', (sub1_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result['deleted_by_user'] == 1