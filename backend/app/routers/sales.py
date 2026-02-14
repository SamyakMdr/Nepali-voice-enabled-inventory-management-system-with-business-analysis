from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Transaction, Product

router = APIRouter(
    prefix="/sales",
    tags=["Sales Dashboard"]
)

@router.get("/stats")
def get_sales_stats(db: Session = Depends(get_db)):
    # 1. Total Revenue (Sum of all SALES)
    total_revenue = db.query(func.sum(Transaction.total_value))\
        .filter(Transaction.transaction_type == "SALE").scalar() or 0.0

    # 2. Total Items Sold
    total_items_sold = db.query(func.count(Transaction.id))\
        .filter(Transaction.transaction_type == "SALE").scalar() or 0

    # 3. Low Stock Items (Less than 5 kg)
    low_stock = db.query(func.count(Product.id))\
        .filter(Product.quantity < 5).scalar() or 0

    return {
        "total_revenue": total_revenue,
        "total_sales_count": total_items_sold,
        "low_stock_alerts": low_stock
    }

@router.get("/history")
def get_sales_history(db: Session = Depends(get_db)):
    # Get last 10 transactions
    history = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(10).all()
    return history