import os
import sys

# ==========================================
# 🛑 SYSTEM FIX: MACOS TMPDIR
# ==========================================
# This acts as a shield to prevent the "No usable temporary directory" crash.
tmp_dir = os.path.join(os.path.expanduser("~"), "tmp")
os.environ["TMPDIR"] = tmp_dir
os.makedirs(tmp_dir, exist_ok=True)
print(f"✅ SYSTEM: Temporary directory secured at {tmp_dir}")
# ==========================================

import json
import random
import pickle
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)

# -----------------------------
# 1️⃣ CONFIGURATION
# -----------------------------
MODEL_NAME = "distilbert-base-multilingual-cased"
SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "bert_brain_model")
DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset.json")

# Hyperparameters
MAX_LEN = 64
BATCH_SIZE = 8
EPOCHS = 20  
LEARNING_RATE = 2e-5

# -----------------------------
# 2️⃣ DATA LOADING & AUGMENTATION
# -----------------------------
if not os.path.exists(DATASET_PATH):
    print(f"❌ FATAL: dataset.json not found at {DATASET_PATH}")
    sys.exit(1)

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

print(f"📂 Loaded {len(raw_data)} raw examples.")

# Intelligent Augmentation (Word Swapping)
def augment_text(text):
    words = text.split()
    if len(words) <= 3: return text 
    idx = random.randint(0, len(words) - 2)
    words[idx], words[idx+1] = words[idx+1], words[idx]
    return " ".join(words)

dataset = []
for item in raw_data:
    dataset.append(item) # Original
    # Create 2 synthetic versions for every real example
    dataset.append({"text": augment_text(item["text"]), "label": item["label"]})
    dataset.append({"text": item["text"], "label": item["label"]}) # Duplicate weight

# Shuffle to prevent order bias
random.shuffle(dataset)

texts = [d["text"] for d in dataset]
labels = [d["label"] for d in dataset]

# Create Label Mappings
unique_labels = sorted(list(set(labels)))
label_to_id = {lbl: i for i, lbl in enumerate(unique_labels)}
id_to_label = {i: lbl for lbl, i in label_to_id.items()}
numeric_labels = [label_to_id[l] for l in labels]

print(f"📊 Final Training Size: {len(dataset)} examples")
print(f"📋 Classes Detected: {label_to_id}")

# Stratified Split 
train_texts, val_texts, train_labels, val_labels = train_test_split(
    texts, numeric_labels, test_size=0.15, stratify=numeric_labels, random_state=42
)

# -----------------------------
# 3️⃣ TOKENIZATION
# -----------------------------
print("⚙️  Tokenizing data...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=MAX_LEN)
val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=MAX_LEN)

class InventoryDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = InventoryDataset(train_encodings, train_labels)
val_dataset = InventoryDataset(val_encodings, val_labels)

# -----------------------------
# 4️⃣ MODEL SETUP
# -----------------------------
model = DistilBertForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=len(unique_labels)
)

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average="weighted")
    return {"accuracy": acc, "f1": f1}

training_args = TrainingArguments(
    output_dir=os.path.join(os.path.dirname(__file__), "results"),
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    warmup_steps=50,
    weight_decay=0.01,
    logging_dir=os.path.join(os.path.dirname(__file__), "logs"),
    logging_steps=10,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    save_total_limit=2,
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=4)],
)

# -----------------------------
# 5️⃣ EXECUTION
# -----------------------------
print("🚀 Starting Training... (This may take a few minutes)")
trainer.train()

print(f"💾 Saving Brain to: {SAVE_DIR}")
os.makedirs(SAVE_DIR, exist_ok=True)
model.save_pretrained(SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)

# Save the label map (Crucial for the Brain to speak English)
with open(os.path.join(SAVE_DIR, "label_map.pkl"), "wb") as f:
    pickle.dump(id_to_label, f)

print("🎉 DONE! The AI is ready.")