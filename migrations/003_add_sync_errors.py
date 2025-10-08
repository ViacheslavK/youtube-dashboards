"""
Migration 003: Add Sync Errors

Adds a table for logging synchronization errors.
"""


def upgrade(cursor):
    """Applies the migration."""
    
    # Create table for synchronization errors
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
    
    # Create index
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sync_errors_unresolved 
        ON sync_errors(resolved, occurred_at DESC)
    ''')
    print("  [OK] Created index: idx_sync_errors_unresolved")
