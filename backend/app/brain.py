import torch
import pickle
import re
import os
from transformers import AutoTokenizer, DistilBertForSequenceClassification

# -------------------------------------------------
# 1️⃣ MODEL SETUP
# -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "bert_brain_model")

print(f"🧠 Loading SmartBiz Brain from: {MODEL_PATH}")

device = "cuda" if torch.cuda.is_available() else "cpu"
BERT_AVAILABLE = False
tokenizer = None
bert_model = None
id_to_label = {}

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    bert_model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
    bert_model.to(device)
    bert_model.eval()
    torch.set_grad_enabled(False)

    with open(os.path.join(MODEL_PATH, "label_map.pkl"), "rb") as f:
        id_to_label = pickle.load(f)

    BERT_AVAILABLE = True
    print(f"✅ BERT Loaded Successfully — labels: {list(id_to_label.values())}")

except Exception as e:
    print("⚠️ BERT Load Failed:", e)
    print("⚠️ Running in Rule-Based Mode Only")

# -------------------------------------------------
# 2️⃣ KNOWN ITEMS (STRICT CONTROL)
# -------------------------------------------------

KNOWN_ITEMS = {
    "चामल", "चामल",
    "दाल", "मसुरो", "रहर", "मुगी", "चना",
    "तेल", "सनफ्लावर",
    "चिनी",
    "नुन",
    "चिउरा",
    "मैदा",
    "अण्डा",
    "बेसार",
    "बिस्कुट",
}

# Map sub-items back to primary item names
ITEM_ALIASES = {
    "मसुरो": "दाल",
    "रहर": "दाल",
    "मुगी": "दाल",
    "चना": "दाल",
    "सनफ्लावर": "तेल",
    "बासमती": "चामल",
    "जिरा": "चामल",
    "सोना": "चामल",
    "मन्सुली": "चामल",
    "मसिनो": "चामल",
    # Common Whisper mishearings
    "ताल": "दाल",
    "टाल": "दाल",
    "थाल": "दाल",
    "दान": "दाल",
    "जमाल": "चामल",
    "सामल": "चामल",
    "छामल": "चामल",
    "चिनि": "चिनी",
    "छिनि": "चिनी",
    "सिनी": "चिनी",
    "टेल": "तेल",
    "टैल": "तेल",
    "पेल": "तेल",
    "नून": "नुन",
    "लुन": "नुन",
}

# -------------------------------------------------
# 3️⃣ STRONG INTENT KEYWORDS (expanded)
# -------------------------------------------------

STRONG_KEYWORDS = {
    "SALE": [
        "बेच", "बेचें", "बेचियो", "बिक्री",
        "घटाउ", "घटाऊ", "कटाओ", "कटाउ",
        "देउ", "दिनु", "दे ", "लग्यो",
        "डेलिभरी", "प्याक", "दर्ता",
    ],
    "ADD": [
        "थप", "थपियो", "राख", "जोड",
        "आयो", "ल्याऊ", "ल्याउ", "किनेर",
        "अपडेट", "गोदाम", "स्टक अपडेट",
    ],
    "CHECK": [
        "कति", "बाँकी", "बांकी",
        "हेर", "स्टक", "सकियो", "सकिन",
        "छ", "हिसाब",
    ],
}

# -------------------------------------------------
# 4️⃣ NEPALI NUMBER SUPPORT (expanded)
# -------------------------------------------------

NEPALI_NUMBERS = {
    "एक": 1, "दुई": 2, "तीन": 3, "चार": 4, "पाँच": 5,
    "छ": 6, "सात": 7, "आठ": 8, "नौ": 9, "दश": 10,
    "एघार": 11, "बाह्र": 12, "तेह्र": 13, "चौध": 14,
    "पन्ध्र": 15, "सोह्र": 16, "सत्र": 17, "अठार": 18,
    "उन्नाइस": 19, "बीस": 20, "पच्चीस": 25,
    "तीस": 30, "चालीस": 40, "पचास": 50,
    "साठी": 60, "सत्तरी": 70, "अस्सी": 80,
    "नब्बे": 90, "सय": 100,
    "आधा": 0.5, "डेढ": 1.5, "पौने": 0.75,
    "१": 1, "२": 2, "३": 3, "४": 4, "५": 5,
    "६": 6, "७": 7, "८": 8, "९": 9, "१०": 10,
    "२०": 20, "२५": 25, "३०": 30, "५०": 50, "१००": 100,
}

def nepali_num_to_english(text):
    """Convert Nepali digits to English digits."""
    mapping = str.maketrans("०१२३४५६७८९", "0123456789")
    return text.translate(mapping)

# -------------------------------------------------
# 5️⃣ NORMALIZATION
# -------------------------------------------------

