# ==========================================
# 🇳🇵 NEPALI TO ENGLISH DICTIONARY
# ==========================================
# This file bridges the gap between what the user SAYS
# and what the Database UNDERSTANDS.

# 1. ITEM MAPPING (Voice -> Database Key)
ITEM_MAP = {
    # RICE (Chamal)
    "chamal": "rice",
    "mansuli": "rice",
    "jira": "rice",
    "basmati": "rice",
    "bhat": "rice",

    # LENTILS (Dal)
    "dal": "lentils",
    "masuro": "lentils",
    "rahar": "lentils",
    "mugi": "lentils",
    "chana": "lentils",
    "maas": "lentils",

    # SUGAR (Chini)
    "chini": "sugar",
    "shugar": "sugar",

    # SALT (Nun)
    "nun": "salt",
    "noon": "salt",
    "aayo": "salt", # Common brand 'Aayo Nun'

    # OIL (Tel)
    "tel": "oil",
    "sunflower": "oil",
    "tori": "oil",
    "dhara": "oil",
    "vhatmas": "oil",

    # FLOUR (Pitho/Maida)
    "pitho": "flour",
    "maida": "flour",
    "aata": "flour",

    # TEA (Chiya)
    "chiya": "tea",
    "chiyapatti": "tea",
    "tokla": "tea",

    # NOODLES (Chauchau)
    "chauchau": "noodles",
    "wai": "noodles", # WaiWai
    "rara": "noodles",
    "rum": "noodles", # RumPum

    # SOAP (Sabun)
    "sabun": "soap",
    "lifebuoy": "soap",
    "dettol": "soap",
    "luga": "soap",

    # SPICES (Masala)
    "masala": "spices",
    "besar": "spices", # Turmeric
    "jeera": "spices", # Cumin
    "dhaniya": "spices",
    "methi": "spices",

    # EXTRAS (Good to have)
    "anda": "eggs",
    "biskut": "biscuits",
    "chiura": "beaten_rice"
}

# 2. UNIT MAPPING (Voice -> Database Unit)
UNIT_MAP = {
    # Weight
    "kilo": "kg",
    "kg": "kg",
    "gram": "g",
    "pav": "250g",
    
    # Volume
    "litar": "ltr",
    "liter": "ltr",
    "ml": "ml",
    
    # Packaging
    "packet": "pkt",
    "pyaket": "pkt",
    "pis": "pcs",
    "piece": "pcs",
    "wata": "pcs",
    "ota": "pcs",
    "carton": "ctn",
    "kartun": "ctn",
    "bora": "sack",
    "bori": "sack",
    "cret": "crate",
    "kret": "crate"
}

# 3. NUMBER MAPPING (Text -> Float)
NEPALI_NUM_MAP = {
    "ek": 1, "euta": 1,
    "dui": 2, "duita": 2,
    "tin": 3, "tinta": 3,
    "char": 4, 
    "paach": 5, "pach": 5,
    "cha": 6, 
    "saat": 7, 
    "aath": 8, 
    "nau": 9, 
    "das": 10,
    "pandhra": 15,
    "bis": 20, "bish": 20,
    "pachis": 25,
    "tis": 30,
    "pachas": 50,
    "say": 100, "saya": 100,
    
    # Fractions
    "aadha": 0.5,
    "adha": 0.5,
    "dedh": 1.5,
    "sawa": 1.25,
    "adhai": 2.5
}