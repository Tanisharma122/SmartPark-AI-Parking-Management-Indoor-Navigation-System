import sqlite3
import os

db_path = "backend/parking.db" if os.path.exists("backend/parking.db") else "parking.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print(f"--- API Keys in {db_path} ---")
    try:
        for row in cur.execute("SELECT key, owner, active FROM api_keys"):
            status = "Active" if row[2] == 1 else "Inactive"
            print(f"Key: {row[0]} | Owner: {row[1]} | Status: {status}")
    except sqlite3.OperationalError:
        print("❌ Table 'api_keys' does not exist.")

    conn.close()
