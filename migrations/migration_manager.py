"""
Система управления миграциями базы данных
"""

import sqlite3
import os
import importlib.util
from typing import List, Tuple
from datetime import datetime


class MigrationManager:
    """Менеджер миграций базы данных"""
    
    def __init__(self, db_path: str = "database/videos.db"):
        self.db_path = db_path
        self.migrations_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__))
        )
        self._ensure_schema_version_table()
    
    def _ensure_schema_version_table(self):
        """Создать таблицу для отслеживания версий"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_current_version(self) -> int:
        """Получить текущую версию схемы БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(version) FROM schema_version')
        result = cursor.fetchone()[0]
        
        conn.close()
        return result if result is not None else 0
    
    def get_available_migrations(self) -> List[Tuple[int, str]]:
        """
        Получить список доступных миграций
        
        Returns:
            List of (version, filename) tuples
        """
        migrations = []
        
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.py') and filename[0].isdigit():
                # Формат: 001_migration_name.py
                try:
                    version = int(filename.split('_')[0])
                    migrations.append((version, filename))
                except ValueError:
                    continue
        
        # Сортируем по версии
        migrations.sort(key=lambda x: x[0])
        return migrations
    
    def get_pending_migrations(self) -> List[Tuple[int, str]]:
        """Получить миграции, которые нужно применить"""
        current_version = self.get_current_version()
        all_migrations = self.get_available_migrations()
        
        # Фильтруем только те, что больше текущей версии
        pending = [(v, f) for v, f in all_migrations if v > current_version]
        return pending
    
    def load_migration(self, filename: str):
        """Загрузить модуль миграции"""
        file_path = os.path.join(self.migrations_dir, filename)
        
        spec = importlib.util.spec_from_file_location("migration", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def apply_migration(self, version: int, filename: str) -> bool:
        """
        Применить одну миграцию
        
        Returns:
            True если успешно, False если ошибка
        """
        try:
            print(f"\n{'─' * 60}")
            print(f"Применение миграции {version}: {filename}")
            print('─' * 60)
            
            # Загружаем модуль миграции
            module = self.load_migration(filename)
            
            # Получаем функцию upgrade
            if not hasattr(module, 'upgrade'):
                print(f"❌ Миграция {filename} не содержит функцию upgrade()")
                return False
            
            # Применяем миграцию
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Выполняем upgrade
                module.upgrade(cursor)
                
                # Записываем версию
                migration_name = filename.replace('.py', '').replace(f'{version:03d}_', '')
                cursor.execute('''
                    INSERT INTO schema_version (version, name)
                    VALUES (?, ?)
                ''', (version, migration_name))
                
                conn.commit()
                print(f"✓ Миграция {version} успешно применена")
                return True
                
            except Exception as e:
                conn.rollback()
                print(f"❌ Ошибка при применении миграции {version}: {e}")
                return False
            finally:
                conn.close()
        
        except Exception as e:
            print(f"❌ Ошибка загрузки миграции {filename}: {e}")
            return False
    
    def migrate(self, target_version: int = None) -> Tuple[int, int]:
        """
        Применить все необходимые миграции
        
        Args:
            target_version: Целевая версия (None = последняя)
            
        Returns:
            (успешных_миграций, общее_количество)
        """
        pending = self.get_pending_migrations()
        
        if target_version is not None:
            pending = [(v, f) for v, f in pending if v <= target_version]
        
        if not pending:
            return (0, 0)
        
        success_count = 0
        
        for version, filename in pending:
            if self.apply_migration(version, filename):
                success_count += 1
            else:
                # Останавливаемся при первой ошибке
                print("\n⚠️  Миграция прервана из-за ошибки")
                break
        
        return (success_count, len(pending))
    
    def get_migration_history(self) -> List[dict]:
        """Получить историю применённых миграций"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version, name, applied_at 
            FROM schema_version 
            ORDER BY version
        ''')
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history
    
    def print_status(self):
        """Вывести статус миграций"""
        current_version = self.get_current_version()
        pending = self.get_pending_migrations()
        all_migrations = self.get_available_migrations()
        
        print(f"\n{'=' * 60}")
        print("Статус миграций базы данных")
        print('=' * 60)
        print(f"\nТекущая версия схемы: {current_version}")
        print(f"Доступно миграций: {len(all_migrations)}")
        print(f"Ожидают применения: {len(pending)}")
        
        if pending:
            print("\nНеприменённые миграции:")
            for version, filename in pending:
                migration_name = filename.replace('.py', '').replace(f'{version:03d}_', '')
                print(f"  [{version}] {migration_name}")
        
        # История
        history = self.get_migration_history()
        if history:
            print("\nПрименённые миграции:")
            for record in history:
                applied = datetime.fromisoformat(record['applied_at'])
                print(f"  [{record['version']}] {record['name']} "
                      f"({applied.strftime('%Y-%m-%d %H:%M')})")
        
        print('=' * 60)


def create_migration_template(name: str, version: int = None):
    """
    Создать шаблон новой миграции
    
    Args:
        name: Название миграции (например, "add_user_settings")
        version: Номер версии (если None - автоматически следующий)
    """
    migrations_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Определяем версию
    if version is None:
        manager = MigrationManager()
        all_migrations = manager.get_available_migrations()
        version = max([v for v, _ in all_migrations], default=0) + 1
    
    # Формируем имя файла
    filename = f"{version:03d}_{name}.py"
    filepath = os.path.join(migrations_dir, filename)
    
    if os.path.exists(filepath):
        print(f"❌ Миграция {filename} уже существует")
        return
    
    # Шаблон миграции
    template = f'''"""
Миграция {version}: {name.replace('_', ' ').title()}

Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""


def upgrade(cursor):
    """
    Применение миграции
    
    Args:
        cursor: SQLite cursor
    """
    # Пример: добавление нового поля
    # cursor.execute(\'\'\'
    #     ALTER TABLE table_name 
    #     ADD COLUMN new_column TEXT DEFAULT 'default_value'
    # \'\'\')
    
    # Пример: создание новой таблицы
    # cursor.execute(\'\'\'
    #     CREATE TABLE IF NOT EXISTS new_table (
    #         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         name TEXT NOT NULL
    #     )
    # \'\'\')
    
    # Пример: создание индекса
    # cursor.execute(\'\'\'
    #     CREATE INDEX IF NOT EXISTS idx_table_column 
    #     ON table_name(column_name)
    # \'\'\')
    
    pass


def downgrade(cursor):
    """
    Откат миграции (опционально, для будущего)
    
    Args:
        cursor: SQLite cursor
    """
    # SQLite не поддерживает DROP COLUMN, поэтому откат сложен
    # Обычно не используется, но можно реализовать через пересоздание таблицы
    pass
'''
    
    # Сохраняем файл
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✓ Создана миграция: {filename}")
    print(f"  Путь: {filepath}")
    print("\nОтредактируйте файл и добавьте необходимые изменения в функцию upgrade()")