import os
import uuid
import whisper
import torch
import difflib
from typing import List

from fastapi import FastAPI, File, UploadFile, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import engine, get_db
from . import models, schemas

# --- IMPORT ROUTERS ---
from .auth import router as auth_router       # Login/Register
from .routers import sales, reports           # Sales Stats & PDF Reports

# --- IMPORT BRAIN & NORMALIZER ---
# (Graceful fallback if these files don't exist yet)
try:
    from .brain import process_command_with_ai, normalize_nepali
except ImportError:
    def process_command_with_ai(text): return {"intent": "UNKNOWN", "item": None}
    def normalize_nepali(text): return text

# Create DB Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nepali Voice Inventory System")

# --- ACTIVATE ROUTERS ---
app.include_router(auth_router)     # ✅ Enables /auth/login & /auth/register
app.include_router(sales.router)    # ✅ Enables /sales/stats
app.include_router(reports.router)  # ✅ Enables /reports/generate

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

# --- SMART PHONETIC SEARCH (ACCENT PROOF) ---
def find_closest_product(db: Session, spoken_item: str):
    if not spoken_item:
        return None

    # 🚨 MANUAL CORRECTION MAP (The 'Accent' Dictionary)
    overrides = {
        # DAAL
        "ताल": "दाल", "टाल": "दाल", "थाल": "दाल", "दान": "दाल", "दाली": "दाल",
        # CHAMAL
        "जमाल": "चामल", "सामल": "चामल", "छामल": "चामल", "कामल": "चामल",
        # CHINI
        "चिनि": "चिनी", "छिनि": "चिनी", "सिनी": "चिनी", "चिन्दि": "चिनी",
        # TEL
        "टेल": "तेल", "टैल": "तेल", "पेल": "तेल", "तैल": "तेल",
        # NUN
        "नुन": "नुन", "नून": "नुन", "लुन": "नुन", "मुन": "नुन"
    }
    
    # 1. Apply Dictionary Fixes
    if spoken_item in overrides:
        print(f"🔧 Auto-Correction: '{spoken_item}' -> '{overrides[spoken_item]}'")
        spoken_item = overrides[spoken_item]

    all_products = db.query(models.Product).all()
    spoken_norm = normalize_nepali(spoken_item)

    best_match = None
    highest_score = 0.0

    for product in all_products:
        db_name = product.name_nepali
        db_norm = normalize_nepali(db_name)

        # 2. Exact & Substring Match
        if spoken_norm == db_norm: return product
        if db_norm in spoken_norm: return product

        # 3. Fuzzy Match
        score = difflib.SequenceMatcher(None, spoken_norm, db_norm).ratio()
        if score > highest_score:
            highest_score = score
            best_match = product

    if highest_score > 0.6:
        print(f"🔍 Fuzzy Match: '{spoken_item}' -> '{best_match.name_nepali}' ({highest_score:.2f})")
        return best_match
    
    return None

# --- CORE LOGIC (UPDATED WITH TOTALS & ALERTS) ---
def execute_inventory_logic(text: str, db: Session):
    print(f"🧠 AI Thinking on: '{text}'...")

    ai_data = process_command_with_ai(text)
    
    intent = ai_data.get("intent")
    raw_item = ai_data.get("item")
    qty = float(ai_data.get("quantity", 1))
    unit = ai_data.get("unit", "kg")
    customer = ai_data.get("customer")

    # Use Smart Finder
    product = find_closest_product(db, raw_item)
    
    item_display = product.name_nepali if product else raw_item
    qty_display = convert_to_nepali_num(qty)

    # Handle Not Found
    if not product:
        if intent == "CHECK":
             return {"intent": intent, "response": "❌ यो सामान स्टकमा भेटिएन।"}
        return {"intent": intent, "response": f"❌ '{raw_item}' बुझिन। (दाल, चामल, चिनी, तेल, नुन मात्र उपलब्ध छ)"}

    # --- ADD LOGIC ---
    if intent == "ADD":
        product.quantity += qty
        
        # Calculate Total Cost
        total_cost = qty * product.cost_price
        
        trans = models.Transaction(
            product_id=product.id, 
            change_amount=qty, 
            transaction_type="PURCHASE",
            total_value=total_cost
        )
        db.add(trans)
        db.commit()
        
        # New Totals
        new_total_qty = convert_to_nepali_num(product.quantity)
        cost_nepali = convert_to_nepali_num(total_cost)
        
        return {
            "intent": intent, 
            "item": item_display,
            "response": f"✅ {item_display} {qty_display} {product.unit} थपियो। (जम्मा: {new_total_qty} {product.unit})"
        }

    # --- SALE LOGIC ---
    if intent == "SALE":
        if product.quantity < qty:
            rem_qty = convert_to_nepali_num(product.quantity)
            return {"intent": intent, "response": f"❌ {item_display} को स्टक पर्याप्त छैन। (बाँकी: {rem_qty} {product.unit})"}
        
        product.quantity -= qty
        
        # Calculate Total Revenue
        total_revenue = qty * product.selling_price
        
        trans = models.Transaction(
            product_id=product.id, 
            change_amount=-qty, 
            transaction_type="SALE",
            total_value=total_revenue
        )
        db.add(trans)
        db.commit()
        
        # Totals & Alerts
        rem = convert_to_nepali_num(product.quantity)
        revenue_nepali = convert_to_nepali_num(total_revenue)
        
        # Low Stock Alert Logic (< 5)
        alert_msg = " ⚠️ चेतावनी: स्टक कम भयो!" if product.quantity <= 5.0 else ""
        
        action_text = f"{customer} लाई बेचियो" if customer else "बिक्री भयो"

        return {
            "intent": intent, 
            "item": item_display,
            "response": f"✅ {item_display} {qty_display} {product.unit} {action_text}। जम्मा: रु {revenue_nepali}। (बाँकी: {rem} {product.unit}){alert_msg}"
        }

    # --- CHECK LOGIC ---
    if intent == "CHECK":
        total = convert_to_nepali_num(product.quantity)
        sp_nepali = convert_to_nepali_num(product.selling_price)
        
        # Low Stock Alert Logic (< 5)
        alert_msg = " ⚠️ चेतावनी: स्टक कम भयो!" if product.quantity <= 5.0 else ""
        
        return {
            "intent": intent, 
            "response": f"📦 {item_display}: {total} {product.unit}। (मूल्य: रु {sp_nepali}/kg){alert_msg}"
        }

    return {"intent": "UNKNOWN", "response": "❌ मैले आदेश बुझिन।"}

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "SmartBiz AI System is Online 🚀"}

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

        hint = "सामानहरु: चामल, दाल, तेल, चिनी, नुन, साबुन"
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