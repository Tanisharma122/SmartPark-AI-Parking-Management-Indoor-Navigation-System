import sqlite3
import os

def db():
    # Use absolute path for database
    db_path = os.path.join(os.path.dirname(__file__), "parking.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = db()
    cur = conn.cursor()
    
    # 1. Clean start: Drop existing table to fix primary key issues
    cur.execute("DROP TABLE IF EXISTS slots")
    
    # 2. Recreate with correct constraints
    cur.execute("""
        CREATE TABLE slots (
            slot_id TEXT,
            camera_id TEXT,
            status TEXT,
            last_seen REAL,
            PRIMARY KEY (slot_id, camera_id)
        )
    """)
    
    # 3. Ensure API KEYS table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            owner TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with strict constraints.")

if __name__ == "__main__":
    init()
