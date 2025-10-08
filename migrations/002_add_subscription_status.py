"""
Migration 002: Add Subscription Status

Adds fields for tracking subscription status (active/inactive).
"""


def upgrade(cursor):
    """Applies the migration."""
    
    # Check if these fields already exist (for idempotency)
    cursor.execute("PRAGMA table_info(subscriptions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add is_active
    if 'is_active' not in columns:
        cursor.execute('''
            ALTER TABLE subscriptions 
            ADD COLUMN is_active BOOLEAN DEFAULT 1
        ''')
        print("  [OK] Added field: is_active")
    
    # Add deleted_by_user
    if 'deleted_by_user' not in columns:
        cursor.execute('''
            ALTER TABLE subscriptions 
            ADD COLUMN deleted_by_user BOOLEAN DEFAULT 0
        ''')
        print("  [OK] Added field: deleted_by_user")
    
    # Add deactivated_at
    if 'deactivated_at' not in columns:
        cursor.execute('''
            ALTER TABLE subscriptions 
            ADD COLUMN deactivated_at TIMESTAMP
        ''')
        print("  [OK] Added field: deactivated_at")
    
    # Create index
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_subscriptions_active 
        ON subscriptions(personal_channel_id, is_active, deleted_by_user)
    ''')
    print("  [OK] Created index: idx_subscriptions_active")
