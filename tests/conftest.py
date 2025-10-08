"""
Pytest fixtures and configuration
"""

import pytest
import os
import sys
import tempfile
import sqlite3
from pathlib import Path

# Добавляем корневую папку в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db_manager import Database


@pytest.fixture
def temp_db_path():
    """Создаёт временную БД для тестов"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # Удаляем после теста
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db(temp_db_path):
    """Создаёт тестовую БД с инициализированной схемой"""
    database = Database(temp_db_path)
    yield database
    # Cleanup происходит через temp_db_path fixture


@pytest.fixture
def sample_channel_data():
    """Тестовые данные для личного канала"""
    return {
        'name': 'Test Channel',
        'youtube_channel_id': 'UC_test_channel_123',
        'oauth_token_path': 'test/token.pickle',
        'color': '#ff0000',
        'order_position': 1
    }


@pytest.fixture
def sample_subscription_data():
    """Тестовые данные для подписки"""
    return {
        'youtube_channel_id': 'UC_subscription_456',
        'channel_name': 'Test Subscription Channel',
        'channel_thumbnail': 'https://example.com/thumb.jpg'
    }


@pytest.fixture
def sample_video_data():
    """Тестовые данные для видео"""
    return {
        'youtube_video_id': 'test_video_789',
        'title': 'Test Video Title',
        'thumbnail': 'https://example.com/video_thumb.jpg',
        'published_at': '2025-01-15T10:30:00Z',
        'duration': '10:30',
        'description': 'Test video description',
        'view_count': 1000
    }


@pytest.fixture
def populated_db(db, sample_channel_data, sample_subscription_data, sample_video_data):
    """БД с тестовыми данными"""
    # Добавляем канал
    channel_id = db.add_personal_channel(
        name=sample_channel_data['name'],
        youtube_channel_id=sample_channel_data['youtube_channel_id'],
        oauth_token_path=sample_channel_data['oauth_token_path'],
        color=sample_channel_data['color'],
        order_position=sample_channel_data['order_position']
    )
    
    # Добавляем подписку
    subscription_id = db.add_subscription(
        personal_channel_id=channel_id,
        youtube_channel_id=sample_subscription_data['youtube_channel_id'],
        channel_name=sample_subscription_data['channel_name'],
        channel_thumbnail=sample_subscription_data['channel_thumbnail']
    )
    
    # Добавляем видео
    video_id = db.add_video(
        subscription_id=subscription_id,
        youtube_video_id=sample_video_data['youtube_video_id'],
        title=sample_video_data['title'],
        thumbnail=sample_video_data['thumbnail'],
        published_at=sample_video_data['published_at'],
        duration=sample_video_data['duration'],
        description=sample_video_data['description'],
        view_count=sample_video_data['view_count']
    )
    
    return {
        'db': db,
        'channel_id': channel_id,
        'subscription_id': subscription_id,
        'video_id': video_id
    }