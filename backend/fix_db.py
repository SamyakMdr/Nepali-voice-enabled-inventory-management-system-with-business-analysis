import psycopg2
import os

DB_NAME = "nepali_inventory"
DB_USER = "postgres"
DB_PASS = "admin"
DB_HOST = "localhost"
<<<<<<< HEAD
DB_PORT = "5434"
=======
DB_PORT = "5432"
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457

try:
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()

    print("🗑️  Dropping the 'users' table...")
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    
    print("✅ Table dropped! Restart your server to recreate it correctly.")
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")