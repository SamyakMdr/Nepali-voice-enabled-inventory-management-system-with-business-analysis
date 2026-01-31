import torch
import pickle
import re
import os
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

# --- 1. SETUP & MODEL LOADING ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "bert_brain_model")

print(f"🧠 Loading BERT Brain from: {MODEL_PATH}...")

BERT_AVAILABLE = False
try:
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
    
    with open(os.path.join(MODEL_PATH, "label_map.pkl"), "rb") as f:
        id_to_label = pickle.load(f)
        
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    
    BERT_AVAILABLE = True
    print("✅ BERT Loaded Successfully!")
except Exception as e:
    print(f"⚠️ BERT Load Failed: {e}")
    print("⚠️ Switching to 'Rule-Based' Mode.")

# --- 2. DATA MAPPINGS ---

# Nepali Numbers
NEPALI_NUMBERS = {
    "एक": 1, "दुई": 2, "तीन": 3, "चार": 4, "पाँच": 5,
    "छ": 6, "सात": 7, "आठ": 8, "नौ": 9, "दश": 10,
    "एघार": 11, "बाह्र": 12, "१": 1, "२": 2, "३": 3, "४": 4, "५": 5,
    "६": 6, "७": 7, "८": 8, "९": 9, "१०": 10
}

# STRONG KEYWORDS (The "Cheat Sheet" for the AI)
# If these words appear, we don't even need to ask BERT.
STRONG_KEYWORDS = {
    "SALE": ["bech", "ghata", "kata", "katao", "katayo", "sale", "deu", "dinus", "gayo", "biki", "sales"],
    "ADD": ["kin", "thap", "lyayo", "aayo", "rakh", "jod", "add", "buy", "purchase"],
    "CHECK": ["kati", "katti", "check", "stock", "her", "status", "baki", "cha", "chha", "inventory"]
}

# --- 3. HELPER FUNCTIONS ---

def normalize_nepali(text):
    """Flattens confused Nepali characters."""
    if not text: return ""
    text = text.lower().strip()
    
    # Map Consonants
    text = text.replace('छ', 'च')
    text = text.replace('क्ष', 'छ') 
    text = text.replace('श', 'स')
    text = text.replace('ष', 'स')
    text = text.replace('व', 'ब')
    text = text.replace('ण', 'न')
    text = text.replace('त', 'द') # Fixes Taal -> Daal
    text = text.replace('ध', 'द') 
    
    # Map Vowels
    text = text.replace('ी', 'ि')
    text = text.replace('ू', 'ु')
    text = text.replace('ै', 'े') 
    text = text.replace('ौ', 'ो')

    return text

def nepali_num_to_english(text):
    mapping = str.maketrans("०१२३४५६७८९", "0123456789")
    return text.translate(mapping)

def extract_quantity(text):
    """Extracts numbers from Digits OR Words (ek, dui)"""
    clean_text = nepali_num_to_english(text)
    
    # 1. Look for digits (e.g. 10, 2.5)
    match = re.search(r"(\d+(\.\d+)?)", clean_text)
    if match:
        return float(match.group(1))
    
    # 2. Look for Number Words (Nepali)
    words = text.split()
    for word in words:
        if word in NEPALI_NUMBERS:
            return float(NEPALI_NUMBERS[word])
            
    return 1.0

def extract_item(text):
    """Removes command words to find the Item Name"""
    
    # Words to ignore so we only see the ITEM Name
    ignore_words = [
        # COMMANDS
        "add", "thap", "thapo", "rakh", "kin", "lyau", "aayo",
        "sale", "bech", "katao", "kata", "ghata", "hata", "deu", "gayo",
        "check", "kati", "her", "stock", "inventory",
        # STATUS
        "cha", "chha", "ho", "baki",
        # UNITS
        "kg", "kilo", "chilo", "liter", "packet", "piece", "pis",
        # FILLERS
        "ma", "ko", "le", "lai", "ta", "ni", "hai", "la", "yo", "tyo", "ek", "dui"
    ]
    
    words = text.split()
    clean_words = []
    
    for word in words:
        norm_word = normalize_nepali(word)
        # Filter: Not a number, not in ignore list
        if not re.search(r'\d', nepali_num_to_english(word)) and \
           word.lower() not in ignore_words and \
           norm_word not in ignore_words and \
           word not in NEPALI_NUMBERS:
            clean_words.append(word)
            
    return " ".join(clean_words) if clean_words else None

# --- 4. MAIN PROCESS FUNCTION ---

def process_command_with_ai(text):
    print(f"🧠 Processing: '{text}'")
    text_clean = text.lower().strip()
    norm_text = normalize_nepali(text_clean)
    
    intent = "UNKNOWN"
    
    # A. RULE-BASED CHECK (PRIORITY 1)
    # This ensures "Katao" works 100% of the time, even if BERT is confused.
    for category, keywords in STRONG_KEYWORDS.items():
        if any(k in norm_text or k in text_clean for k in keywords):
            intent = category
            print(f"⚡ Rule Match: {intent} (Keyword found)")
            break
    
    # B. BERT MODEL CHECK (PRIORITY 2)
    # Only use BERT if Rules failed
    if intent == "UNKNOWN" and BERT_AVAILABLE:
        try:
            inputs = tokenizer(text_clean, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
            with torch.no_grad():
                logits = model(**inputs).logits
            
            # Context Boost for "Check"
            if any(w in norm_text for w in ["kati", "cha", "katti"]):
                 if "CHECK" in id_to_label.values():
                     check_idx = [k for k, v in id_to_label.items() if v == "CHECK"][0]
                     logits[0][check_idx] += 2.0

            predicted_class_id = logits.argmax().item()
            bert_intent = id_to_label[predicted_class_id]
            confidence = torch.softmax(logits, dim=1).max().item()
            
            # Lowered threshold slightly to 0.5 to catch more commands
            if confidence > 0.5:
                intent = bert_intent
                print(f"🤖 BERT Intent: {intent} (Confidence: {confidence:.2f})")
            else:
                print(f"⚠️ BERT Low Confidence: {bert_intent} ({confidence:.2f})")
                
        except Exception as e:
            print(f"❌ BERT Error: {e}")

    # C. EXTRACT
    item = extract_item(text_clean)
    qty = extract_quantity(text_clean)

    return {"intent": intent, "item": item, "quantity": qty, "unit": "kg", "customer": None}