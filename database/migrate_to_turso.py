import sqlite3
import os

try:
    import libsql_experimental
except ImportError:
    print("Harap install libsql-experimental terlebih dahulu:")
    print("pip install libsql-experimental")
    exit(1)

# Ganti dengan URL dan Token Turso Anda
TURSO_DB_URL = os.environ.get('TURSO_DATABASE_URL', 'libsql://<NAMA-DB>-<USERNAME>.turso.io')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '<TOKEN_ANDA>')
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
        print(f"Ditemukan {len(movies)} baris di tabel movie_analysis.")
    except Exception as e:
        print(f"Gagal membaca tabel movie_analysis: {e}")
        movies = []

    if not movies:
        print("Tidak ada data untuk dimigrasikan.")
        return

    print("Menghubungkan ke Turso...")
    try:
        turso_conn = libsql_experimental.connect(TURSO_DB_URL, auth_token=TURSO_AUTH_TOKEN)
        turso_cursor = turso_conn.cursor()
        
        # Buat tabel jika belum ada (sekadar jaga-jaga)
        turso_cursor.execute('''
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
                turso_cursor.execute('''
                    INSERT OR REPLACE INTO movie_analysis (id_title, result_data, created_at)
                    VALUES (?, ?, ?)
                ''', (id_title, result_data, created_at))
                success_count += 1
            except Exception as e:
                print(f"Gagal migrasi data {id_title}: {e}")
        
        turso_conn.commit()
        print(f"Migrasi selesai! Berhasil memindahkan {success_count}/{len(movies)} baris ke Turso.")
        
    except Exception as e:
        print(f"Gagal terhubung ke Turso atau mengeksekusi query: {e}")

if __name__ == '__main__':
    migrate()
