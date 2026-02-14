import sys
import os

# Get the current folder
current_dir = os.getcwd()

# 1. Add 'backend' to the path so Python finds 'app' inside it
sys.path.append(os.path.join(current_dir, "backend"))

# 2. Also keep the current directory just in case
sys.path.append(current_dir)

from app.database import SessionLocal, engine
from app import models

# 1. Create Tables (if new columns were added)
print("🛠Checking Database Tables...")
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

# 2. Define Prices [Cost Price (Buy), Selling Price (Sell)]
prices = {
    "दाल": [120, 150],   # Buy @ 120, Sell @ 150
    "चामल": [80, 100],   # Buy @ 80, Sell @ 100
    "चिनी": [90, 110],   # Buy @ 90, Sell @ 110
    "तेल": [200, 240],   # Buy @ 200, Sell @ 240
    "नुन": [20, 25]      # Buy @ 20, Sell @ 25
}

print("🔄 Updating Prices...")

for name, (cp, sp) in prices.items():
    # Find the product by its Nepali name
    product = db.query(models.Product).filter(models.Product.name_nepali == name).first()
    
    if product:
        product.cost_price = cp
        product.selling_price = sp
        print(f"✅ {name}: Set CP={cp}, SP={sp}")
    else:
        print(f"❌ {name} not found in DB! (Add it via voice first: 'Add 10kg {name}')")

db.commit()
db.close()
print("🎉 Prices Set Successfully!")