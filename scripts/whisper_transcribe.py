import os
import whisper
import pandas as pd
import torch
import warnings

# Suppress other minor warnings
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
MODEL = "large"  # tiny / base / small / medium / large
INPUT_FOLDER = "processed_audio" 
OUTPUT_CSV = "transcriptions.csv"

# Check device (Mac uses CPU usually)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Loading Whisper '{MODEL}' model on {device}...")

model = whisper.load_model(MODEL, device=device)

rows = []

# Verify folder exists
if not os.path.exists(INPUT_FOLDER):
    print(f"❌ Error: Folder '{INPUT_FOLDER}' not found!")
    exit()

files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith((".wav", ".mp3", ".ogg"))]
total_files = len(files)

print(f"📂 Found {total_files} audio files. Starting transcription...\n")

for i, filename in enumerate(files):
    path = os.path.join(INPUT_FOLDER, filename)
    try:
        # 🔥 THE FIX: fp16=False forces it to use 32-bit mode directly (No warnings)
        result = model.transcribe(path, language="ne", fp16=False)
        
        text = result["text"].strip()
        rows.append({"file": filename, "text": text})
        
        print(f"[{i+1}/{total_files}] ✔ Done: {filename}")
        
    except Exception as e:
        print(f"[{i+1}/{total_files}] ❌ Failed: {filename} | Error: {e}")

# Save to CSV
df = pd.DataFrame(rows)
df.to_csv(OUTPUT_CSV, index=False)

print(f"\n🎉 All done! Saved {len(rows)} rows to '{OUTPUT_CSV}'")