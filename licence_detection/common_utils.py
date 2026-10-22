import sqlite3
import re
import os
import datetime

# Default DB Path (relative to this file)
DB_NAME = "plates.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)

def init_db(db_path=DB_PATH):
    """Initialize the SQLite database with the vehicle_entries table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicle_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ [DATABASE] Initialized at {db_path}")

def save_plate_to_db(plate_number, db_path=DB_PATH):
    """
    Save a plate number to the database.
    Prevents duplicate entries within a short timeframe (e.g., 15 seconds).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for recent same-plate entries to prevent spamming
    # We'll check if THIS specific plate was seen in the last 15 seconds
    cursor.execute("""
        SELECT id FROM vehicle_entries 
        WHERE plate_number = ? 
        AND timestamp > datetime('now', '-15 seconds')
    """, (plate_number,))
    
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO vehicle_entries (plate_number) VALUES (?)", (plate_number,))
        conn.commit()
        print(f"💾 [DATABASE] Saved New Plate: {plate_number}")
        result = True
    else:
        print(f"⏩ [DATABASE] Skipped Duplicate (Recent): {plate_number}")
        result = False
        
    conn.close()
    return result

def clean_ocr_text(text):
    """
    Clean and correct common OCR errors for License Plates (focus on Indian format logic).
    """
    text = text.upper().strip()
    text = re.sub(r'[^A-Z0-9]', '', text)
    
    if not text:
        return ""

    # 1. Handle Leading Noise
    if len(text) > 10:
        if text[1:3] in ['GJ', 'MH', 'DL', 'KA', 'HR', 'UP', 'TN', 'WB']:
            text = text[1:]
    
    # 2. Basic Correction
    if text.startswith('6J') or text.startswith('G6'):
        text = 'GJ' + text[2:]

    # 3. Smart Character Replacement based on Index (Heuristic for AA 00 AA 0000)
    # We will try to be safe; if exact format isn't matched, some of these might be risky, 
    # but valid plates usually follow this.
    chars = list(text)
    length = len(chars)

    for i in range(length):
        # Digits expected: Positions 2,3 (Area Code) and -4,-3,-2,-1 (Number) if standard
        # Heuristic: If it looks like a standard ~10 char plate
        
        # Simple Logic: 
        # First 2 chars -> Letter
        # Next 2 chars -> Digit
        # Next 1-2 chars -> Letter (optional series)
        # Last 4 chars -> Digit
        
        is_digit_pos = False
        is_letter_pos = False
        
        # Reverse mapping logic
        if i in [2, 3] or i >= length - 4:
            is_digit_pos = True
        elif i in [0, 1]:
            is_letter_pos = True
        # Middle ones are tricky (Series), let's stick to obvious fixes
        
        if is_digit_pos:
            if chars[i] in ['O', 'D', 'Q']: chars[i] = '0'
            if chars[i] == 'I': chars[i] = '1'
            if chars[i] == 'Z': chars[i] = '2'
            if chars[i] == 'S': chars[i] = '5'
            if chars[i] == 'B': chars[i] = '8'
            if chars[i] == 'G': chars[i] = '6'
            
        if is_letter_pos:
            if chars[i] == '0': chars[i] = 'O'
            if chars[i] == '1': chars[i] = 'I'
            if chars[i] == '5': chars[i] = 'S'
            if chars[i] == '8': chars[i] = 'B'
            if chars[i] == '6': chars[i] = 'G'

    return "".join(chars)
