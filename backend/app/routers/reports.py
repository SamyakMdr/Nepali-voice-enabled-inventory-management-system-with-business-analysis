from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product, Transaction

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/generate")
def generate_inventory_report(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    
    report_data = []
    total_inventory_value = 0.0
    
    for p in products:
        # Calculate how much money is tied up in stock
        stock_value = p.quantity * p.cost_price
        total_inventory_value += stock_value
        
        report_data.append({
            "product": p.name_english,
            "nepali_name": p.name_nepali,
            "current_stock": p.quantity,
            "unit": p.unit,
            "stock_value": stock_value
        })
        
    return {
        "report_date": "Today",
        "total_inventory_value": total_inventory_value,
        "items": report_data
    }