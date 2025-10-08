"""
Тесты для системы миграций
"""

import pytest
import os
import sqlite3
from pathlib import Path
import tempfile

from migrations.migration_manager import MigrationManager


@pytest.fixture
def temp_migrations_dir(tmp_path):
    """Создаёт временную папку с миграциями для тестов"""
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    
    # Создаём тестовую миграцию
    migration_file = migrations_dir / "001_test_migration.py"
    migration_file.write_text("""
def upgrade(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')
    print("  [OK] Test migration applied")
""", encoding='utf-8')
    
    return str(migrations_dir)


@pytest.fixture
def migration_manager(temp_db_path, temp_migrations_dir, monkeypatch):
    """Создаёт MigrationManager с временными путями"""
    manager = MigrationManager(temp_db_path)
    # Переопределяем папку миграций
    monkeypatch.setattr(manager, 'migrations_dir', temp_migrations_dir)
    return manager


@pytest.mark.unit
class TestMigrationManager:
    """Тесты для MigrationManager"""
    
    def test_schema_version_table_created(self, temp_db_path):
        """Тест создания таблицы schema_version"""
        manager = MigrationManager(temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Проверяем, что таблица создана
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_version'
        """)
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 'schema_version'
        
        conn.close()
    
    def test_get_current_version_initial(self, migration_manager):
        """Тест: начальная версия = 0"""
        version = migration_manager.get_current_version()
        assert version == 0
    
    def test_get_available_migrations(self, migration_manager):
        """Тест получения доступных миграций"""
        migrations = migration_manager.get_available_migrations()
        
        assert len(migrations) >= 1
        assert migrations[0][0] == 1  # Версия
        assert '001_test_migration.py' in migrations[0][1]  # Имя файла
    
    def test_get_pending_migrations(self, migration_manager):
        """Тест получения неприменённых миграций"""
        pending = migration_manager.get_pending_migrations()
        
        # Все миграции должны быть pending (версия = 0)
        assert len(pending) >= 1
    
    def test_apply_migration(self, migration_manager, temp_db_path):
        """Тест применения миграции"""
        migrations = migration_manager.get_available_migrations()
        version, filename = migrations[0]
        
        success = migration_manager.apply_migration(version, filename)
        
        assert success is True
        
        # Проверяем, что таблица создана
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='test_table'
        """)
        result = cursor.fetchone()
        assert result is not None
        
        # Проверяем, что версия обновилась
        cursor.execute('SELECT version FROM schema_version WHERE version = ?', (version,))
        version_result = cursor.fetchone()
        assert version_result is not None
        
        conn.close()
    
    def test_migrate_all(self, migration_manager):
        """Тест применения всех миграций"""
        success_count, total = migration_manager.migrate()
        
        assert success_count == total
        assert total >= 1
        
        # Проверяем текущую версию
        current_version = migration_manager.get_current_version()
        assert current_version >= 1
    
    def test_migration_idempotency(self, migration_manager):
        """Тест идемпотентности миграций"""
        # Применяем миграции
        migration_manager.migrate()
        
        # Пробуем применить снова
        pending = migration_manager.get_pending_migrations()
        
        # Не должно быть pending миграций
        assert len(pending) == 0
    
    def test_get_migration_history(self, migration_manager):
        """Тест получения истории миграций"""
        # Применяем миграции
        migration_manager.migrate()
        
        history = migration_manager.get_migration_history()
        
        assert len(history) >= 1
        assert 'version' in history[0]
        assert 'name' in history[0]
        assert 'applied_at' in history[0]


@pytest.mark.integration
class TestRealMigrations:
    """Интеграционные тесты с реальными миграциями проекта"""
    
    def test_apply_all_project_migrations(self, temp_db_path):
        """Тест применения всех миграций проекта"""
        manager = MigrationManager(temp_db_path)
        
        success_count, total = manager.migrate()
        
        assert success_count == total
        assert total >= 3  # У нас минимум 3 миграции
        
        # Проверяем, что все таблицы созданы
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'personal_channels' in tables
        assert 'subscriptions' in tables
        assert 'videos' in tables
        assert 'sync_errors' in tables
        assert 'schema_version' in tables
        
        conn.close()
    
    def test_migration_001_initial_schema(self, temp_db_path):
        """Тест миграции 001: initial_schema"""
        manager = MigrationManager(temp_db_path)
        
        # Применяем только первую миграцию
        manager.migrate(target_version=1)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Проверяем базовые таблицы
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('personal_channels', 'subscriptions', 'videos')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        assert len(tables) == 3
        
        conn.close()
    
    def test_migration_002_subscription_status(self, temp_db_path):
        """Тест миграции 002: add_subscription_status"""
        manager = MigrationManager(temp_db_path)
        
        # Применяем до версии 2
        manager.migrate(target_version=2)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Проверяем новые поля
        cursor.execute('PRAGMA table_info(subscriptions)')
        columns = [row[1] for row in cursor.fetchall()]
        
        assert 'is_active' in columns
        assert 'deleted_by_user' in columns
        assert 'deactivated_at' in columns
        
        conn.close()
    
    def test_migration_003_sync_errors(self, temp_db_path):
        """Тест миграции 003: add_sync_errors"""
        manager = MigrationManager(temp_db_path)
        
        # Применяем все до версии 3
        manager.migrate(target_version=3)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Проверяем таблицу sync_errors
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sync_errors'
        """)
        result = cursor.fetchone()
        
        assert result is not None
        
        conn.close()
    
    def test_incremental_migrations(self, temp_db_path):
        """Тест последовательного применения миграций"""
        manager = MigrationManager(temp_db_path)
        
        # Применяем по одной
        for version in range(1, 4):
            current = manager.get_current_version()
            manager.migrate(target_version=version)
            new_version = manager.get_current_version()
            
            assert new_version == version
            assert new_version > current


@pytest.mark.unit
class TestMigrationCreation:
    """Тесты создания новых миграций"""
    
    def test_create_migration_template(self, tmp_path, monkeypatch):
        """Тест создания шаблона миграции"""
        from migrations.migration_manager import create_migration_template
        
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        
        # Переопределяем путь
        import migrations.migration_manager as mm
        original_file = mm.__file__
        monkeypatch.setattr(mm, '__file__', str(migrations_dir / 'migration_manager.py'))
        
        create_migration_template('test_feature', version=10)
        
        # Проверяем, что файл создан
        migration_file = migrations_dir / '010_test_feature.py'
        assert migration_file.exists()
        
        # Проверяем содержимое (читаем с UTF-8)
        content = migration_file.read_text(encoding='utf-8')
        assert 'def upgrade(cursor):' in content
        assert 'def downgrade(cursor):' in content