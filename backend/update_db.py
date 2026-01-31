import sys
import os
from sqlalchemy import text

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.database import engine
except ModuleNotFoundError:
    # Fallback if running as a script and 'app' is a sibling directory
    import sys
    import os
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
    sys.path.insert(0, app_path)
    from database import engine

print("🛠  Adding Cost Price & Selling Price columns to 'products' table...")

with engine.connect() as connection:
    # 1. Start a transaction
    trans = connection.begin()
    try:
        # 2. Add 'cost_price' column if it doesn't exist
        connection.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_price FLOAT DEFAULT 0.0;"))
        
        # 3. Add 'selling_price' column if it doesn't exist
        connection.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS selling_price FLOAT DEFAULT 0.0;"))
        
        # 4. Add 'total_value' column to transactions (just in case you missed it)
        connection.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS total_value FLOAT DEFAULT 0.0;"))
        
        trans.commit()
        print("✅ Columns added successfully!")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Error: {e}")

print("🚀 Now you can run 'python seed.py'")