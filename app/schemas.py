from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Product Schemas
class ProductBase(BaseModel):
    name_english: str
    name_nepali: str
    quantity: float
    unit: str

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    class Config:
        from_attributes = True