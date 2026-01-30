import os
import uuid
import whisper
import torch
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

# --- DATABASE IMPORTS ---
from .database import engine, get_db
from . import models, schemas

# --- OFFLINE BRAIN IMPORT ---
try:
    from .brain import process_command_with_ai
except ImportError:
    # Fallback in case brain.py is missing
    def process_command_with_ai(text):
        return {"intent": "UNKNOWN", "item": None}

# Create Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nepali Voice Inventory System")

# --- WHISPER SETUP ---
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Loading Whisper model on {device}...")
model = whisper.load_model("small", device=device)

UPLOAD_DIR = "temp_storage"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class Command(BaseModel):
    text: str

# --- HELPER: NUMBER CONVERSION ---
def convert_to_nepali_num(number: float) -> str:
    if number is None: return "०"
    if number % 1 == 0: number = int(number)
    eng_to_nep = str.maketrans("0123456789", "०१२३४५६७८९")
    return str(number).translate(eng_to_nep)

# --- CORE LOGIC (Text & Voice) ---
def execute_inventory_logic(text: str, db: Session):
    print(f"🧠 AI Thinking on: '{text}'...")

    ai_data = process_command_with_ai(text)
    
    intent = ai_data.get("intent")
    item = ai_data.get("item") # Nepali name from Brain
    qty = float(ai_data.get("quantity", 1))
    unit = ai_data.get("unit", "kg")
    customer = ai_data.get("customer")

    # 1. Spelling Correction (Fixes Whisper errors)
    corrections = {
        "चिनि": "चिनी",
        "टेल": "तेल",
        "नुन": "नुन"
    }
    if item in corrections:
        item = corrections[item]

    if not item:
        return {"intent": intent, "response": "❌ माफ गर्नुहोला, मैले सामानको नाम बुझिन।"}

    # 2. Database Lookup
    product = db.query(models.Product).filter(models.Product.name_nepali == item).first()
    qty_display = convert_to_nepali_num(qty)

    # --- ADD LOGIC ---
    if intent == "ADD":
        if product:
            product.quantity += qty
        else:
            product = models.Product(name_nepali=item, name_english=item, quantity=qty, unit=unit)
            db.add(product)
        
        db.flush()
        # Log Transaction
        trans = models.Transaction(product_id=product.id, change_amount=qty, transaction_type="PURCHASE")
        db.add(trans)
        db.commit()
        
        total = convert_to_nepali_num(product.quantity)
        return {
            "intent": intent, 
            "item": item,
            "response": f"✅ {item} {qty_display} {unit} थपियो। जम्मा: {total}"
        }

    # --- SALE LOGIC (With Low Stock Alert) ---
    if intent == "SALE":
        if not product or product.quantity < qty:
            return {"intent": intent, "response": f"❌ {item} को स्टक पर्याप्त छैन।"}
        
        product.quantity -= qty
        
        # Log Transaction
        trans = models.Transaction(product_id=product.id, change_amount=-qty, transaction_type="SALE")
        db.add(trans)
        db.commit()
        
        rem = convert_to_nepali_num(product.quantity)
        
        # 🚨 ALERT LOGIC
        alert_msg = ""
        if product.quantity <= 5:
            alert_msg = " ⚠️ चेतावनी: स्टक कम भयो!"

        action_text = f"{customer} लाई बेचियो" if customer else "घटाइयो"

        return {
            "intent": intent, 
            "item": item,
            "response": f"✅ {item} {qty_display} {unit} {action_text}। बाँकी: {rem}।{alert_msg}"
        }

    # --- CHECK LOGIC ---
    if intent == "CHECK":
        if product:
            total = convert_to_nepali_num(product.quantity)
            return {"intent": intent, "response": f"📦 {item} गोदाममा {total} {product.unit} छ।"}
        return {"intent": intent, "response": f"❌ {item} स्टकमा छैन।"}

    return {"intent": "UNKNOWN", "response": "❌ मैले आदेश बुझिन।"}

# --- ENDPOINTS ---

@app.post("/command")
def process_command(cmd: Command, db: Session = Depends(get_db)):
    return execute_inventory_logic(cmd.text, db)

@app.post("/voice")
async def process_voice_command(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        filename = f"{uuid.uuid4()}.wav"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(await file.read())

        # Updated Hint for better accuracy
        hint = "सामानहरु: चामल, दाल, तेल, चिनी, नुन, साबुन, कटाऊ, थप, बेच"
        result = model.transcribe(filepath, language="ne", fp16=False, initial_prompt=hint)
        
        if os.path.exists(filepath): os.remove(filepath)

        text = result["text"].strip()
        print(f"🎤 Heard: '{text}'")

        result_data = execute_inventory_logic(text, db)
        result_data["transcription"] = text
        return result_data

    except Exception as e:
        return {"error": str(e)}

@app.get("/products", response_model=List[schemas.ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@app.get("/sales/daily")
def daily_sales(db: Session = Depends(get_db)):
    today = datetime.now().date()
    sales = db.query(models.Transaction).filter(
        models.Transaction.transaction_type == "SALE",
        func.date(models.Transaction.timestamp) >= today
    ).all()
    return {"date": str(today), "total_sales_count": len(sales), "transactions": sales}