"""
Тесты для Database Manager
"""

import pytest
from datetime import datetime


@pytest.mark.unit
class TestPersonalChannels:
    """Тесты для работы с личными каналами"""
    
    def test_add_personal_channel(self, db, sample_channel_data):
        """Тест добавления личного канала"""
        channel_id = db.add_personal_channel(
            name=sample_channel_data['name'],
            youtube_channel_id=sample_channel_data['youtube_channel_id'],
            oauth_token_path=sample_channel_data['oauth_token_path'],
            color=sample_channel_data['color']
        )
        
        assert channel_id is not None
        assert channel_id > 0
    
    def test_get_all_personal_channels(self, db, sample_channel_data):
        """Тест получения всех каналов"""
        # Добавляем несколько каналов
        db.add_personal_channel(
            name='Channel 1',
            youtube_channel_id='UC_1',
            oauth_token_path='token1.pickle',
            color='#ff0000'
        )
        db.add_personal_channel(
            name='Channel 2',
            youtube_channel_id='UC_2',
            oauth_token_path='token2.pickle',
            color='#00ff00'
        )
        
        channels = db.get_all_personal_channels()
        
        assert len(channels) == 2
        assert channels[0]['name'] == 'Channel 1'
        assert channels[1]['name'] == 'Channel 2'
    
    def test_update_authuser_index(self, db, sample_channel_data):
        """Тест обновления authuser индекса"""
        channel_id = db.add_personal_channel(
            name=sample_channel_data['name'],
            youtube_channel_id=sample_channel_data['youtube_channel_id'],
            oauth_token_path=sample_channel_data['oauth_token_path']
        )
        
        db.update_authuser_index(channel_id, 2)
        
        channels = db.get_all_personal_channels()
        assert channels[0]['authuser_index'] == 2


@pytest.mark.unit
class TestSubscriptions:
    """Тесты для работы с подписками"""
    
    def test_add_subscription(self, db, sample_channel_data, sample_subscription_data):
        """Тест добавления подписки"""
        channel_id = db.add_personal_channel(
            name=sample_channel_data['name'],
            youtube_channel_id=sample_channel_data['youtube_channel_id'],
            oauth_token_path=sample_channel_data['oauth_token_path']
        )
        
        subscription_id = db.add_subscription(
            personal_channel_id=channel_id,
            youtube_channel_id=sample_subscription_data['youtube_channel_id'],
            channel_name=sample_subscription_data['channel_name'],
            channel_thumbnail=sample_subscription_data['channel_thumbnail']
        )
        
        assert subscription_id is not None
        assert subscription_id > 0
    
    def test_get_subscriptions_by_channel(self, populated_db):
        """Тест получения подписок для канала"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        subscriptions = db.get_subscriptions_by_channel(channel_id)
        
        assert len(subscriptions) == 1
        assert subscriptions[0]['channel_name'] == 'Test Subscription Channel'
        assert subscriptions[0]['is_active'] == 1
    
    def test_deactivate_subscription(self, populated_db):
        """Тест деактивации подписки"""
        db = populated_db['db']
        subscription_id = populated_db['subscription_id']
        
        db.deactivate_subscription(subscription_id)
        
        # Проверяем, что подписка деактивирована
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_active FROM subscriptions WHERE id = ?', (subscription_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result['is_active'] == 0
    
    def test_sync_subscriptions_status(self, populated_db):
        """Тест синхронизации статусов подписок"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        # Добавляем ещё одну подписку
        sub2_id = db.add_subscription(
            personal_channel_id=channel_id,
            youtube_channel_id='UC_sub2',
            channel_name='Sub 2',
            channel_thumbnail='thumb2.jpg'
        )
        
        # Синхронизируем: оставляем только первую подписку активной
        stats = db.sync_subscriptions_status(
            channel_id, 
            ['UC_subscription_456']  # Только первая подписка
        )
        
        assert stats['deactivated'] == 1  # Вторая подписка деактивирована
        assert stats['unchanged'] == 1    # Первая осталась активной


