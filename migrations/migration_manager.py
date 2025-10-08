"""
Database migration management system.
"""

import sqlite3
import os
import importlib.util
from typing import List, Tuple
from datetime import datetime
from locales.i18n import t, load_locale_from_config

# Load locale from settings
load_locale_from_config()


class MigrationManager:
    """Database migration manager."""
    
    def __init__(self, db_path: str = "database/videos.db"):
        self.db_path = db_path
        # Create the folder for the database if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.migrations_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__))
        )
        self._ensure_schema_version_table()
    
    def _ensure_schema_version_table(self):
        """Create a table to track versions."""
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
        """Get the current database schema version."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(version) FROM schema_version')
        result = cursor.fetchone()[0]
        
        conn.close()
        return result if result is not None else 0
    
    def get_available_migrations(self) -> List[Tuple[int, str]]:
        """
        Get a list of available migrations.
        
        Returns:
            List of (version, filename) tuples
        """
        migrations = []
        
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.py') and filename[0].isdigit():
                # Format: 001_migration_name.py
                try:
                    version = int(filename.split('_')[0])
                    migrations.append((version, filename))
                except ValueError:
                    continue
        
        # Sort by version
        migrations.sort(key=lambda x: x[0])
        return migrations
    
    def get_pending_migrations(self) -> List[Tuple[int, str]]:
        """Get migrations that need to be applied."""
        current_version = self.get_current_version()
        all_migrations = self.get_available_migrations()
        
        # Filter only those that are greater than the current version
        pending = [(v, f) for v, f in all_migrations if v > current_version]
        return pending
    
    def load_migration(self, filename: str):
        """Load a migration module."""
        file_path = os.path.join(self.migrations_dir, filename)
        
        spec = importlib.util.spec_from_file_location("migration", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def apply_migration(self, version: int, filename: str) -> bool:
        """
        Apply a single migration.
        
        Returns:
            True if successful, False if there is an error.
        """
        try:
            print(f"\n{'─' * 60}")
            print(t('migrations.applying_migration', version=version, filename=filename))
            print('─' * 60)
            
            # Load the migration module
            module = self.load_migration(filename)
            
            # Get the upgrade function
            if not hasattr(module, 'upgrade'):
                print(f"❌ {t('migrations.migration_missing_upgrade', filename=filename)}")
                return False
            
            # Apply the migration
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Execute the upgrade
                module.upgrade(cursor)
                
                # Record the version
                migration_name = filename.replace('.py', '').replace(f'{version:03d}_', '')
                cursor.execute('''
                    INSERT INTO schema_version (version, name)
                    VALUES (?, ?)
                ''', (version, migration_name))
                
                conn.commit()
                print(f"[OK] {t('migrations.migration_applied', version=version)}")
                return True

            except Exception as e:
                conn.rollback()
                print(f"❌ {t('migrations.migration_apply_error', version=version, error=str(e))}")
                return False
            finally:
                conn.close()
        
        except Exception as e:
            print(f"❌ {t('migrations.migration_load_error', filename=filename, error=str(e))}")
            return False
    
    def migrate(self, target_version: int = None) -> Tuple[int, int]:
        """
        Apply all necessary migrations.
        
        Args:
            target_version: The target version (None = latest).
            
        Returns:
            (successful_migrations, total_migrations)
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
                # Stop on the first error
                print(f"\n⚠️  {t('migrations.migration_interrupted')}")
                break
        
        return (success_count, len(pending))
    
    def get_migration_history(self) -> List[dict]:
        """Get the history of applied migrations."""
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
        """Print the migration status."""
        current_version = self.get_current_version()
        pending = self.get_pending_migrations()
        all_migrations = self.get_available_migrations()

        print(f"\n{'=' * 60}")
        print(t('migrations.title'))
        print('=' * 60)
        print(f"\n{t('migrations.current_version', version=current_version)}")
        print(t('migrations.available', count=len(all_migrations)))
        print(t('migrations.pending', count=len(pending)))

        if pending:
            print(f"\n{t('migrations.pending_list')}")
            for version, filename in pending:
                migration_name = filename.replace('.py', '').replace(f'{version:03d}_', '')
                print(f"  [{version}] {migration_name}")

        # History
        history = self.get_migration_history()
        if history:
            print(f"\n{t('migrations.applied_list')}")
            for record in history:
                applied = datetime.fromisoformat(record['applied_at'])
                print(f"  [{record['version']}] {record['name']} "
                      f"({applied.strftime('%Y-%m-%d %H:%M')})")

        print('=' * 60)


def create_migration_template(name: str, version: int = None):
    """
    Create a new migration template.
    
    Args:
        name: The name of the migration (e.g., "add_user_settings").
        version: The version number (if None, the next available version is used).
    """
    migrations_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine the version
    if version is None:
        manager = MigrationManager()
        all_migrations = manager.get_available_migrations()
        version = max([v for v, _ in all_migrations], default=0) + 1
    
    # Format the filename
    filename = f"{version:03d}_{name}.py"
    filepath = os.path.join(migrations_dir, filename)
    
    if os.path.exists(filepath):
        print(f"❌ {t('migrations.migration_already_exists', filename=filename)}")
        return
    
    # Migration template
    template = f'''"""
Migration {version}: {name.replace('_', ' ').title()}

Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""


def upgrade(cursor):
    """
    Applies the migration.
    
    Args:
        cursor: SQLite cursor
    """
    # Example: add a new field
    # cursor.execute(\'\'\'
    #     ALTER TABLE table_name 
    #     ADD COLUMN new_column TEXT DEFAULT 'default_value'
    # \'\'\')
    
    # Example: create a new table
    # cursor.execute(\'\'\'
    #     CREATE TABLE IF NOT EXISTS new_table (
    #         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         name TEXT NOT NULL
    #     )
    # \'\'\')
    
    # Example: create an index
    # cursor.execute(\'\'\'
    #     CREATE INDEX IF NOT EXISTS idx_table_column 
    #     ON table_name(column_name)
    # \'\'\')
    
    pass


def downgrade(cursor):
    """
    Reverts the migration (optional, for future use).
    
    Args:
        cursor: SQLite cursor
    """
    # SQLite does not support DROP COLUMN, so rollback is complicated.
    # Usually not used, but can be implemented by recreating the table.
    pass
'''
    
    # Save the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"[OK] Created migration: {filename}")
    print(f"  Path: {filepath}")
    print("\nEdit the file and add necessary changes to the upgrade() function")
