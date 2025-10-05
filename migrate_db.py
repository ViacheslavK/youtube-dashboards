#!/usr/bin/env python3
"""
Миграция базы данных: добавление полей is_active, deleted_by_user, deactivated_at
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))


def migrate():
    """Применить миграцию к существующей БД"""
    db_path = "database/videos.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    print("=" * 60)
    print("Миграция базы данных")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже эти поля
    cursor.execute("PRAGMA table_info(subscriptions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    migrations_needed = []
    
    if 'is_active' not in columns:
        migrations_needed.append('is_active')
    if 'deleted_by_user' not in columns:
        migrations_needed.append('deleted_by_user')
    if 'deactivated_at' not in columns:
        migrations_needed.append('deactivated_at')
    
    if not migrations_needed:
        print("✅ База данных уже обновлена, миграция не требуется")
        conn.close()
        return
    
    print(f"\nНеобходимо добавить поля: {', '.join(migrations_needed)}")
    print("\nПрименяем миграцию...")
    
    try:
        # Добавляем новые поля
        if 'is_active' in migrations_needed:
            cursor.execute('''
                ALTER TABLE subscriptions 
                ADD COLUMN is_active BOOLEAN DEFAULT 1
            ''')
            print("  ✓ Добавлено поле: is_active")
        
        if 'deleted_by_user' in migrations_needed:
            cursor.execute('''
                ALTER TABLE subscriptions 
                ADD COLUMN deleted_by_user BOOLEAN DEFAULT 0
            ''')
            print("  ✓ Добавлено поле: deleted_by_user")
        
        if 'deactivated_at' in migrations_needed:
            cursor.execute('''
                ALTER TABLE subscriptions 
                ADD COLUMN deactivated_at TIMESTAMP
            ''')
            print("  ✓ Добавлено поле: deactivated_at")
        
        # Создаём индекс если его нет
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_subscriptions_active 
            ON subscriptions(personal_channel_id, is_active, deleted_by_user)
        ''')
        print("  ✓ Создан индекс: idx_subscriptions_active")
        
        # Создаём таблицу sync_errors если её нет
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
        print("  ✓ Создана таблица: sync_errors")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sync_errors_unresolved 
            ON sync_errors(resolved, occurred_at DESC)
        ''')
        print("  ✓ Создан индекс: idx_sync_errors_unresolved")
        
        conn.commit()
        
        print("\n✅ Миграция успешно применена!")
        print("\nТеперь можно запустить:")
        print("  python src/sync_subscriptions.py  - для синхронизации статуса подписок")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Ошибка при миграции: {e}")
    finally:
        conn.close()
    
    print("=" * 60)


if __name__ == '__main__':
    try:
        migrate()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)