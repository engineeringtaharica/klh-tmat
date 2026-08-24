import sqlite3
import os
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tmat_logger_queue.db")
CSV_PATH = os.path.join(BASE_DIR, "customers.csv")

def init_db():
    print("[DATABASE] Validating local database queue schema...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            licor_sn TEXT UNIQUE NOT NULL,
            licor_token TEXT NOT NULL,
            klh_api_key TEXT NOT NULL,
            klh_device_id_unik TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id_unik TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tmat_value REAL DEFAULT 0,
            hujan_value REAL DEFAULT 0,
            kelembapan_tanah REAL DEFAULT 0,
            suhu_value REAL DEFAULT 0,
            ph_value REAL DEFAULT 0,
            baterai_value REAL DEFAULT 0,
            klh_insert_id INTEGER DEFAULT NULL,
            klh_received_at TEXT DEFAULT NULL,
            UNIQUE(device_id_unik, timestamp)
        )
    ''')
    conn.commit()
    conn.close()

def get_last_timestamp(device_id_unik):
    """Finds the most recent hourly data point stored for this specific logger."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(timestamp) FROM sensor_data WHERE device_id_unik = ?', (device_id_unik,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else None

def sync_config_from_csv():
    if not os.path.exists(CSV_PATH):
        print(f"[DATABASE] [WARNING] Configuration file '{CSV_PATH}' not found. Skipping auto-sync.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        with open(CSV_PATH, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('licor_sn') or not row['licor_sn'].strip():
                    continue
                cursor.execute('''
                    INSERT INTO devices_config (customer_name, licor_sn, licor_token, klh_api_key, klh_device_id_unik)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(licor_sn) DO UPDATE SET
                        customer_name = excluded.customer_name,
                        licor_token = excluded.licor_token,
                        klh_api_key = excluded.klh_api_key,
                        klh_device_id_unik = excluded.klh_device_id_unik
                ''', (
                    row['customer_name'].strip(), row['licor_sn'].strip(),
                    row['licor_token'].strip(), row['klh_api_key'].strip(),
                    row['klh_device_id_unik'].strip()
                ))
        conn.commit()
    except Exception as e:
        print(f"[DATABASE] [ERROR] Failed to read Excel CSV file: {e}")
    finally:
        conn.close()

def get_active_loggers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT customer_name, licor_sn, licor_token, klh_api_key, klh_device_id_unik FROM devices_config')
    rows = cursor.fetchall()
    conn.close()
    return [{
        "customer_name": r[0], "licor_sn": r[1], "licor_token": r[2], 
        "klh_api_key": r[3], "klh_device_id_unik": r[4]
    } for r in rows]

def save_to_queue(all_data):
    if not all_data:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    inserted_count = 0
    for item in all_data:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO sensor_data 
                (device_id_unik, timestamp, tmat_value, hujan_value, kelembapan_tanah, suhu_value, ph_value, baterai_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['device_id_unik'], item['timestamp'], item['tmat_value'], 
                item['hujan_value'], item['kelembapan_tanah'], item['suhu_value'], 
                item['ph_value'], item['baterai_value']
            ))
            if cursor.rowcount > 0:
                inserted_count += 1
        except sqlite3.Error as e:
            print(f"[DATABASE] [ERROR] Fault: {e}")
    conn.commit()
    conn.close()
    if inserted_count > 0:
        print(f"[DATABASE] Enqueued {inserted_count} new hourly backlog records.")

def fetch_unsent_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.device_id_unik, s.tmat_value, s.hujan_value, s.kelembapan_tanah, 
               s.suhu_value, s.ph_value, s.baterai_value, c.klh_api_key
        FROM sensor_data s
        JOIN devices_config c ON s.device_id_unik = c.klh_device_id_unik
        WHERE s.klh_insert_id IS NULL
        ORDER BY s.timestamp ASC
    ''')
    records = cursor.fetchall()
    conn.close()
    return records

def mark_as_sent_with_audit(audit_records):
    if not audit_records:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executemany('''
        UPDATE sensor_data SET klh_insert_id = ?, klh_received_at = ? WHERE id = ?
    ''', audit_records)
    conn.commit()
    conn.close()
