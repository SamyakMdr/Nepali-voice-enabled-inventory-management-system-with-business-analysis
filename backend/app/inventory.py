from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
<<<<<<< HEAD
from app.database import get_db
from app.models import Product, Transaction
=======
from .database import get_db
from .models import Product, Transaction
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
from pydantic import BaseModel
import re

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory & Voice"]
)

<<<<<<< HEAD
class VoiceCommand(BaseModel):
    command: str

=======
# Schema for Voice Command Input
class VoiceCommand(BaseModel):
    command: str

# 1. 🎤 VOICE PROCESSING API
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
@router.post("/voice-command")
def process_voice(data: VoiceCommand, db: Session = Depends(get_db)):
    text = data.command.lower()
    
<<<<<<< HEAD
    # Logic: "Sell 2 packet Biscuit" or "Sell 1 kg Chiura"
    # Regex captures:
    # Group 1: Quantity (digits)
    # Group 2: Unit (kg, liter, packet, etc.) - Optional
    # Group 3: Item Name
    match = re.search(r"(\d+)\s*(kg|liter|packet|piece|pieces)?\s*(\w+)", text)
=======
    # Logic: "Sell 2 kg Rice"
    # Regex to find number and item
    match = re.search(r"(\d+)\s*(kg|liter|packet)?\s*(\w+)", text)
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
    
    if "sell" in text and match:
        qty = float(match.group(1))
        item_name = match.group(3)
        
        # Find product (English or Nepali)
        product = db.query(Product).filter(
            (func.lower(Product.name_english) == item_name) | 
            (Product.name_nepali == item_name)
        ).first()
        
        if not product:
            return {"error": f"Product '{item_name}' not found."}
        
        if product.quantity < qty:
<<<<<<< HEAD
            return {"error": f"Not enough stock! You only have {product.quantity} {product.unit}."}
=======
            return {"error": "Not enough stock!"}
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
            
        # Calculate Total Price
        total_price = qty * product.selling_price
        
<<<<<<< HEAD
        # Create Transaction
=======
        # ✅ Create Transaction (Now 'total_value' will work!)
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
        new_transaction = Transaction(
            product_id=product.id,
            change_amount=-qty,
            transaction_type="SALE",
<<<<<<< HEAD
            total_value=total_price  
=======
            total_value=total_price  # <--- This caused your error before
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
        )
        
        # Update Stock
        product.quantity -= qty
        
        db.add(new_transaction)
        db.commit()
        
        return {
<<<<<<< HEAD
            "message": f"Sold {qty} {product.unit} of {product.name_english} ({product.name_nepali})",
=======
            "message": f"Sold {qty} {product.unit} of {product.name_english}",
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
            "total_price": total_price,
            "remaining_stock": product.quantity
        }

<<<<<<< HEAD
    return {"message": "Command not understood. Try 'Sell 2 packet Biscuit'"}

@router.get("/reports")
def generate_report(db: Session = Depends(get_db)):
    # Calculate Total Sales Revenue
=======
    return {"message": "Command not understood. Try 'Sell 2 kg Rice'"}

# 2. 📊 REPORT GENERATION API
@router.get("/reports")
def generate_report(db: Session = Depends(get_db)):
    # Calculate Total Sales
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
    total_sales = db.query(func.sum(Transaction.total_value))\
        .filter(Transaction.transaction_type == "SALE").scalar() or 0.0
        
    # Get recent transactions
<<<<<<< HEAD
    history = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(10).all()
=======
    history = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(5).all()
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
    
    return {
        "total_revenue": total_sales,
        "recent_transactions": history
    }