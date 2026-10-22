import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "parking.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT key, key_type, basement_id, is_active FROM api_keys")
rows = cur.fetchall()

print("\n--- API KEYS IN DB ---")
for r in rows:
    print(r)

conn.close()
