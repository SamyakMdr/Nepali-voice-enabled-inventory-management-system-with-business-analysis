from app.database import SessionLocal, engine
from app.models import Base, Product

# 1. Create the tables if they don't exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# 2. List of items to add
initial_items = [
    {"name_english": "Rice", "name_nepali": "चामल", "unit": "kg"},
    {"name_english": "Lentils", "name_nepali": "दाल", "unit": "kg"},
    {"name_english": "Oil", "name_nepali": "तेल", "unit": "liter"},
    {"name_english": "Sugar", "name_nepali": "चिनी", "unit": "kg"},
    {"name_english": "Salt", "name_nepali": "नुन", "unit": "packet"},
]

print("🌱 Seeding Database...")

for item in initial_items:
    # Check if exists
    existing = db.query(Product).filter(Product.name_nepali == item["name_nepali"]).first()
    
    if not existing:
        new_product = Product(
            name_english=item["name_english"],
            name_nepali=item["name_nepali"],
            quantity=10.0,  # Starting with 10 KG
            unit=item["unit"]
        )
        db.add(new_product)
        print(f"✅ Added {item['name_english']} ({item['name_nepali']}) - 10 {item['unit']}")
    else:
        # Reset to 10 if it already exists
        existing.quantity = 10.0
        print(f"🔄 Reset {item['name_english']} to 10 {item['unit']}")

db.commit()
db.close()
print("🎉 Database Ready!")