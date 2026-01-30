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
    print("⚠️ Switching to 'Rule-Based' Mode (Old Brain).")

# --- 2. PHONETIC NORMALIZER ---
def normalize_nepali(text):
    """
    Flattens confused Nepali characters to a single form.
    """
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
    text = text.replace('ध', 'द') # Fixes Dha -> Da
    
    # Map Vowels
    text = text.replace('ी', 'ि')
    text = text.replace('ू', 'ु')
    text = text.replace('ै', 'े') 
    text = text.replace('ौ', 'ो')

    return text

# --- 3. HELPER FUNCTIONS ---

def nepali_num_to_english(text):
    mapping = str.maketrans("०१२३४५६७८९", "0123456789")
    return text.translate(mapping)

def extract_quantity(text):
    clean_text = nepali_num_to_english(text)
    match = re.search(r"(\d+(\.\d+)?)", clean_text)
    if match:
        return float(match.group(1))
    return 1.0

def extract_item(text):
    """Removes command words and noise words to find the Item Name"""
    
    # --- MASSIVE IGNORE LIST (ACCENT PROOF) ---
    ignore_words = [
        # COMMANDS (ADD)
        "add", "thap", "thapa", "thaba", "thapo", "rakh", "rakha", "kin", "kinera", "lyau", "aayo", "ayo",
        # COMMANDS (SELL/REMOVE)
        "sale", "bech", "becha", "bach", "katau", "kata", "ghata", "hata", "gata", "deu", "dinus", "gayo",
        # COMMANDS (CHECK)
        "check", "chek", "kati", "katti", "koti", "her", "hera", "count", "gan", "stok", "stock",
        # STATUS
        "cha", "chha", "ca", "sa", "ho", "baki", "baaki", "bagi", "baagi", "bacheko",
        # UNITS (Mispronounced)
        "kg", "kilo", "chilo", "tilo", "killa", "kila",
        "liter", "litar", "nitar", "rita", 
        "packet", "pyaket", "jacket",
        "piece", "pis", "fees",
        # FILLERS
        "ma", "ko", "le", "lai", "ta", "ni", "hai", "la", "tyo", "yo", "inventory", "please",
        "ek", "dui", "tin", "char", "paach", "kilo", # Nepali Numbers as text
        "ti", "te", "chahiyo"
    ]
    
    words = text.split()
    clean_words = []
    
    for word in words:
        norm_word = normalize_nepali(word)
        # Filter logic
        if not re.search(r'\d', nepali_num_to_english(word)) and \
           word.lower() not in ignore_words and \
           norm_word not in ignore_words:
            clean_words.append(word)
            
    return " ".join(clean_words) if clean_words else None

# --- 4. MAIN PROCESS FUNCTION ---

def process_command_with_ai(text):
    print(f"🧠 Processing: '{text}'")
    text_clean = text.lower().strip()
    
    # A. PREDICT INTENT
    intent = "UNKNOWN"
    
    if BERT_AVAILABLE:
        try:
            inputs = tokenizer(text_clean, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
            with torch.no_grad():
                logits = model(**inputs).logits
            
            # Boost Check Intent if we hear specific status words
            if any(w in text_clean for w in ["kati", "baagi", "bagi", "cha", "katti"]):
                 if "CHECK" in id_to_label.values():
                     check_idx = [k for k, v in id_to_label.items() if v == "CHECK"][0]
                     logits[0][check_idx] += 2.0

            predicted_class_id = logits.argmax().item()
            intent = id_to_label[predicted_class_id]
            confidence = torch.softmax(logits, dim=1).max().item()
            
            print(f"🤖 BERT Intent: {intent} (Confidence: {confidence:.2f})")
            if confidence < 0.6: intent = "UNKNOWN"

        except Exception as e:
            print(f"❌ BERT Error: {e}")
            intent = "UNKNOWN"
    
    # B. FALLBACK (If BERT fails)
    if intent == "UNKNOWN":
        norm_text = normalize_nepali(text_clean)
        # Expanded Keyword Fallback
        if any(w in norm_text for w in ["thap", "thaba", "add", "kin", "aayo", "rakh"]): intent = "ADD"
        elif any(w in norm_text for w in ["bech", "ghata", "kata", "sale", "gayo"]): intent = "SALE"
        elif any(w in norm_text for w in ["kati", "baki", "bagi", "her", "check"]): intent = "CHECK"

    # C. EXTRACT
    item = extract_item(text_clean)
    qty = extract_quantity(text_clean)

    return {"intent": intent, "item": item, "quantity": qty, "unit": "kg", "customer": None}