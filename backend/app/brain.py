import os
import torch
import pickle
import re
from transformers import AutoTokenizer, DistilBertForSequenceClassification
from app.nepali_mapping import ITEM_MAP, UNIT_MAP, NEPALI_NUM_MAP

# -----------------------------
# 1️⃣ INITIALIZATION
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "bert_brain_model")

print(f"🧠 BRAIN: Initializing from {MODEL_PATH}...")

device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = None
model = None
id_to_label = {}
BERT_READY = False

try:
    # Load the Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    
    # Load the Model (Safe Mode: ignores mismatched sizes if you retrain often)
    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL_PATH, 
        ignore_mismatched_sizes=True
    )
    model.to(device)
    model.eval()
    
    # Load the Labels
    with open(os.path.join(MODEL_PATH, "label_map.pkl"), "rb") as f:
        id_to_label = pickle.load(f)
        
    BERT_READY = True
    print("✅ BRAIN: BERT Model is Online & Ready.")
except Exception as e:
    print(f"⚠️ BRAIN: BERT failed to load. Reason: {e}")
    print("⚠️ BRAIN: Switching to RULE-BASED fallback mode.")

# -----------------------------
# 2️⃣ LOGIC: EXTRACTION
# -----------------------------
def extract_quantity(text):
    text = text.lower()
    
    # A. Check for known word-numbers (e.g., "dedh", "pachas")
    for word, val in NEPALI_NUM_MAP.items():
        # strict word boundary check to avoid matching "tin" inside "martin"
        if re.search(r'\b' + re.escape(word) + r'\b', text):
            return float(val)
            
    # B. Check for digits (e.g., "5", "10.5")
    digit_match = re.search(r"(\d+(\.\d+)?)", text)
    if digit_match:
        return float(digit_match.group(1))
        
    return 1.0 # Default fallback

def extract_details(text):
    text = text.lower()
    found_item = None
    found_unit = "unit" # Default
    
    # Find Item (Longest match first to catch 'sunflower oil' before 'oil')
    sorted_items = sorted(ITEM_MAP.keys(), key=len, reverse=True)
    for nepali_key in sorted_items:
        if nepali_key in text:
            found_item = ITEM_MAP[nepali_key]
            break
            
    # Find Unit
    for nepali_unit, english_unit in UNIT_MAP.items():
        if nepali_unit in text:
            found_unit = english_unit
            break
            
    return found_item, found_unit

# -----------------------------
# 3️⃣ LOGIC: PREDICTION
# -----------------------------
def process_command(text):
    response = {
        "intent": "UNKNOWN",
        "item": None,
        "quantity": 0,
        "unit": None,
        "confidence": 0.0
    }
    
    # Step 1: Extract Entities (Item, Qty, Unit)
    response["quantity"] = extract_quantity(text)
    item, unit = extract_details(text)
    response["item"] = item
    response["unit"] = unit

    # Step 2: Determine Intent (Hybrid Approach)
    intent = "UNKNOWN"
    conf = 0.0

    # PLAN A: Ask BERT
    if BERT_READY:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=64).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        conf_score, pred_idx = torch.max(probs, dim=1)
        conf = round(conf_score.item(), 4)
        
        # Threshold Check: If BERT is < 60% sure, don't trust it.
        if conf > 0.60:
            intent = id_to_label.get(pred_idx.item(), "UNKNOWN")

    # PLAN B: Rule Fallback (If BERT is dead or confused)
    if intent == "UNKNOWN":
        text_lower = text.lower()
        if any(x in text_lower for x in ["thap", "aayo", "rakh", "kin", "lyau"]):
            intent = "ADD"
            conf = 1.0
        elif any(x in text_lower for x in ["bech", "gayo", "ghatau", "bikri", "kat"]):
            intent = "SALE"
            conf = 1.0
        elif any(x in text_lower for x in ["kati", "her", "check", "stock", "sakin"]):
            intent = "CHECK"
            conf = 1.0

    response["intent"] = intent
    response["confidence"] = conf
    
    print(f"🧠 Analysis: {text} -> {response['intent']} ({response['confidence']*100}%) | Item: {response['item']}")
    return response