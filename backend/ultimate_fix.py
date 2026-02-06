import psycopg2

# Settings from your docker-compose
DB_CONFIG = {
    "dbname": "nepali_inventory",
    "user": "postgres",
    "password": "admin",
    "host": "localhost",
    "port": "5432" # Your Docker port
}

print("🔧 Connecting to Database...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    # 1. DROP the table
    print("🧨 Dropping 'users' table...")
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")

    # 2. CREATE the table manually (to be 100% sure)
    print("🏗️  Creating 'users' table manually...")
    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            email VARCHAR UNIQUE,
            password VARCHAR,
            ix_users_name VARCHAR,
            ix_users_email VARCHAR
        );
    """)
    
    # 3. VERIFY it
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users';")
    columns = [row[0] for row in cur.fetchall()]
    
    print(f"✅ Table created with columns: {columns}")
    
    if "password" in columns:
        print("🎉 SUCCESS! The 'password' column exists.")
    else:
        print("❌ FAILURE! Something went wrong.")

    conn.close()

except Exception as e:
    print(f"❌ Connection Error: {e}")