from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Product, Transaction
from pydantic import BaseModel
import re

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory & Voice"]
)

class VoiceCommand(BaseModel):
    command: str

@router.post("/voice-command")
def process_voice(data: VoiceCommand, db: Session = Depends(get_db)):
    text = data.command.lower()
    
    # Logic: "Sell 2 packet Biscuit" or "Sell 1 kg Chiura"
    # Regex captures:
    # Group 1: Quantity (digits)
    # Group 2: Unit (kg, liter, packet, etc.) - Optional
    # Group 3: Item Name
    match = re.search(r"(\d+)\s*(kg|liter|packet|piece|pieces)?\s*(\w+)", text)
    
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
            return {"error": f"Not enough stock! You only have {product.quantity} {product.unit}."}
            
        # Calculate Total Price
        total_price = qty * product.selling_price
        
        # Create Transaction
        new_transaction = Transaction(
            product_id=product.id,
            change_amount=-qty,
            transaction_type="SALE",
            total_value=total_price  
        )
        
        # Update Stock
        product.quantity -= qty
        
        db.add(new_transaction)
        db.commit()
        
        return {
            "message": f"Sold {qty} {product.unit} of {product.name_english} ({product.name_nepali})",
            "total_price": total_price,
            "remaining_stock": product.quantity
        }

    return {"message": "Command not understood. Try 'Sell 2 packet Biscuit'"}

@router.get("/reports")
def generate_report(db: Session = Depends(get_db)):
    # Calculate Total Sales Revenue
    total_sales = db.query(func.sum(Transaction.total_value))\
        .filter(Transaction.transaction_type == "SALE").scalar() or 0.0
        
    # Get recent transactions
    history = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(10).all()
    
    return {
        "total_revenue": total_sales,
        "recent_transactions": history
    }