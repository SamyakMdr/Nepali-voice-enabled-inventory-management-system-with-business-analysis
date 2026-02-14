import sys
import os

# Fix import path so 'app' module is found properly
<<<<<<< HEAD
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine, Base
from app.models import Product
=======
# This allows you to run 'python backend/seed.py' from the main project folder
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine
from app.models import Base, Product
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457

# 1. Create the tables if they don't exist
print("🔨 Checking tables...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()

<<<<<<< HEAD
# 2. List of items
initial_items = [
    # --- EXISTING ITEMS ---
=======
# 2. List of items with CP (Buying Price) and SP (Selling Price)
initial_items = [
    # Format: English Name, Nepali Name, Unit, Cost Price, Selling Price
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
    {"name_english": "Rice",    "name_nepali": "चामल", "unit": "kg",     "cp": 80.0,  "sp": 100.0},
    {"name_english": "Lentils", "name_nepali": "दाल",  "unit": "kg",     "cp": 120.0, "sp": 150.0},
    {"name_english": "Oil",     "name_nepali": "तेल",  "unit": "liter",  "cp": 200.0, "sp": 240.0},
    {"name_english": "Sugar",   "name_nepali": "चिनी", "unit": "kg",     "cp": 90.0,  "sp": 110.0},
    {"name_english": "Salt",    "name_nepali": "नुन",  "unit": "packet", "cp": 20.0,  "sp": 25.0},
<<<<<<< HEAD
    {"name_english": "Egg",     "name_nepali": "अण्डा", "unit": "piece",  "cp": 15.0,  "sp": 20.0},

    # --- ✅ NEW ITEMS ADDED ---
    {"name_english": "Chiura",  "name_nepali": "चिउरा", "unit": "kg",     "cp": 110.0, "sp": 140.0},
    {"name_english": "Maida",   "name_nepali": "मैदा",  "unit": "kg",     "cp": 60.0,  "sp": 80.0},
    {"name_english": "Turmeric", "name_nepali": "बेसार", "unit": "kg",    "cp": 300.0, "sp": 400.0},
    {"name_english": "Biscuit", "name_nepali": "बिस्कुट", "unit": "packet", "cp": 15.0,  "sp": 20.0},
=======
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
]

print("🌱 Seeding Database with Prices...")

for item in initial_items:
    # Check if exists (Matching by Nepali Name)
    existing = db.query(Product).filter(Product.name_nepali == item["name_nepali"]).first()
    
    if not existing:
        new_product = Product(
            name_english=item["name_english"],
            name_nepali=item["name_nepali"],
<<<<<<< HEAD
            quantity=100.0,            # Start with 100 units default
=======
            quantity=10.0,             # Start with 10 KG stock default
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
            unit=item["unit"],
            cost_price=item["cp"],     # Buying Price
            selling_price=item["sp"]   # Selling Price
        )
        db.add(new_product)
<<<<<<< HEAD
        print(f"✅ Created {item['name_english']} ({item['name_nepali']})")
=======
        print(f"✅ Created {item['name_english']} ({item['name_nepali']}): CP={item['cp']}, SP={item['sp']}")
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
    else:
        # If it exists, UPDATE the prices
        existing.cost_price = item["cp"]
        existing.selling_price = item["sp"]
<<<<<<< HEAD
        print(f"🔄 Updated {item['name_english']} prices.")

db.commit()
db.close()
print("🎉 Database Ready! New items added.")
=======
        # Optional: Reset stock to 10 for testing
        existing.quantity = 10.0 
        print(f"🔄 Updated {item['name_english']}: Prices set to CP={item['cp']}, SP={item['sp']}")

db.commit()
db.close()
print("🎉 Database Ready! Prices are set.")
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
