from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# --- USER MODEL ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

# --- PRODUCT MODEL ---
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name_english = Column(String, index=True) 
    name_nepali = Column(String, unique=True, index=True) 
    
    quantity = Column(Float, default=0.0)
    unit = Column(String, default="kg")
    
    # Prices
    cost_price = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    
    # Relationship
    transactions = relationship("Transaction", back_populates="product")

# --- TRANSACTION MODEL ---
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    change_amount = Column(Float)      # e.g., -2.0 for selling 2kg
    transaction_type = Column(String)  # "SALE" or "PURCHASE"
    
    # Crucial for revenue reports
    total_value = Column(Float, default=0.0) 
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    product = relationship("Product", back_populates="transactions")