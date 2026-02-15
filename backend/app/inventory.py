import os
import shutil
import uuid
import torch
import whisper
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.brain import process_command
from app import models, schemas # Needed for the product list

# Initialize Router
router = APIRouter()

# ==========================================
# 🎤 SETUP WHISPER AI (Voice to Text)
# ==========================================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Loading Whisper model on {device}...")

try:
    # 'base' is a good balance. Use 'small' if you have a strong GPU.
    model = whisper.load_model("base", device=device)
    print("✅ Whisper AI Loaded Successfully!")
except Exception as e:
    print(f"⚠️ Whisper Load Failed: {e}")
    model = None

# Temp folder for audio uploads
UPLOAD_DIR = "temp_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# 🧠 SHARED LOGIC (The Executioner)
# ==========================================
def execute_inventory_logic(user_text: str, db: Session):
    """
    Takes text -> Asks Brain -> Updates DB -> Returns Nepali Message
    """
    print(f"🧠 Processing: {user_text}")

    # 1. Ask the Brain
    logic = process_command(user_text)
    
    intent = logic["intent"]
    item_key = logic["item"]
    qty = logic["quantity"]
    unit = logic["unit"]

    print(f"🤖 DECISION: {intent} {qty} {unit} of {item_key}")

    # 2. Handle Unknown Items (Safety Check)
    if not item_key and intent != "CHECK": 
        return {
            "status": "error",
            "logic": logic,
            "nepali_msg": "कुन सामान हो? बुझिएन।"
        }

    # 3. EXECUTE DATABASE ACTIONS
    try:
        # 🟢 CASE 1: ADD STOCK
        if intent == "ADD":
            # Check if item exists
            check_sql = text("SELECT quantity FROM inventory WHERE name = :name")
            existing = db.execute(check_sql, {"name": item_key}).fetchone()
            
            if existing:
                update_sql = text("UPDATE inventory SET quantity = quantity + :qty WHERE name = :name")
                db.execute(update_sql, {"qty": qty, "name": item_key})
                msg = f"हस, {qty} {unit} {item_key} थपियो।"
            else:
                insert_sql = text("INSERT INTO inventory (name, quantity, unit) VALUES (:name, :qty, :unit)")
                db.execute(insert_sql, {"name": item_key, "qty": qty, "unit": unit})
                msg = f"नयाँ सामान: {item_key}, {qty} {unit} राखियो।"
            
            db.commit()
            return {
                "status": "success",
                "action": "added",
                "nepali_msg": msg,
                "logic": logic
            }

        # 🔴 CASE 2: SALE STOCK
        elif intent == "SALE":
            check_sql = text("SELECT quantity FROM inventory WHERE name = :name")
            result = db.execute(check_sql, {"name": item_key}).fetchone()
            
            if not result:
                return {"status": "error", "nepali_msg": f"{item_key} स्टकमा छैन।"}
            
            current_stock = result[0]
            if current_stock < qty:
                return {
                    "status": "warning",
                    "nepali_msg": f"स्टक पुग्दैन। जम्मा {current_stock} {unit} बाँकी छ।"
                }
            
            update_sql = text("UPDATE inventory SET quantity = quantity - :qty WHERE name = :name")
            db.execute(update_sql, {"qty": qty, "name": item_key})
            db.commit()
            return {
                "status": "success",
                "action": "sold",
                "nepali_msg": f"ल, {qty} {unit} {item_key} बिक्री भयो।",
                "logic": logic
            }

        # 🔵 CASE 3: CHECK STOCK
        elif intent == "CHECK":
            if item_key:
                # Check specific item
                sql = text("SELECT quantity, unit FROM inventory WHERE name = :name")
                result = db.execute(sql, {"name": item_key}).fetchone()
                if result:
                    return {"status": "success", "nepali_msg": f"{item_key} {result[0]} {result[1]} बाँकी छ।"}
                return {"status": "success", "nepali_msg": f"{item_key} स्टकमा भेटिएन।"}
            else:
                # Check General Stock (Top 5 Items)
                sql = text("SELECT name, quantity, unit FROM inventory LIMIT 5")
                results = db.execute(sql).fetchall()
                if not results:
                    return {"status": "success", "nepali_msg": "स्टक खाली छ।"}
                
                items_desc = ", ".join([f"{r[0]} ({r[1]})" for r in results])
                return {"status": "success", "nepali_msg": f"हालको स्टक: {items_desc}..."}

        # ⚫ CASE 4: UNKNOWN
        else:
            return {
                "status": "ignored",
                "nepali_msg": "माफ गर्नुस, मैले बुझिन।",
                "logic": logic
            }

    except Exception as e:
        db.rollback()
        print(f"❌ DB Error: {e}")
        return {"status": "error", "nepali_msg": "डाटाबेस समस्या आयो।"}

# ==========================================
# 🔌 ENDPOINTS
# ==========================================

# 1. TEXT Endpoint (For testing or Chat UI)
@router.post("/command")
async def process_text_command(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    user_text = body.get("text", "")
    return execute_inventory_logic(user_text, db)

# 2. VOICE Endpoint (For Microphone Input)
@router.post("/voice")
async def process_voice_command(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not model:
        return {"status": "error", "nepali_msg": "AI मोडेल लोड भएन।"}

    # A. Save Audio File Temporarily
    filename = f"{uuid.uuid4()}.wav"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # B. Transcribe (Audio -> Text)
        print(f"🎧 Transcribing {filename}...")
        result = model.transcribe(filepath, language="ne", fp16=False)
        transcribed_text = result["text"].strip()
        print(f"🗣️ User Said: {transcribed_text}")
        
        # C. Execute Logic
        response = execute_inventory_logic(transcribed_text, db)
        
        # Add transcription to response so frontend can show what user said
        response["transcription"] = transcribed_text
        return response

    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        return {"status": "error", "message": str(e), "nepali_msg": "आवाज बुझ्न सकिएन।"}
    
    finally:
        # D. Cleanup (Delete temp file)
        if os.path.exists(filepath):
            os.remove(filepath)

# 3. GET PRODUCTS (List items for Frontend)
@router.get("/products", response_model=List[schemas.ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()