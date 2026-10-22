import sqlite3
import os

# ---------- DB CONNECTION ----------
def db():
    db_path = os.path.join(os.path.dirname(__file__), "parking.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- INITIALIZE DATABASE ----------
def init():
    conn = db()
    cur = conn.cursor()

    # ===============================
    # ORGANIZATIONS (SaaS customers)
    # ===============================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            org_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    # ===============================
    # BASEMENTS / ZONES (Geo location)
    # ===============================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS basements (
            basement_id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            name TEXT,
            latitude REAL,
            longitude REAL,
            FOREIGN KEY (org_id) REFERENCES organizations(org_id)
        )
    """)

    # ===============================
    # VIDEOS (video files or IP streams)
    # ===============================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            basement_id TEXT NOT NULL,
            type TEXT,              -- video / ip
            source TEXT,            -- video path or rtsp url
            latitude REAL,          -- geo location
            longitude REAL,         -- geo location
            lanes_file TEXT,        -- path to lanes.json
            slots_file TEXT,        -- path to slots.json
            image_file TEXT,        -- path to background image
            is_active INTEGER DEFAULT 1,
            last_heartbeat REAL DEFAULT 0,
            FOREIGN KEY (basement_id) REFERENCES basements(basement_id)
        )
    """)

    # ===============================
    # API KEYS (Unified Scope)
    # ===============================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            key_type TEXT NOT NULL,     -- 'org', 'basement', 'device'
            target_id TEXT NOT NULL,    -- ID of the entity this key belongs to
            owner TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    # ===============================
    # SLOTS (REAL-TIME DATA)
    # ===============================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            slot_id TEXT,
            video_id TEXT,
            status TEXT,
            last_seen REAL,
            is_reserved INTEGER DEFAULT 0,
            reserved_at REAL DEFAULT 0,
            reserved_by TEXT,
            PRIMARY KEY (slot_id, video_id),
            FOREIGN KEY (video_id) REFERENCES videos(video_id)
        )
    """)

    # ===============================
    # SYSTEM LOGS (GLOBAL ERRORS)
    # ===============================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            org_id TEXT,          -- Which client this belongs to
            level TEXT,           -- INFO, WARNING, ERROR, CRITICAL
            source TEXT,          -- Backend, Node_VID1, etc.
            message TEXT,
            FOREIGN KEY (org_id) REFERENCES organizations(org_id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Video-centric database initialized successfully.")

# ---------- RUN DIRECTLY ----------
if __name__ == "__main__":
    init()
