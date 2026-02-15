from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from passlib.context import CryptContext

# 1. Setup Database Base
Base = declarative_base()

# 2. Setup Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================================
# 🗄️ DATABASE TABLES
# ==========================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="staff")  # admin, staff

class Product(Base):
    __tablename__ = "inventory"  # This matches the SQL used in inventory.py

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # e.g., "chamal"
    name_english = Column(String, nullable=True)    # e.g., "Rice"
    quantity = Column(Float, default=0.0)
    unit = Column(String, default="kg")             # kg, ltr, packet
    cost_price = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    
    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="product")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("inventory.id"))
    transaction_type = Column(String)  # "PURCHASE" (Add) or "SALE" (Deduct)
    quantity = Column(Float)
    total_amount = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="transactions")

# ==========================================
# 🔐 MISSING PASSWORD FUNCTIONS (Added Here)
# ==========================================

def hash_password(password: str):
    """Hashes a plain text password."""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """Checks if a plain password matches the hash."""
    return pwd_context.verify(plain_password, hashed_password)