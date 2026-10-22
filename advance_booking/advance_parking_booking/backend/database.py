import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "parking.db")

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            location TEXT,
            wing TEXT,
            slot TEXT,
            start_time TEXT,
            duration REAL,
            amount INTEGER,
            coupon TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_booking(data):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO bookings (timestamp, location, wing, slot, start_time, duration, amount, coupon, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['timestamp'], data['location'], data['wing'], data['slot'],
        data['start_time'], data['duration'], data['amount'], data['coupon'], 'CONFIRMED'
    ))
    conn.commit()
    conn.close()

def get_all_bookings():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    import pandas as pd
    df = pd.read_sql_query("SELECT * FROM bookings ORDER BY id DESC", conn)
    conn.close()
    return df
