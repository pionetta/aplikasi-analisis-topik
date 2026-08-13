import sqlite3
import os
import json

try:
    import psycopg2
except ImportError:
    print("Harap install psycopg2 terlebih dahulu dengan mengetik perintah ini di terminal:")
    print("pip install psycopg2-binary")
    exit(1)

# Ganti dengan Connection String Supabase Anda (jangan lupa password-nya dimasukkan)
SUPABASE_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres.[PROYEK_ANDA]:[PASSWORD_ANDA]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres')

# Lokasi database lokal SQLite Anda
LOCAL_DB_PATH = '../backend/database.db'

def migrate():
    if not os.path.exists(LOCAL_DB_PATH):
        print(f"Error: Database lokal tidak ditemukan di {LOCAL_DB_PATH}")
        return

    print("Membaca data dari database lokal (SQLite)...")
    local_conn = sqlite3.connect(LOCAL_DB_PATH)
    local_cursor = local_conn.cursor()

    try:
        local_cursor.execute("SELECT id_title, result_data, created_at FROM movie_analysis")
        movies = local_cursor.fetchall()
        print(f"Ditemukan {len(movies)} baris di tabel movie_analysis (Lokal).")
    except Exception as e:
        print(f"Gagal membaca tabel movie_analysis lokal: {e}")
        movies = []

    if not movies:
        print("Tidak ada data untuk dimigrasikan.")
        return

    print("Menghubungkan ke Supabase (PostgreSQL)...")
    try:
        supa_conn = psycopg2.connect(SUPABASE_DB_URL)
        supa_cursor = supa_conn.cursor()
        
        # Buat tabel jika belum ada (sekadar jaga-jaga)
        supa_cursor.execute('''
            CREATE TABLE IF NOT EXISTS movie_analysis (
                id_title    TEXT PRIMARY KEY,
                result_data TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        success_count = 0
        for row in movies:
            id_title, result_data, created_at = row
            try:
                # Upsert query untuk PostgreSQL
                supa_cursor.execute('''
                    INSERT INTO movie_analysis (id_title, result_data, created_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id_title) DO UPDATE 
                    SET result_data = EXCLUDED.result_data, 
                        created_at = EXCLUDED.created_at
                ''', (id_title, result_data, created_at))
                success_count += 1
            except Exception as e:
                print(f"Gagal migrasi data {id_title}: {e}")
        
        supa_conn.commit()
        print(f"Migrasi selesai! Berhasil memindahkan {success_count}/{len(movies)} baris histori ke Supabase.")
        
    except Exception as e:
        print(f"Gagal terhubung ke Supabase atau mengeksekusi query: {e}")
    finally:
        if 'supa_conn' in locals():
            supa_conn.close()

if __name__ == '__main__':
    migrate()
