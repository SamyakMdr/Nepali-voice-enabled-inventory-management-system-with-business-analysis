import json
import os
import torch
from sklearn.model_selection import train_test_split
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments

# 1. Setup
MODEL_NAME = "distilbert-base-multilingual-cased"
SAVE_DIR = "../bert_brain_model"  # Where the trained model will live

# 2. Load Data
with open("dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

texts = [item["text"] for item in data]
labels = [item["label"] for item in data]

# Map labels to numbers (ADD=0, CHECK=1, SALE=2)
label_map = {label: i for i, label in enumerate(set(labels))}
id_to_label = {i: label for label, i in label_map.items()}
numeric_labels = [label_map[l] for l in labels]

# 3. Tokenize (Turn text into numbers)
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
encodings = tokenizer(texts, truncation=True, padding=True, max_length=128)

class InventoryDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

dataset = InventoryDataset(encodings, numeric_labels)

# 4. Train the Model
model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=len(label_map))

training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=10,         # Loop over data 10 times
    per_device_train_batch_size=4,
    logging_dir='./logs',
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

print("🧠 Training BERT... (This might take a minute)")
trainer.train()

# 5. Save the new Brain
print(f"💾 Saving model to {SAVE_DIR}...")
model.save_pretrained(SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)

# Save the label map so the app knows 0=ADD
import pickle
with open(os.path.join(SAVE_DIR, "label_map.pkl"), "wb") as f:
    pickle.dump(id_to_label, f)

print("🎉 Done! BERT is ready.")