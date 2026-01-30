import os
import uuid
import whisper
import torch
import difflib
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import engine, get_db
from . import models, schemas

# --- IMPORT BRAIN & NORMALIZER ---
try:
    from .brain import process_command_with_ai, normalize_nepali
except ImportError:
    def process_command_with_ai(text): return {"intent": "UNKNOWN", "item": None}
    def normalize_nepali(text): return text

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

# --- SMART PHONETIC SEARCH (ACCENT PROOF) ---
def find_closest_product(db: Session, spoken_item: str):
    if not spoken_item:
        return None

    # 🚨 MANUAL CORRECTION MAP (The 'Accent' Dictionary)
    # Maps WRONG inputs -> CORRECT Database Names
    overrides = {
        # DAAL (Lentils) - Fixes "Taal", "Thaal"
        "ताल": "दाल", "टाल": "दाल", "थाल": "दाल", "दान": "दाल", "दाली": "दाल",
        
        # CHAMAL (Rice)
        "जमाल": "चामल", "सामल": "चामल", "छामल": "चामल", "कामल": "चामल",
        
        # CHINI (Sugar)
        "चिनि": "चिनी", "छिनि": "चिनी", "सिनी": "चिनी", "चिन्दि": "चिनी",
        
        # TEL (Oil)
        "टेल": "तेल", "टैल": "तेल", "पेल": "तेल", "तैल": "तेल",
        
        # NUN (Salt)
        "नुन": "नुन", "नून": "नुन", "लुन": "नुन", "मुन": "नुन"
    }
    
    # 1. Apply Dictionary Fixes First
    if spoken_item in overrides:
        print(f"🔧 Auto-Correction: '{spoken_item}' -> '{overrides[spoken_item]}'")
        spoken_item = overrides[spoken_item]

    # Get valid products
    all_products = db.query(models.Product).all()
    spoken_norm = normalize_nepali(spoken_item)

    best_match = None
    highest_score = 0.0

    for product in all_products:
        db_name = product.name_nepali
        db_norm = normalize_nepali(db_name)

        # 2. Exact Match
        if spoken_norm == db_norm:
            return product
        
        # 3. Substring Match
        if db_norm in spoken_norm:
            return product

        # 4. Fuzzy Similarity
        score = difflib.SequenceMatcher(None, spoken_norm, db_norm).ratio()
        if score > highest_score:
            highest_score = score
            best_match = product

    # Only accept fuzzy match if score > 60%
    if highest_score > 0.6:
        print(f"🔍 Fuzzy Match Found: '{spoken_item}' -> '{best_match.name_nepali}' (Score: {highest_score:.2f})")
        return best_match
    
    return None

# --- CORE LOGIC ---
def execute_inventory_logic(text: str, db: Session):
    print(f"🧠 AI Thinking on: '{text}'...")

    ai_data = process_command_with_ai(text)
    
    intent = ai_data.get("intent")
    raw_item = ai_data.get("item")
    qty = float(ai_data.get("quantity", 1))
    unit = ai_data.get("unit", "kg")
    customer = ai_data.get("customer")

    # Use the Smart Finder
    product = find_closest_product(db, raw_item)
    
    item_display = product.name_nepali if product else raw_item
    qty_display = convert_to_nepali_num(qty)

    # Handle Not Found
    if not product:
        if intent == "CHECK":
             return {"intent": intent, "response": "❌ यो सामान स्टकमा भेटिएन।"}
        
        # STRICT MODE: If we can't find it in the Dictionary or Fuzzy Match, reject it.
        # This prevents creating junk items like "Taal".
        return {"intent": intent, "response": f"❌ '{raw_item}' बुझिन। (दाल, चामल, चिनी, तेल, नुन मात्र उपलब्ध छ)"}

    # --- ADD LOGIC ---
    if intent == "ADD":
        product.quantity += qty
        
        trans = models.Transaction(product_id=product.id, change_amount=qty, transaction_type="PURCHASE")
        db.add(trans)
        db.commit()
        
        total = convert_to_nepali_num(product.quantity)
        return {
            "intent": intent, 
            "item": item_display,
            "response": f"✅ {item_display} {qty_display} {product.unit} थपियो। जम्मा: {total}"
        }

    # --- SALE LOGIC ---
    if intent == "SALE":
        if product.quantity < qty:
            return {"intent": intent, "response": f"❌ {item_display} को स्टक पर्याप्त छैन।"}
        
        product.quantity -= qty
        
        trans = models.Transaction(product_id=product.id, change_amount=-qty, transaction_type="SALE")
        db.add(trans)
        db.commit()
        
        rem = convert_to_nepali_num(product.quantity)
        
        # Alert on Sale
        alert_msg = " ⚠️ चेतावनी: स्टक कम भयो!" if product.quantity <= 5 else ""
        action_text = f"{customer} लाई बेचियो" if customer else "घटाइयो"

        return {
            "intent": intent, 
            "item": item_display,
            "response": f"✅ {item_display} {qty_display} {product.unit} {action_text}। बाँकी: {rem}।{alert_msg}"
        }

    # --- CHECK LOGIC ---
    if intent == "CHECK":
        total = convert_to_nepali_num(product.quantity)
        
        # Alert on Check
        alert_msg = " ⚠️ चेतावनी: स्टक कम भयो!" if product.quantity <= 5 else ""
        
        return {
            "intent": intent, 
            "response": f"📦 {item_display} गोदाममा {total} {product.unit} छ।{alert_msg}"
        }

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

        # Updated Hint
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

@app.get("/sales/daily")
def daily_sales(db: Session = Depends(get_db)):
    today = datetime.now().date()
    sales = db.query(models.Transaction).filter(
        models.Transaction.transaction_type == "SALE",
        func.date(models.Transaction.timestamp) >= today
    ).all()
    return {"date": str(today), "total_sales_count": len(sales), "transactions": sales}