import psycopg2
import os

# --- SETTINGS (MATCHING YOUR DOCKER PS) ---
DB_NAME = "nepali_inventory"
DB_USER = "postgres"
DB_PASS = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"  # <--- Crucial! Your docker ps says 5434

print(f"🕵️‍♂️ Connecting to {DB_HOST}:{DB_PORT}...")

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    print("✅ SUCCESS! Python connected to Docker Database.")
    
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = cur.fetchall()
    
    print("\n📊 Tables found in database:")
    for t in tables:
        print(f" - {t[0]}")
        
    conn.close()

except Exception as e:
    print("\n❌ CONNECTION FAILED")
    print(f"Error: {e}")