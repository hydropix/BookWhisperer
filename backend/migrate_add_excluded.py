"""Migration script to add 'excluded' column to chapters table."""
import sqlite3

DB_PATH = "bookwhisperer.db"

def migrate():
    """Add excluded column to chapters table."""
    print("Running migration: Add 'excluded' column to chapters table...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(chapters)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'excluded' in columns:
        print("Column 'excluded' already exists. Skipping migration.")
        conn.close()
        return

    # Add the column
    cursor.execute("ALTER TABLE chapters ADD COLUMN excluded INTEGER DEFAULT 0 NOT NULL")

    conn.commit()
    conn.close()

    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
