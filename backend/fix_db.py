import sys
import os
from sqlalchemy import text

# --- FIX IMPORTS ---
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, "backend"))
sys.path.append(current_dir)

from app.database import engine

print("🛠  Fixing Database: Adding missing columns...")

with engine.connect() as connection:
    # We use a transaction to make sure changes are saved
    with connection.begin():
        print("1️⃣  Adding 'cost_price'...")
        connection.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_price FLOAT DEFAULT 0.0;"))
        
        print("2️⃣  Adding 'selling_price'...")
        connection.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS selling_price FLOAT DEFAULT 0.0;"))
        
        print("3️⃣  Adding 'total_value' to transactions...")
        connection.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS total_value FLOAT DEFAULT 0.0;"))

print("✅ Database successfully updated! Now you can run seed.py.")