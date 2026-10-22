import sqlite3
import time

conn = sqlite3.connect('backend/parking.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
now = time.time()
print(f"Current Time: {now}")

cur.execute("SELECT slot_id, video_id, status, is_reserved, last_seen, (?-last_seen) as seconds_ago FROM slots", (now,))
rows = cur.fetchall()
for r in rows:
    print(dict(r))

conn.close()
