#!/usr/bin/env python3
"""
Migration script to add split_type column to expenses table
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(expenses)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'split_type' not in columns:
        print("Adding split_type column to expenses table...")
        cursor.execute("ALTER TABLE expenses ADD COLUMN split_type TEXT DEFAULT 'EQUAL'")

        # Migrate existing data by inferring split type
        print("Migrating existing expense data...")

        # Get all expenses
        cursor.execute("SELECT id FROM expenses")
        expense_ids = [row[0] for row in cursor.fetchall()]

        for expense_id in expense_ids:
            # Check for itemized expenses
            cursor.execute("SELECT COUNT(*) FROM expense_items WHERE expense_id = ?", (expense_id,))
            has_items = cursor.fetchone()[0] > 0

            if has_items:
                cursor.execute("UPDATE expenses SET split_type = 'ITEMIZED' WHERE id = ?", (expense_id,))
                continue

            # Check splits for percentage/shares
            cursor.execute("SELECT percentage, shares, amount_owed FROM expense_splits WHERE expense_id = ?", (expense_id,))
            splits = cursor.fetchall()

            if not splits:
                continue

            # Check for percentage splits
            if splits[0][0] is not None:
                cursor.execute("UPDATE expenses SET split_type = 'PERCENT' WHERE id = ?", (expense_id,))
            # Check for share splits
            elif splits[0][1] is not None:
                cursor.execute("UPDATE expenses SET split_type = 'SHARES' WHERE id = ?", (expense_id,))
            else:
                # Check if amounts vary (EXACT vs EQUAL)
                amounts = [s[2] for s in splits]
                if len(amounts) > 1 and max(amounts) - min(amounts) > 1:
                    cursor.execute("UPDATE expenses SET split_type = 'EXACT' WHERE id = ?", (expense_id,))
                else:
                    cursor.execute("UPDATE expenses SET split_type = 'EQUAL' WHERE id = ?", (expense_id,))

        conn.commit()
        print(f"Migration complete! Updated {len(expense_ids)} expenses.")
    else:
        print("Column split_type already exists, skipping migration.")

    conn.close()

if __name__ == "__main__":
    migrate()
