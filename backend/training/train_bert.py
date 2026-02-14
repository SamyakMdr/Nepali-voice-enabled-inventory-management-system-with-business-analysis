import json
import os
import random
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
# 1️⃣ SETTINGS
# -----------------------------
MODEL_NAME = "distilbert-base-multilingual-cased"
SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "bert_brain_model")
MAX_LEN = 64
BATCH_SIZE = 8
EPOCHS = 15
LEARNING_RATE = 3e-5

# -----------------------------
# 2️⃣ LOAD DATA
# -----------------------------
dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")

if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"{dataset_path} not found. Please add your dataset!")

with open(dataset_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# -----------------------------
# 2.5️⃣ DATA AUGMENTATION
# -----------------------------
def augment(text):
    """Simple augmentation: randomly drop one word."""
    words = text.split()
    if len(words) <= 2:
        return text
    idx = random.randint(0, len(words) - 1)
    return " ".join(words[:idx] + words[idx + 1:])

augmented = []
for item in data:
    augmented.append(item)
    # Add 2 augmented copies per sample
    for _ in range(2):
        augmented.append({"text": augment(item["text"]), "label": item["label"]})

random.shuffle(augmented)
data = augmented

print(f"📊 Dataset: {len(data)} samples (with augmentation)")

texts = [item["text"] for item in data]
labels = [item["label"] for item in data]

# Map labels to numbers
unique_labels = sorted(list(set(labels)))
label_map = {label: i for i, label in enumerate(unique_labels)}
id_to_label = {i: label for label, i in label_map.items()}
numeric_labels = [label_map[label] for label in labels]

print(f"📋 Labels: {label_map}")
for lbl in unique_labels:
    count = labels.count(lbl)
    print(f"   {lbl}: {count} samples")

# Train/Validation Split (stratified)
train_texts, val_texts, train_labels, val_labels = train_test_split(
    texts, numeric_labels, test_size=0.2, random_state=42, stratify=numeric_labels
)

# -----------------------------
# 3️⃣ TOKENIZATION
# -----------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

train_encodings = tokenizer(
    train_texts, truncation=True, padding=True, max_length=MAX_LEN
)
val_encodings = tokenizer(
    val_texts, truncation=True, padding=True, max_length=MAX_LEN
)

# -----------------------------
# 4️⃣ DATASET CLASS
# -----------------------------
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
# 5️⃣ LOAD MODEL
# -----------------------------
model = DistilBertForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(unique_labels)
)

# -----------------------------
# 6️⃣ METRICS
# -----------------------------
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average="weighted")
    print(f"   📈 Eval — Accuracy: {acc:.4f}, F1: {f1:.4f}")
    return {"accuracy": acc, "f1": f1}

# -----------------------------
# 7️⃣ TRAINING ARGUMENTS
# -----------------------------
training_args = TrainingArguments(
    output_dir=os.path.join(os.path.dirname(__file__), "results"),
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_dir=os.path.join(os.path.dirname(__file__), "logs"),
    logging_steps=10,
    learning_rate=LEARNING_RATE,
    warmup_ratio=0.1,
    weight_decay=0.01,
    save_total_limit=3,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True,
    report_to="none",
)

# -----------------------------
# 8️⃣ TRAINER
# -----------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
)

# -----------------------------
# 9️⃣ TRAIN MODEL
# -----------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🧠 Training BERT on {device}...")
trainer.train()

# -----------------------------
# 🔟 EVALUATE
# -----------------------------
print("\n📊 Final Evaluation:")
eval_results = trainer.evaluate()
print(f"   Accuracy: {eval_results.get('eval_accuracy', 'N/A')}")
print(f"   F1 Score: {eval_results.get('eval_f1', 'N/A')}")

# -----------------------------
# 1️⃣1️⃣ SAVE MODEL
# -----------------------------
print("💾 Saving model...")
os.makedirs(SAVE_DIR, exist_ok=True)
model.save_pretrained(SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)

import pickle
with open(os.path.join(SAVE_DIR, "label_map.pkl"), "wb") as f:
    pickle.dump(id_to_label, f)

print("🎉 Training Complete!")
