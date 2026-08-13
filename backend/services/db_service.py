import os
import json
import datetime

# Supabase Postgres URL
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_POSTGRES = DATABASE_URL is not None and DATABASE_URL.startswith('postgres')

if IS_POSTGRES:
    import psycopg2
else:
    import sqlite3

DB_PATH = os.environ.get('DATABASE_PATH', 'database.db')

def get_db_connection():
    if IS_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect(DB_PATH, timeout=30.0)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if IS_POSTGRES:
        # PostgreSQL schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movie_analysis (
                id_title    TEXT PRIMARY KEY,
                result_data TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS background_tasks (
                task_id TEXT PRIMARY KEY,
                task_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # SQLite schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movie_analysis (
                id_title    TEXT PRIMARY KEY,
                result_data TEXT,
                created_at  TIMESTAMP
            )
        ''')
        try:
            cursor.execute("ALTER TABLE movie_analysis ADD COLUMN created_at TIMESTAMP")
            cursor.execute("UPDATE movie_analysis SET created_at = datetime('now') WHERE created_at IS NULL")
        except Exception:
            pass
            
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS background_tasks (
                task_id TEXT PRIMARY KEY,
                task_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS FOR TASKS ---
def get_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT task_data FROM background_tasks WHERE task_id = %s" if IS_POSTGRES else "SELECT task_data FROM background_tasks WHERE task_id = ?"
    cursor.execute(query, (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None

def set_task(task_id, task_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data_str = json.dumps(task_data)
    if IS_POSTGRES:
        query = '''
            INSERT INTO background_tasks (task_id, task_data) 
            VALUES (%s, %s) 
            ON CONFLICT (task_id) DO UPDATE SET task_data = EXCLUDED.task_data
        '''
    else:
        query = '''
            INSERT INTO background_tasks (task_id, task_data) 
            VALUES (?, ?) 
            ON CONFLICT(task_id) DO UPDATE SET task_data = excluded.task_data
        '''
    
    cursor.execute(query, (task_id, data_str))
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS FOR MOVIE ANALYSIS ---
def save_movie_analysis(id_title, result_data_dict, created_at=None):
    if not created_at:
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    data_str = json.dumps(result_data_dict)
    
    if IS_POSTGRES:
        query = '''
            INSERT INTO movie_analysis (id_title, result_data, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (id_title) DO UPDATE 
            SET result_data = EXCLUDED.result_data, created_at = EXCLUDED.created_at
        '''
    else:
        query = '''
            INSERT OR REPLACE INTO movie_analysis (id_title, result_data, created_at)
            VALUES (?, ?, ?)
        '''
        
    cursor.execute(query, (id_title, data_str, created_at))
    conn.commit()
    conn.close()

def get_movie_analysis(id_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT result_data FROM movie_analysis WHERE id_title = %s" if IS_POSTGRES else "SELECT result_data FROM movie_analysis WHERE id_title = ?"
    cursor.execute(query, (id_title,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None

def get_all_movie_analysis():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id_title, result_data FROM movie_analysis ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            'id_title': row[0],
            'result_data': json.loads(row[1])
        })
    return results

def delete_movie_analysis(id_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "DELETE FROM movie_analysis WHERE id_title = %s" if IS_POSTGRES else "DELETE FROM movie_analysis WHERE id_title = ?"
    cursor.execute(query, (id_title,))
    conn.commit()
    conn.close()
