import os
import uuid
import whisper
import torch
import difflib
from typing import List

from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import engine, get_db
from . import models, schemas

# --- IMPORT ROUTERS ---
from .auth import router as auth_router       # Login/Register
from .routers import sales, reports           # Sales Stats & PDF Reports

# --- IMPORT BRAIN & NORMALIZER ---
try:
    from .brain import process_command_with_ai, normalize_nepali
except ImportError:
    def process_command_with_ai(text): return {"intent": "UNKNOWN", "item": None}
    def normalize_nepali(text): return text

# Create DB Tables
models.Base.metadata.create_all(bind=engine)

# ✅ THIS LINE IS CRITICAL (The error happens if this is missing)
app = FastAPI(title="Nepali Voice Inventory System")

# --- ENABLE CORS (Fixes "Failed to Fetch") ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ACTIVATE ROUTERS ---
app.include_router(auth_router)
app.include_router(sales.router)
app.include_router(reports.router)

# --- WHISPER SETUP ---
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Loading Whisper model on {device}...")
try:
    model = whisper.load_model("small", device=device)
except Exception as e:
    print(f"⚠️ Whisper load failed: {e}")
    model = None

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
    if not spoken_item: return None
    overrides = {
        "ताल": "दाल", "टाल": "दाल", "थाल": "दाल", "दान": "दाल",
        "जमाल": "चामल", "सामल": "चामल", "छामल": "चामल",
        "चिनि": "चिनी", "छिनि": "चिनी", "सिनी": "चिनी",
        "टेल": "तेल", "टैल": "तेल", "पेल": "तेल",
        "नुन": "नुन", "नून": "नुन", "लुन": "नुन"
    }
    if spoken_item in overrides: spoken_item = overrides[spoken_item]

    all_products = db.query(models.Product).all()
    spoken_norm = normalize_nepali(spoken_item)
    best_match = None
    highest_score = 0.0

    for product in all_products:
        db_norm = normalize_nepali(product.name_nepali)
        if spoken_norm == db_norm: return product
        if db_norm in spoken_norm: return product
        score = difflib.SequenceMatcher(None, spoken_norm, db_norm).ratio()
        if score > highest_score:
            highest_score = score
            best_match = product

    return best_match if highest_score > 0.6 else None

# --- CORE LOGIC ---
def execute_inventory_logic(text: str, db: Session):
    ai_data = process_command_with_ai(text)
    intent = ai_data.get("intent")
    raw_item = ai_data.get("item")
    qty = float(ai_data.get("quantity", 1))
    
    product = find_closest_product(db, raw_item)
    item_display = product.name_nepali if product else raw_item
    qty_display = convert_to_nepali_num(qty)

    if not product:
        if intent == "CHECK": return {"intent": intent, "response": "❌ यो सामान स्टकमा भेटिएन।"}
        return {"intent": intent, "response": f"❌ '{raw_item}' बुझिन।"}

    if intent == "ADD":
        product.quantity += qty
        total_cost = qty * product.cost_price
        db.add(models.Transaction(product_id=product.id, change_amount=qty, transaction_type="PURCHASE", total_value=total_cost))
        db.commit()
        return {"intent": intent, "response": f"✅ {item_display} {qty_display} {product.unit} थपियो।"}

    if intent == "SALE":
        if product.quantity < qty:
            rem_qty = convert_to_nepali_num(product.quantity)
            return {"intent": intent, "response": f"❌ {item_display} को स्टक पुग्दैन। (बाँकी: {rem_qty} {product.unit})"}
        product.quantity -= qty
        total_rev = qty * product.selling_price
        db.add(models.Transaction(product_id=product.id, change_amount=-qty, transaction_type="SALE", total_value=total_rev))
        db.commit()
        return {"intent": intent, "response": f"✅ {item_display} बिक्री भयो।"}

    if intent == "CHECK":
        return {"intent": intent, "response": f"📦 {item_display}: {convert_to_nepali_num(product.quantity)} {product.unit}।"}

    return {"intent": "UNKNOWN", "response": "❌ आदेश बुझिन।"}

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
        if not model: return {"error": "AI Model not loaded"}
        filename = f"{uuid.uuid4()}.wav"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f: f.write(await file.read())
        result = model.transcribe(filepath, language="ne", fp16=False)
        if os.path.exists(filepath): os.remove(filepath)
        result_data = execute_inventory_logic(result["text"].strip(), db)
        result_data["transcription"] = result["text"].strip()
        return result_data
    except Exception as e:
        return {"error": str(e)}

@app.get("/products", response_model=List[schemas.ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()