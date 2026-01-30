import re

def nepali_num_to_english(text):
    """Converts Nepali text numbers (१, २) to English integers (1, 2)"""
    mapping = str.maketrans("०१२३४५६७८९", "0123456789")
    return text.translate(mapping)

def extract_quantity(text):
    """Finds numbers in the text (e.g., '2 kg', '५ किलो')"""
    # Convert Nepali digits to English first
    clean_text = nepali_num_to_english(text)
    
    # Look for integer or decimal numbers
    match = re.search(r"(\d+(\.\d+)?)", clean_text)
    if match:
        return float(match.group(1))
    return 1.0  # Default to 1 if no number found

def process_command_with_ai(text):
    """
    A 'Local Brain' that understands Nepali Inventory Commands
    without needing the Internet or BERT.
    """
    print(f"🧠 Local Brain processing: {text}")
    
    # 1. Normalize Text
    text = text.lower().strip()
    
    # 2. Define Keywords
    # ADD (Adding stock)
    keywords_add = ["थप", "kin", "lyau", "rakh", "add", "kinera", "किनेर", "राख"]
    # SALE (Selling/Removing stock)
    keywords_sale = ["katau", "ghata", "bech", "sale", "deduct", "कटाऊ", "बेच", "घटाऊ", "दिनु", "deu"]
    # CHECK (Checking stock)
    keywords_check = ["kati", "check", "stock", "कति", "check", "baki", "बाँकी"]

    # 3. Detect Intent
    intent = "UNKNOWN"
    if any(w in text for w in keywords_add):
        intent = "ADD"
    elif any(w in text for w in keywords_sale):
        intent = "SALE"
    elif any(w in text for w in keywords_check):
        intent = "CHECK"

    # 4. Extract Quantity
    quantity = extract_quantity(text)

    # 5. Extract Item Name
    # Strategy: Remove the command keywords and numbers. What is left is likely the Item.
    ignore_words = keywords_add + keywords_sale + keywords_check + [
        "ek", "dui", "tin", "char", "paach", "kilo", "kg", "packet", "liter", "ko", "ma", "le", "please", "inventory",
        "एक", "दुई", "तीन", "चार", "पाँच", "किलो", "केजी", "प्याकेट", "लिटर", "को", "मा", "ले"
    ]
    
    words = text.split()
    item_words = []
    
    for word in words:
        # If word is NOT a number and NOT a keyword, it's part of the Item Name
        if not re.search(r'\d', nepali_num_to_english(word)) and word not in ignore_words:
            item_words.append(word)
            
    # Join leftovers to form item name (e.g., "chini")
    item = " ".join(item_words) if item_words else None

    # 6. Return Data Structure
    return {
        "intent": intent,
        "item": item,
        "quantity": quantity,
        "unit": "kg",     # Default unit
        "customer": None  # Simple version doesn't extract customer names yet
    }
    
    