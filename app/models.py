from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    # We store both names so the App looks good (English) but Voice works (Nepali)
    name_english = Column(String, index=True) 
    name_nepali = Column(String, unique=True, index=True) 
    
    quantity = Column(Float, default=0.0)
    unit = Column(String, default="kg")
    
    # Link to history
    transactions = relationship("Transaction", back_populates="product")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key links to the Product table
    product_id = Column(Integer, ForeignKey("products.id"))
    
    change_amount = Column(Float)      # +10 for add, -5 for sale
    transaction_type = Column(String)  # "PURCHASE" or "SALE"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="transactions")