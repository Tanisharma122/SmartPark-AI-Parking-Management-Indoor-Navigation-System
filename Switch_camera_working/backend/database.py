import sqlite3

DB_PATH = "parking.db"

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS slots (
        slot_id TEXT,
        camera_id TEXT,
        status TEXT,
        last_seen REAL,
        PRIMARY KEY (slot_id, camera_id)
    )
    """)

    conn.commit()
    conn.close()
