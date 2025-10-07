"""
Миграция 003: Add Sync Errors

Добавление таблицы для логирования ошибок синхронизации
"""


def upgrade(cursor):
    """Применение миграции"""
    
    # Создаём таблицу для ошибок синхронизации
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
    print("  [OK] Created table: sync_errors")
    
    # Создаём индекс
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sync_errors_unresolved 
        ON sync_errors(resolved, occurred_at DESC)
    ''')
    print("  [OK] Created index: idx_sync_errors_unresolved")