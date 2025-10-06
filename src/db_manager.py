import sqlite3
from datetime import datetime
from typing import List, Optional, Dict
import json


class Database:
    def __init__(self, db_path: str = "database/videos.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Создание таблиц базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
        
        # Подписки (каналы на которые подписаны личные каналы)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_channel_id INTEGER NOT NULL,
                youtube_channel_id TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                channel_thumbnail TEXT,
                is_active BOOLEAN DEFAULT 1,
                deleted_by_user BOOLEAN DEFAULT 0,
                deactivated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (personal_channel_id) REFERENCES personal_channels(id),
                UNIQUE(personal_channel_id, youtube_channel_id)
            )
        ''')
        
        # Индекс для быстрого поиска активных подписок
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_subscriptions_active 
            ON subscriptions(personal_channel_id, is_active, deleted_by_user)
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
        
        # Индексы для оптимизации
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_videos_watched 
            ON videos(is_watched, published_at DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_videos_subscription 
            ON videos(subscription_id, published_at DESC)
        ''')
        
        # Таблица для логирования ошибок синхронизации
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personal_channel_id INTEGER,
                subscription_id INTEGER,
                channel_name TEXT,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0,
                FOREIGN KEY (personal_channel_id) REFERENCES personal_channels(id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sync_errors_unresolved 
            ON sync_errors(resolved, occurred_at DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    # === Personal Channels ===
    
    def add_personal_channel(self, name: str, youtube_channel_id: str, 
                            oauth_token_path: str, color: str = '#3b82f6',
                            order_position: int = None) -> int:
        """Добавление личного канала"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if order_position is None:
            cursor.execute('SELECT MAX(order_position) FROM personal_channels')
            max_pos = cursor.fetchone()[0]
            order_position = (max_pos or 0) + 1
        
        cursor.execute('''
            INSERT INTO personal_channels 
            (name, youtube_channel_id, oauth_token_path, color, order_position)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, youtube_channel_id, oauth_token_path, color, order_position))
        
        channel_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return channel_id
    
    def get_all_personal_channels(self) -> List[Dict]:
        """Получение всех личных каналов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM personal_channels 
            ORDER BY order_position
        ''')
        
        channels = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return channels
    
    def update_authuser_index(self, channel_id: int, authuser_index: int):
        """Обновление authuser индекса для канала"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE personal_channels 
            SET authuser_index = ? 
            WHERE id = ?
        ''', (authuser_index, channel_id))
        
        conn.commit()
        conn.close()
    
    # === Subscriptions ===
    
    def add_subscription(self, personal_channel_id: int, youtube_channel_id: str,
                        channel_name: str, channel_thumbnail: str = None) -> int:
        """Добавление подписки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO subscriptions 
                (personal_channel_id, youtube_channel_id, channel_name, channel_thumbnail)
                VALUES (?, ?, ?, ?)
            ''', (personal_channel_id, youtube_channel_id, channel_name, channel_thumbnail))
            
            subscription_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            # Подписка уже существует
            cursor.execute('''
                SELECT id FROM subscriptions 
                WHERE personal_channel_id = ? AND youtube_channel_id = ?
            ''', (personal_channel_id, youtube_channel_id))
            subscription_id = cursor.fetchone()[0]
        
        conn.close()
        return subscription_id
    
    def get_subscriptions_by_channel(self, personal_channel_id: int, 
                                     include_inactive: bool = False) -> List[Dict]:
        """Получение подписок для личного канала"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM subscriptions 
            WHERE personal_channel_id = ? AND deleted_by_user = 0
        '''
        
        if not include_inactive:
            query += ' AND is_active = 1'
        
        cursor.execute(query, (personal_channel_id,))
        
        subscriptions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return subscriptions
    
    def deactivate_subscription(self, subscription_id: int):
        """Деактивировать подписку и удалить её видео"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Деактивируем подписку
        cursor.execute('''
            UPDATE subscriptions 
            SET is_active = 0, deactivated_at = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), subscription_id))
        
        # Удаляем все видео этой подписки
        cursor.execute('''
            DELETE FROM videos 
            WHERE subscription_id = ?
        ''', (subscription_id,))
        
        conn.commit()
        conn.close()
    
    def reactivate_subscription(self, subscription_id: int):
        """Реактивировать подписку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE subscriptions 
            SET is_active = 1, deactivated_at = NULL 
            WHERE id = ?
        ''', (subscription_id,))
        
        conn.commit()
        conn.close()
    
    def mark_subscription_deleted(self, subscription_id: int):
        """Пометить подписку как удалённую пользователем (для истории)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE subscriptions 
            SET deleted_by_user = 1 
            WHERE id = ?
        ''', (subscription_id,))
        
        conn.commit()
        conn.close()
    
    def sync_subscriptions_status(self, personal_channel_id: int, 
                                  current_youtube_ids: List[str]) -> Dict:
        """
        Синхронизация статуса подписок с YouTube
        
        Args:
            personal_channel_id: ID личного канала
            current_youtube_ids: Список актуальных YouTube channel IDs из API
            
        Returns:
            Статистика: {'activated': int, 'deactivated': int, 'unchanged': int}
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {'activated': 0, 'deactivated': 0, 'unchanged': 0}
        
        # Получаем текущие подписки из БД
        cursor.execute('''
            SELECT id, youtube_channel_id, is_active 
            FROM subscriptions 
            WHERE personal_channel_id = ? AND deleted_by_user = 0
        ''', (personal_channel_id,))
        
        db_subscriptions = {row['youtube_channel_id']: row for row in cursor.fetchall()}
        
        # Проверяем каждую подписку из БД
        for yt_id, sub in db_subscriptions.items():
            if yt_id in current_youtube_ids:
                # Подписка активна на YouTube
                if not sub['is_active']:
                    # Реактивируем
                    self.reactivate_subscription(sub['id'])
                    stats['activated'] += 1
                else:
                    stats['unchanged'] += 1
            else:
                # Подписка пропала из YouTube
                if sub['is_active']:
                    # Деактивируем
                    self.deactivate_subscription(sub['id'])
                    stats['deactivated'] += 1
        
        conn.close()
        return stats
    
    # === Videos ===
    
    def add_video(self, subscription_id: int, youtube_video_id: str,
                  title: str, thumbnail: str, published_at: str,
                  duration: str = None, description: str = None,
                  view_count: int = None) -> Optional[int]:
        """Добавление нового видео"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO videos 
                (subscription_id, youtube_video_id, title, description, thumbnail, 
                 published_at, duration, view_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (subscription_id, youtube_video_id, title, description, 
                  thumbnail, published_at, duration, view_count))
            
            video_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return video_id
        except sqlite3.IntegrityError:
            # Видео уже существует
            conn.close()
            return None
    
    def get_videos_by_personal_channel(self, personal_channel_id: int, 
                                       include_watched: bool = True) -> List[Dict]:
        """Получение всех видео для личного канала (только с активных подписок)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT v.*, s.channel_name, s.channel_thumbnail,
                   s.youtube_channel_id as subscription_youtube_id
            FROM videos v
            JOIN subscriptions s ON v.subscription_id = s.id
            WHERE s.personal_channel_id = ? 
              AND s.is_active = 1 
              AND s.deleted_by_user = 0
        '''
        
        if not include_watched:
            query += ' AND v.is_watched = 0'
        
        query += ' ORDER BY v.published_at DESC'
        
        cursor.execute(query, (personal_channel_id,))
        
        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return videos
    
    def mark_video_watched(self, video_id: int):
        """Отметить видео как просмотренное"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE videos 
            SET is_watched = 1, watched_at = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), video_id))
        
        conn.commit()
        conn.close()
    
    def clear_watched_videos(self, personal_channel_id: int):
        """Очистить просмотренные видео для личного канала"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM videos 
            WHERE id IN (
                SELECT v.id FROM videos v
                JOIN subscriptions s ON v.subscription_id = s.id
                WHERE s.personal_channel_id = ? AND v.is_watched = 1
            )
        ''', (personal_channel_id,))
        
        conn.commit()
        conn.close()
    
    def get_video_by_id(self, video_id: int) -> Optional[Dict]:
        """Получение видео по ID с информацией о личном канале"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v.*, s.personal_channel_id, pc.authuser_index
            FROM videos v
            JOIN subscriptions s ON v.subscription_id = s.id
            JOIN personal_channels pc ON s.personal_channel_id = pc.id
            WHERE v.id = ?
        ''', (video_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    # === Sync Errors ===
    
    def log_sync_error(self, personal_channel_id: int, subscription_id: Optional[int],
                       channel_name: str, error_type: str, error_message: str):
        """Логирование ошибки синхронизации"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sync_errors 
            (personal_channel_id, subscription_id, channel_name, error_type, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (personal_channel_id, subscription_id, channel_name, error_type, error_message))
        
        conn.commit()
        conn.close()
    
    def get_unresolved_errors(self, personal_channel_id: Optional[int] = None) -> List[Dict]:
        """Получение нерешённых ошибок"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if personal_channel_id:
            cursor.execute('''
                SELECT * FROM sync_errors 
                WHERE personal_channel_id = ? AND resolved = 0
                ORDER BY occurred_at DESC
            ''', (personal_channel_id,))
        else:
            cursor.execute('''
                SELECT * FROM sync_errors 
                WHERE resolved = 0
                ORDER BY occurred_at DESC
            ''')
        
        errors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return errors
    
    def mark_error_resolved(self, error_id: int):
        """Отметить ошибку как решённую"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sync_errors 
            SET resolved = 1 
            WHERE id = ?
        ''', (error_id,))
        
        conn.commit()
        conn.close()
    
    def clear_old_errors(self, days: int = 30):
        """Удалить старые решённые ошибки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM sync_errors 
            WHERE resolved = 1 
            AND occurred_at < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        conn.commit()
        conn.close()