import os
import json
import sqlite3

# Jika dijalankan di Railway, gunakan path dari environment variable (misal: /app/data/database.db)
# Jika lokal, gunakan 'database.db'
DB_PATH = os.environ.get('DATABASE_PATH', 'database.db')

def get_db_connection():
    # Local SQLite fallback
    return sqlite3.connect(DB_PATH, timeout=30.0)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movie_analysis (
            id_title    TEXT PRIMARY KEY,
            result_data TEXT,
            created_at  TIMESTAMP
        )
    ''')
    # [ARSITEKTUR] Migrasi: tambah kolom created_at jika tabel lama belum punya.
    try:
        cursor.execute("ALTER TABLE movie_analysis ADD COLUMN created_at TIMESTAMP")
        cursor.execute("UPDATE movie_analysis SET created_at = datetime('now') WHERE created_at IS NULL")
    except Exception:
        pass  # Kolom sudah ada — abaikan
    # Background tasks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS background_tasks (
            task_id TEXT PRIMARY KEY,
            task_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT task_data FROM background_tasks WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def set_task(task_id, task_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO background_tasks (task_id, task_data) 
        VALUES (?, ?) 
        ON CONFLICT(task_id) DO UPDATE SET task_data = excluded.task_data
    ''', (task_id, json.dumps(task_data)))
    conn.commit()
    conn.close()
