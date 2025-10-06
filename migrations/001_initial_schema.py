"""
Миграция 001: Initial Schema

Создание базовой структуры БД
"""


def upgrade(cursor):
    """Применение миграции"""
    
    # Личные каналы пользователя
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            youtube_channel_id TEXT UNIQUE,
            oauth_token_path TEXT,
            color TEXT DEFAULT '#3b82f6',
            authuser_index INTEGER,
            order_position INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Подписки
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personal_channel_id INTEGER NOT NULL,
            youtube_channel_id TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            channel_thumbnail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (personal_channel_id) REFERENCES personal_channels(id),
            UNIQUE(personal_channel_id, youtube_channel_id)
        )
    ''')
    
    # Видео
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER NOT NULL,
            youtube_video_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            thumbnail TEXT,
            published_at TIMESTAMP NOT NULL,
            duration TEXT,
            view_count INTEGER,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_watched BOOLEAN DEFAULT 0,
            watched_at TIMESTAMP,
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
            UNIQUE(subscription_id, youtube_video_id)
        )
    ''')
    
    # Индексы
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_videos_watched 
        ON videos(is_watched, published_at DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_videos_subscription 
        ON videos(subscription_id, published_at DESC)
    ''')
    
    print("  ✓ Созданы таблицы: personal_channels, subscriptions, videos")
    print("  ✓ Созданы индексы для оптимизации запросов")