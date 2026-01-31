from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

# --- PRODUCT SCHEMAS ---
class ProductBase(BaseModel):
    name_english: str
    name_nepali: str
    quantity: float
    unit: str
    
    # ✅ Added Prices here so Frontend can see them
    cost_price: float = 0.0
    selling_price: float = 0.0

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    class Config:
        from_attributes = True

# --- SALES DASHBOARD SCHEMAS (New) ---

# For the "Profit/Revenue" Cards
class SalesStats(BaseModel):
    period: str
    total_revenue: float
    total_profit: float
    sales_count: int

# For the "Item Lists" (History)
class SaleItem(BaseModel):
    id: int
    item_name: str
    quantity: float
    total_amount: float
    timestamp: datetime
    
    class Config:
        from_attributes = True
        
        
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

# What the App sends to LOGIN
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# What the API sends back (Notice: NO password here!)
class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True