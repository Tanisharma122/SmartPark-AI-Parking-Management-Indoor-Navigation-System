from database import init, db

init()

conn = db()
cur = conn.cursor()

cur.execute(
    "INSERT OR IGNORE INTO api_keys (key, owner) VALUES (?, ?)",
    ("sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f", "admin")
)

conn.commit()
conn.close()

print("✅ API key inserted and table initialized")
