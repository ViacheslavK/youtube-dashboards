"""
Миграция 002: Add Subscription Status

Добавление полей для отслеживания статуса подписок (активные/неактивные)
"""


def upgrade(cursor):
    """Применение миграции"""
    
    # Проверяем, есть ли уже эти поля (для идемпотентности)
    cursor.execute("PRAGMA table_info(subscriptions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Добавляем is_active
    if 'is_active' not in columns:
        cursor.execute('''
            ALTER TABLE subscriptions 
            ADD COLUMN is_active BOOLEAN DEFAULT 1
        ''')
        print("  ✓ Добавлено поле: is_active")
    
    # Добавляем deleted_by_user
    if 'deleted_by_user' not in columns:
        cursor.execute('''
            ALTER TABLE subscriptions 
            ADD COLUMN deleted_by_user BOOLEAN DEFAULT 0
        ''')
        print("  ✓ Добавлено поле: deleted_by_user")
    
    # Добавляем deactivated_at
    if 'deactivated_at' not in columns:
        cursor.execute('''
            ALTER TABLE subscriptions 
            ADD COLUMN deactivated_at TIMESTAMP
        ''')
        print("  ✓ Добавлено поле: deactivated_at")
    
    # Создаём индекс
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_subscriptions_active 
        ON subscriptions(personal_channel_id, is_active, deleted_by_user)
    ''')
    print("  ✓ Создан индекс: idx_subscriptions_active")