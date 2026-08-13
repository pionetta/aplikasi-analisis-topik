import sys, os
os.environ['TURSO_DATABASE_URL'] = 'libsql://analisis-topik-altabell.aws-ap-northeast-1.turso.io'
os.environ['TURSO_AUTH_TOKEN'] = 'eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODY2NTc5MjcsImlkIjoiMDE5ZmZkMWMtNTcwMS03N2IwLTlhNmQtYTQxYTJmNjE3ODEwIiwia2lkIjoiRklueXZyV0VpRk9HZ3lnSXJpcG10eW5admJZdUtwQWlzcUx2dDlaSC1yYyIsInJpZCI6IjJmYWEyZWVlLWQ3M2EtNGYwNi1hY2ViLTM4M2FjMWJmYTEzOSJ9.7RsQS8C6z0ZdohkSLjmm4TChAGGesCjdQtMSVUK_8rwIEsd64yyS0i8BPxjTc-rxWzlxL_dv9YLBwqsOenKdCw'

sys.path.insert(0, os.getcwd())
import services.db_service as db
print(f"IS_TURSO: {db.IS_TURSO}")
print("GET ALL...")
rows = db.get_all_movie_analysis()
print(f'Total rows in Turso: {len(rows)}')
