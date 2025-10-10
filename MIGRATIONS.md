# Database Migrations Guide

## Concept

SubDeck for YouTube uses a versioned migration system to manage database schema changes.

### Principles:

1. **Each migration** = separate file with version number
2. **Sequential application** - migrations are applied in order
3. **Idempotency** - can be run repeatedly safely
4. **Add-only** - migrations don't delete user data
5. **Version tracking** - `schema_version` table stores history

## Usage

### Check migration status

```bash
python migrate.py status
```

Shows:
- Current database schema version
- Available migrations
- Unapplied migrations
- History of applied migrations

### Apply all migrations

```bash
python migrate.py up
```

Applies all unapplied migrations sequentially.

### Apply up to specific version

```bash
python migrate.py up --target 3
```

Applies migrations up to version 3 inclusive.

## Application Update Scenario

### Situation: User upgrades from version 1.0 to 3.0

```
Версия 1.0 (схема v1) → Версия 2.0 (схема v2) → Версия 3.0 (схема v3)
```

**What happens:**

1. User downloads version 3.0
2. On first run (or manually) executes: `python migrate.py up`
3. System determines current DB version: `v1`
4. Applies migrations: `v1 → v2 → v3` sequentially
5. User data is preserved, only new fields/tables are added

**Safety:**
- If migration v2 fails → process stops
- User can fix the problem and run again
- Already applied migrations are skipped

## Creating a new migration

### Automatic template creation

```bash
python migrate.py create add_user_settings
```

Will create file: `migrations/004_add_user_settings.py`

### Migration structure

```python
"""
Migration 004: Add User Settings

Description of changes
"""

def upgrade(cursor):
    """Apply migration"""
    
    # Adding field
    cursor.execute('''
        ALTER TABLE personal_channels 
        ADD COLUMN default_view TEXT DEFAULT 'grid'
    ''')
    
    # Creating table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT
        )
    ''')
    
    # Creating index
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_settings_key 
        ON user_settings(key)
    ''')
    
    print("  ✓ User settings added")
```

## Existing migrations

### 001: Initial Schema
- Создание базовых таблиц: `personal_channels`, `subscriptions`, `videos`
- Индексы для оптимизации

### 002: Add Subscription Status
- Поля: `is_active`, `deleted_by_user`, `deactivated_at`
- Отслеживание статуса подписок

### 003: Add Sync Errors
- Таблица `sync_errors` для логирования ошибок
- Индексы для быстрого поиска

## Best practices

### ✅ Do:

1. **Use `IF NOT EXISTS`** for tables and indexes
2. **Check column existence** before adding (PRAGMA table_info)
3. **Add DEFAULT values** for new fields
4. **Document changes** in migration docstring
5. **Test on database copy** before release

### ❌ Don't do:

1. **Don't delete columns** (SQLite doesn't support DROP COLUMN easily)
2. **Don't change data types** of existing columns
3. **Don't delete user data**
4. **Don't change already applied migrations** - create new ones
5. **Don't rely on specific record order** in database

## Migration rollback

Rollback (downgrade) **is not implemented** by default because:
- SQLite has limited ALTER TABLE support
- DROP COLUMN is not supported
- Risk of data loss

If rollback is needed:
1. Make database backup
2. Restore from backup
3. Apply required migrations

## Backup

**Always make backup before migration!**

```bash
# Automatic backup (recommended to add to migrate.py)
cp database/videos.db database/videos.db.backup
```

## schema_version table structure

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,    -- Migration version number
    name TEXT NOT NULL,             -- Migration name
    applied_at TIMESTAMP            -- When applied
);
```

Example data:

| version | name | applied_at |
|---------|------|------------|
| 1 | initial_schema | 2025-01-15 10:30:00 |
| 2 | add_subscription_status | 2025-01-20 14:15:00 |
| 3 | add_sync_errors | 2025-01-25 09:45:00 |

## Troubleshooting

### Error: "Migration X failed"

1. Check error log
2. Fix the problem (possibly SQL syntax)
3. Run `python migrate.py up` again
4. Already applied migrations will be skipped

### Error: "Table already exists"

- This is normal if `CREATE TABLE IF NOT EXISTS` is used
- Check that migration is idempotent

### "Version mismatch after update"

```bash
# Check status
python migrate.py status

# Apply missing migrations
python migrate.py up
```

### Full schema reinstallation (⚠️ WILL DELETE ALL DATA)

```bash
# Backup
cp database/videos.db database/videos.db.backup

# Delete DB
rm database/videos.db

# Create anew
python migrate.py up
```

## Integration into CI/CD

### Automatic check during deployment

```bash
# In deployment script
python migrate.py status
python migrate.py up --yes  # (if --yes flag is added)
```

## Real-world scenario examples

### Scenario 1: Adding new feature

**Task:** Add favorite videos

```bash
# Create migration
python migrate.py create add_favorites

# Edit migrations/004_add_favorites.py:
```

```python
def upgrade(cursor):
    cursor.execute('''
        ALTER TABLE videos 
        ADD COLUMN is_favorite BOOLEAN DEFAULT 0
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_videos_favorite 
        ON videos(is_favorite, published_at DESC)
    ''')
    
    print("  ✓ Favorite feature added")
```

```bash
# Apply
python migrate.py up
```

### Scenario 2: Structure refactoring

**Task:** Separate channel and email into different tables

```bash
python migrate.py create separate_user_accounts
```

```python
def upgrade(cursor):
    # Create new table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT
        )
    ''')
    
    # Add relation to existing table
    cursor.execute('''
        ALTER TABLE personal_channels 
        ADD COLUMN user_account_id INTEGER 
        REFERENCES user_accounts(id)
    ''')
    
    # Data migration (if needed)
    # ... логика переноса ...
    
    print("  ✓ User accounts separated")
```

### Scenario 3: Performance optimization

**Task:** Add index for fast search

```bash
python migrate.py create optimize_video_search
```

```python
def upgrade(cursor):
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_videos_title_search 
        ON videos(title)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_videos_channel_date 
        ON videos(subscription_id, published_at DESC, is_watched)
    ''')
    
    print("  ✓ Indexes added for optimization")
```

## FAQ

**Q: Can a migration be skipped?**
A: No, migrations are applied sequentially. This ensures integrity.

**Q: What if I have an old DB version without schema_version?**
A: The system will automatically create the table and determine version as 0.

**Q: How to rollback to previous version?**
A: Restore from backup. Full rollback is not supported.

**Q: How many migrations can be created?**
A: Practically unlimited. Versions from 001 to 999.

**Q: Should migrations be committed to Git?**
A: Yes! Migrations are part of application code.

**Q: How to test migrations?**
A: Create DB copy and test on it before production.

## File structure

```
youtube-dashboard/
├── migrations/
│   ├── __init__.py
│   ├── migration_manager.py      # Система управления
│   ├── 001_initial_schema.py
│   ├── 002_add_subscription_status.py
│   ├── 003_add_sync_errors.py
│   └── 004_your_new_migration.py
├── migrate.py                     # CLI utility
└── database/
    └── videos.db                  # DB with schema_version table
```

## Conclusion

Migration system provides:
- ✅ Safe application updates
- ✅ User data preservation
- ✅ Change transparency
- ✅ Version skipping capability (e.g., 1.0 → 3.0)
- ✅ Rollback via backups

**Remember:** Always make backup before migration in production!
