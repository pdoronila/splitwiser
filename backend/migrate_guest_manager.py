"""
Migration script to enable guest-to-guest management.

Changes:
1. Add managed_by_type column to guest_members
2. Rename managed_by_user_id to managed_by_id
3. Set managed_by_type = 'user' for existing managed guests
"""

import sqlite3
import sys

def migrate_guest_manager_fields():
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        print("Starting migration...")
        
        # Step 1: Add managed_by_type column
        print("Adding managed_by_type column...")
        cursor.execute("""
            ALTER TABLE guest_members 
            ADD COLUMN managed_by_type TEXT
        """)
        
        # Step 2: Copy data from managed_by_user_id to temporary column
        print("Creating temporary column for data migration...")
        cursor.execute("""
            ALTER TABLE guest_members 
            ADD COLUMN managed_by_id_temp INTEGER
        """)
        
        cursor.execute("""
            UPDATE guest_members 
            SET managed_by_id_temp = managed_by_user_id
        """)
        
        # Step 3: Set managed_by_type = 'user' for existing managed guests
        print("Setting managed_by_type for existing records...")
        cursor.execute("""
            UPDATE guest_members 
            SET managed_by_type = 'user' 
            WHERE managed_by_user_id IS NOT NULL
        """)
        
        # Step 4: Drop old column and rename temp column
        # SQLite doesn't support DROP COLUMN or RENAME COLUMN directly in all versions
        # So we'll create a new table and copy data
        print("Recreating table with new schema...")
        cursor.execute("""
            CREATE TABLE guest_members_new (
                id INTEGER PRIMARY KEY,
                group_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_by_id INTEGER NOT NULL,
                claimed_by_id INTEGER,
                managed_by_id INTEGER,
                managed_by_type TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO guest_members_new 
            SELECT id, group_id, name, created_by_id, claimed_by_id, 
                   managed_by_id_temp, managed_by_type
            FROM guest_members
        """)
        
        cursor.execute("DROP TABLE guest_members")
        cursor.execute("ALTER TABLE guest_members_new RENAME TO guest_members")
        
        conn.commit()
        print("Migration completed successfully!")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(guest_members)")
        columns = cursor.fetchall()
        print("\nNew table schema:")
        for col in columns:
            print(f"  {col[1]} {col[2]}")
        
        cursor.execute("SELECT COUNT(*) FROM guest_members WHERE managed_by_type = 'user'")
        count = cursor.fetchone()[0]
        print(f"\nMigrated {count} managed guests to new schema")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    success = migrate_guest_manager_fields()
    sys.exit(0 if success else 1)
