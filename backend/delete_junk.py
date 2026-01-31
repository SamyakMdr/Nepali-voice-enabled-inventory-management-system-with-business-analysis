import sys
import os

sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import Product, Transaction

db = SessionLocal()

# The junk name
junk_name = "ताल चिलो थबा"

print(f"🔍 Looking for '{junk_name}'...")
item = db.query(Product).filter(Product.name_nepali == junk_name).first()

if item:
    print(f"⚠️ Found item ID: {item.id}")
    
    # 1. DELETE TRANSACTIONS FIRST (The Fix)
    num_trans = db.query(Transaction).filter(Transaction.product_id == item.id).delete()
    print(f"🗑 Deleted {num_trans} history records linked to this item.")

    # 2. NOW DELETE THE ITEM
    db.delete(item)
    db.commit()
    print("✅ Junk item deleted successfully!")
else:
    print("❌ Item not found. Already deleted?")

db.close()