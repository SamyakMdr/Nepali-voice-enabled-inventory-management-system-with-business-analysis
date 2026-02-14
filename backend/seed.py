import sys
import os

# Fix import path so 'app' module is found properly
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine, Base
from app.models import Product

# 1. Create the tables if they don't exist
print("🔨 Checking tables...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# 2. List of items
initial_items = [
    {"name_english": "Rice",    "name_nepali": "चामल", "unit": "kg",     "cp": 80.0,  "sp": 100.0},
    {"name_english": "Lentils", "name_nepali": "दाल",  "unit": "kg",     "cp": 120.0, "sp": 150.0},
    {"name_english": "Oil",     "name_nepali": "तेल",  "unit": "liter",  "cp": 200.0, "sp": 240.0},
    {"name_english": "Sugar",   "name_nepali": "चिनी", "unit": "kg",     "cp": 90.0,  "sp": 110.0},
    {"name_english": "Salt",    "name_nepali": "नुन",  "unit": "packet", "cp": 20.0,  "sp": 25.0},
    # ✅ ADDED EGG
    {"name_english": "Egg",     "name_nepali": "अण्डा", "unit": "piece",  "cp": 15.0,  "sp": 20.0},
]

print("🌱 Seeding Database with Prices...")

for item in initial_items:
    existing = db.query(Product).filter(Product.name_nepali == item["name_nepali"]).first()
    
    if not existing:
        new_product = Product(
            name_english=item["name_english"],
            name_nepali=item["name_nepali"],
            quantity=100.0,            
            unit=item["unit"],
            cost_price=item["cp"],     
            selling_price=item["sp"]   
        )
        db.add(new_product)
        print(f"✅ Created {item['name_english']}")
    else:
        existing.cost_price = item["cp"]
        existing.selling_price = item["sp"]
        print(f"🔄 Updated {item['name_english']}")

db.commit()
db.close()
print("🎉 Database Ready!")