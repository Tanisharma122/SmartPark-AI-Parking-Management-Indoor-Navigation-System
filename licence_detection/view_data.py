import sqlite3
import os
from common_utils import DB_PATH

def view_data():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        print("Run the detection scripts first to generate data.")
        return

    print(f"📂 Opening Database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM vehicle_entries ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        print("\n" + "="*50)
        print(f"{'ID':<5} | {'PLATE NUMBER':<15} | {'TIMESTAMP':<20}")
        print("="*50)
        
        if not rows:
            print("   (No entries found)")
        else:
            for row in rows:
                # row structure: (id, plate_number, timestamp)
                print(f"{row[0]:<5} | {row[1]:<15} | {row[2]:<20}")
        
        print("="*50 + "\n")
        print(f"Total Entries: {len(rows)}")
        
    except sqlite3.OperationalError as e:
        print(f"❌ Error querying database: {e}")
        
    conn.close()
    input("\nPress Enter to close...")

if __name__ == "__main__":
    view_data()