@pytest.mark.unit
class TestVideos:
    """Тесты для работы с видео"""
    
    def test_add_video(self, populated_db, sample_video_data):
        """Тест добавления видео"""
        db = populated_db['db']
        subscription_id = populated_db['subscription_id']
        
        video_id = db.add_video(
            subscription_id=subscription_id,
            youtube_video_id='new_video_123',
            title='New Video',
            thumbnail='thumb.jpg',
            published_at='2025-01-20T10:00:00Z',
            duration='5:30'
        )
        
        assert video_id is not None
        assert video_id > 0
    
    def test_get_videos_by_personal_channel(self, populated_db):
        """Тест получения видео для канала"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        videos = db.get_videos_by_personal_channel(channel_id)
        
        assert len(videos) == 1
        assert videos[0]['title'] == 'Test Video Title'
        assert videos[0]['is_watched'] == 0
    
    def test_mark_video_watched(self, populated_db):
        """Тест отметки видео как просмотренного"""
        db = populated_db['db']
        video_id = populated_db['video_id']
        
        db.mark_video_watched(video_id)
        
        # Проверяем
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_watched, watched_at FROM videos WHERE id = ?', (video_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result['is_watched'] == 1
        assert result['watched_at'] is not None
    
    def test_clear_watched_videos(self, populated_db):
        """Тест очистки просмотренных видео"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        video_id = populated_db['video_id']
        
        # Отмечаем как просмотренное
        db.mark_video_watched(video_id)
        
        # Очищаем
        db.clear_watched_videos(channel_id)
        
        # Проверяем, что видео удалено
        videos = db.get_videos_by_personal_channel(channel_id)
        assert len(videos) == 0
    
    def test_videos_filtered_by_active_subscriptions(self, populated_db):
        """Тест: видео с неактивных подписок не отображаются"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        subscription_id = populated_db['subscription_id']
        
        # Деактивируем подписку
        db.deactivate_subscription(subscription_id)
        
        # Видео не должно отображаться
        videos = db.get_videos_by_personal_channel(channel_id)
        assert len(videos) == 0


@pytest.mark.unit
class TestSyncErrors:
    """Тесты для логирования ошибок"""
    
    def test_log_sync_error(self, populated_db):
        """Тест логирования ошибки синхронизации"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        subscription_id = populated_db['subscription_id']
        
        db.log_sync_error(
            personal_channel_id=channel_id,
            subscription_id=subscription_id,
            channel_name='Test Channel',
            error_type='PLAYLIST_NOT_FOUND',
            error_message='Playlist not found'
        )
        
        errors = db.get_unresolved_errors(channel_id)
        
        assert len(errors) == 1
        assert errors[0]['error_type'] == 'PLAYLIST_NOT_FOUND'
        assert errors[0]['resolved'] == 0
    
    def test_mark_error_resolved(self, populated_db):
        """Тест отметки ошибки как решённой"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        db.log_sync_error(
            personal_channel_id=channel_id,
            subscription_id=None,
            channel_name='Test',
            error_type='TEST_ERROR',
            error_message='Test error'
        )
        
        errors = db.get_unresolved_errors(channel_id)
        error_id = errors[0]['id']
        
        db.mark_error_resolved(error_id)
        
        # Проверяем
        errors_after = db.get_unresolved_errors(channel_id)
        assert len(errors_after) == 0


@pytest.mark.integration
class TestDatabaseIntegration:
    """Интеграционные тесты БД"""
    
    def test_full_workflow(self, db):
        """Тест полного workflow: канал → подписка → видео → просмотр"""
        # 1. Создаём канал
        channel_id = db.add_personal_channel(
            name='Integration Test',
            youtube_channel_id='UC_integration',
            oauth_token_path='integration_token.pickle',
            color='#0000ff'
        )
        
        # 2. Добавляем подписку
        subscription_id = db.add_subscription(
            personal_channel_id=channel_id,
            youtube_channel_id='UC_sub_integration',
            channel_name='Integration Sub',
            channel_thumbnail='thumb.jpg'
        )
        
        # 3. Добавляем видео
        video_id = db.add_video(
            subscription_id=subscription_id,
            youtube_video_id='video_integration',
            title='Integration Video',
            thumbnail='video_thumb.jpg',
            published_at='2025-01-15T10:00:00Z',
            duration='15:00'
        )
        
        # 4. Проверяем, что всё добавилось
        videos = db.get_videos_by_personal_channel(channel_id)
        assert len(videos) == 1
        assert videos[0]['title'] == 'Integration Video'
        
        # 5. Отмечаем просмотренным
        db.mark_video_watched(video_id)
        
        # 6. Проверяем фильтрацию
        unwatched = db.get_videos_by_personal_channel(channel_id, include_watched=False)
        assert len(unwatched) == 0
        
        all_videos = db.get_videos_by_personal_channel(channel_id, include_watched=True)
        assert len(all_videos) == 1
        assert all_videos[0]['is_watched'] == 1