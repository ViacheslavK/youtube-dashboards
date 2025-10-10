"""
Tests for migration system
"""

import pytest
import os
import sqlite3
from pathlib import Path
import tempfile

from migrations.migration_manager import MigrationManager


@pytest.fixture
def temp_migrations_dir(tmp_path):
    """Creates temporary folder with migrations for tests"""
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    
    # Create test migration
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
    """Creates MigrationManager with temporary paths"""
    manager = MigrationManager(temp_db_path)
    # Override migrations folder
    monkeypatch.setattr(manager, 'migrations_dir', temp_migrations_dir)
    return manager


@pytest.mark.unit
class TestMigrationManager:
    """Tests for MigrationManager"""
    
    def test_schema_version_table_created(self, temp_db_path):
        """Test creating schema_version table"""
        manager = MigrationManager(temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Check that table is created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_version'
        """)
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 'schema_version'
        
        conn.close()
    
    def test_get_current_version_initial(self, migration_manager):
        """Test: initial version = 0"""
        version = migration_manager.get_current_version()
        assert version == 0
    
    def test_get_available_migrations(self, migration_manager):
        """Test getting available migrations"""
        migrations = migration_manager.get_available_migrations()
        
        assert len(migrations) >= 1
        assert migrations[0][0] == 1  # Version
        assert '001_test_migration.py' in migrations[0][1]  # Filename
    
    def test_get_pending_migrations(self, migration_manager):
        """Test getting unapplied migrations"""
        pending = migration_manager.get_pending_migrations()
        
        # All migrations should be pending (version = 0)
        assert len(pending) >= 1
    
    def test_apply_migration(self, migration_manager, temp_db_path):
        """Test applying migration"""
        migrations = migration_manager.get_available_migrations()
        version, filename = migrations[0]
        
        success = migration_manager.apply_migration(version, filename)
        
        assert success is True
        
        # Check that table is created
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='test_table'
        """)
        result = cursor.fetchone()
        assert result is not None
        
        # Check that version is updated
        cursor.execute('SELECT version FROM schema_version WHERE version = ?', (version,))
        version_result = cursor.fetchone()
        assert version_result is not None
        
        conn.close()
    
    def test_migrate_all(self, migration_manager):
        """Test applying all migrations"""
        success_count, total = migration_manager.migrate()
        
        assert success_count == total
        assert total >= 1
        
        # Check current version
        current_version = migration_manager.get_current_version()
        assert current_version >= 1
    
    def test_migration_idempotency(self, migration_manager):
        """Test migration idempotency"""
        # Apply migrations
        migration_manager.migrate()
        
        # Try to apply again
        pending = migration_manager.get_pending_migrations()
        
        # Should not have pending migrations
        assert len(pending) == 0
    
    def test_get_migration_history(self, migration_manager):
        """Test getting migration history"""
        # Apply migrations
        migration_manager.migrate()
        
        history = migration_manager.get_migration_history()
        
        assert len(history) >= 1
        assert 'version' in history[0]
        assert 'name' in history[0]
        assert 'applied_at' in history[0]


@pytest.mark.integration
class TestRealMigrations:
    """Integration tests with real project migrations"""
    
    def test_apply_all_project_migrations(self, temp_db_path):
        """Test applying all project migrations"""
        manager = MigrationManager(temp_db_path)
        
        success_count, total = manager.migrate()
        
        assert success_count == total
        assert total >= 3  # We have at least 3 migrations
        
        # Check that all tables are created
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
        """Test migration 001: initial_schema"""
        manager = MigrationManager(temp_db_path)
        
        # Apply only first migration
        manager.migrate(target_version=1)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Check basic tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('personal_channels', 'subscriptions', 'videos')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        assert len(tables) == 3
        
        conn.close()
    
    def test_migration_002_subscription_status(self, temp_db_path):
        """Test migration 002: add_subscription_status"""
        manager = MigrationManager(temp_db_path)
        
        # Apply up to version 2
        manager.migrate(target_version=2)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Check new fields
        cursor.execute('PRAGMA table_info(subscriptions)')
        columns = [row[1] for row in cursor.fetchall()]
        
        assert 'is_active' in columns
        assert 'deleted_by_user' in columns
        assert 'deactivated_at' in columns
        
        conn.close()
    
    def test_migration_003_sync_errors(self, temp_db_path):
        """Test migration 003: add_sync_errors"""
        manager = MigrationManager(temp_db_path)
        
        # Apply all up to version 3
        manager.migrate(target_version=3)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Check sync_errors table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sync_errors'
        """)
        result = cursor.fetchone()
        
        assert result is not None
        
        conn.close()
    
    def test_incremental_migrations(self, temp_db_path):
        """Test sequential application of migrations"""
        manager = MigrationManager(temp_db_path)
        
        # Apply one by one
        for version in range(1, 4):
            current = manager.get_current_version()
            manager.migrate(target_version=version)
            new_version = manager.get_current_version()
            
            assert new_version == version
            assert new_version > current


@pytest.mark.unit
class TestMigrationCreation:
    """Tests for creating new migrations"""
    
    def test_create_migration_template(self, tmp_path, monkeypatch):
        """Test creating migration template"""
        from migrations.migration_manager import create_migration_template
        
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        
        # Override path
        import migrations.migration_manager as mm
        original_file = mm.__file__
        monkeypatch.setattr(mm, '__file__', str(migrations_dir / 'migration_manager.py'))
        
        create_migration_template('test_feature', version=10)
        
        # Check that file is created
        migration_file = migrations_dir / '010_test_feature.py'
        assert migration_file.exists()
        
        # Check content (read with UTF-8)
        content = migration_file.read_text(encoding='utf-8')
        assert 'def upgrade(cursor):' in content
        assert 'def downgrade(cursor):' in content