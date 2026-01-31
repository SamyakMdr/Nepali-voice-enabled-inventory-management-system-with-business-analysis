import psycopg2
from sqlalchemy import create_engine
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Base

# 1. Connect directly and DROP the broken table
try:
    # Extract connection info from the URL for raw psycopg2 connection
    # URL format: postgresql://postgres:admin@localhost:5434/nepali_inventory
    print("🧨 Connecting to database to destroy old 'users' table...")
    
    # Simple parsing (assuming standard format you used)
    # You can also just hardcode these if the parsing fails
    DB_NAME = "nepali_inventory"
    DB_USER = "postgres"
    DB_PASS = "admin"
    DB_HOST = "localhost"
    DB_PORT = "5434"

    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()

    # THE NUCLEAR COMMAND
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    print("💥 Table 'users' has been dropped!")
    
    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error dropping table: {e}")

# 2. Use SQLAlchemy to Re-Create it properly
print("🏗️  Re-building tables with new schema...")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(bind=engine)
print("✅ SUCCESS! New 'users' table created with 'password' column.")