def normalize_nepali(text):
    """Normalize Nepali text for fuzzy matching (exported for main.py)."""
    text = text.strip()
    replacements = {
        "क्ष": "छ",
        "श": "स",
        "ष": "स",
        "व": "ब",
        "ण": "न",
        "ै": "े",
        "ौ": "ो",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def normalize_text(text):
    """Full normalization: lowercase + phonetic folding."""
    return normalize_nepali(text.lower().strip())

# -------------------------------------------------
# 6️⃣ EXTRACT QUANTITY + UNIT
# -------------------------------------------------

def extract_quantity_and_unit(text):
    text_en = nepali_num_to_english(text)

    # 1) Try Nepali word numbers first (longest match first)
    quantity = None
    for word, val in sorted(NEPALI_NUMBERS.items(), key=lambda x: -len(x[0])):
        if word in text:
            quantity = val
            break

    # 2) Fall back to digit regex
    if quantity is None:
        match = re.search(r"\d+(\.\d+)?", text_en)
        quantity = float(match.group()) if match else 1.0

    # Detect unit
    if "किलो" in text or "kg" in text.lower():
        unit = "kg"
    elif "बोरा" in text:
        unit = "bora"
    elif "वटा" in text:
        unit = "piece"
    elif "प्याकेट" in text:
        unit = "packet"
    elif "लिटर" in text:
        unit = "litre"
    elif "कार्टुन" in text:
        unit = "carton"
    else:
        unit = "kg"

    return float(quantity), unit

# -------------------------------------------------
# 7️⃣ EXTRACT ITEM (with aliases + substring matching)
# -------------------------------------------------

def extract_item(text):
    words = text.split()

    # Direct match
    for word in words:
        if word in KNOWN_ITEMS:
            return word

    # Alias match
    for word in words:
        if word in ITEM_ALIASES:
            return ITEM_ALIASES[word]

    # Substring match (e.g. "चामलको" contains "चामल")
    for item in KNOWN_ITEMS:
        if item in text:
            return item

    return None

# -------------------------------------------------
# 8️⃣ BERT INFERENCE
# -------------------------------------------------

def predict_intent_bert(text, threshold=0.55):
    """Run BERT inference and return (intent, confidence) or (None, 0)."""
    if not BERT_AVAILABLE:
        return None, 0.0

    try:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=64,
        ).to(device)

        with torch.no_grad():
            outputs = bert_model(**inputs)

        probs = torch.softmax(outputs.logits, dim=1)
        confidence, pred_id = torch.max(probs, dim=1)
        confidence = confidence.item()
        pred_id = pred_id.item()
        intent = id_to_label.get(pred_id, "UNKNOWN")

        print(f"🤖 BERT → {intent} ({confidence:.2f})")
        return intent, confidence

    except Exception as e:
        print("❌ BERT Error:", e)
        return None, 0.0

# -------------------------------------------------
# 9️⃣ RULE-BASED INTENT
# -------------------------------------------------

def predict_intent_rules(text):
    """Return intent from keyword matching, or None."""
    for category, keywords in STRONG_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                print(f"⚡ Rule Match: {category} (keyword: {keyword})")
                return category
    return None

# -------------------------------------------------
# 🔟 MAIN PROCESS FUNCTION
# -------------------------------------------------

def process_command_with_ai(text):
    print(f"\n🧠 Processing: {text}")

    text_clean = normalize_text(text)
    # Also keep original (un-normalized) for BERT — the model was trained on raw text
    text_original = text.strip()

    # ----------------------------
    # A. RULE-BASED PRIORITY
    # ----------------------------
    intent = predict_intent_rules(text_clean)

    # ----------------------------
    # B. BERT (on original text — matches training data better)
    # ----------------------------
    if intent is None:
        bert_intent, bert_conf = predict_intent_bert(text_original)
        if bert_intent and bert_conf >= 0.55:
            intent = bert_intent

    # ----------------------------
    # C. BERT on normalized text as secondary attempt
    # ----------------------------
    if intent is None:
        bert_intent, bert_conf = predict_intent_bert(text_clean)
        if bert_intent and bert_conf >= 0.50:
            intent = bert_intent

    if intent is None:
        intent = "UNKNOWN"

    # ----------------------------
    # D. EXTRACT DATA
    # ----------------------------
    item = extract_item(text_clean) or extract_item(text_original)
    quantity, unit = extract_quantity_and_unit(text_original)

    print(f"📋 Result: intent={intent}, item={item}, qty={quantity}, unit={unit}")

    return {
        "intent": intent,
        "item": item,
        "quantity": quantity,
        "unit": unit,
        "customer": None,
    }
