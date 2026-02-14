import os
import whisper
import pandas as pd
import torch
import warnings

warnings.filterwarnings("ignore")

# ---------- PATH SETUP ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FOLDER = os.path.join(BASE_DIR, "processed_audio")
OUTPUT_CSV = os.path.join(BASE_DIR, "transcriptions.csv")

# ---------- CONFIG ----------
MODEL = "large"  # tiny / base / small / medium / large

# ---------- DEVICE ----------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Loading Whisper '{MODEL}' model on {device}...")

model = whisper.load_model(MODEL, device=device)

# ---------- VERIFY INPUT ----------
if not os.path.exists(INPUT_FOLDER):
    print(f"❌ Error: Folder '{INPUT_FOLDER}' not found!")
    exit()

files = sorted([f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".wav")])
total_files = len(files)

print(f"📂 Found {total_files} audio files. Starting transcription...\n")

rows = []

# ---------- TRANSCRIPTION ----------
for i, filename in enumerate(files):
    path = os.path.join(INPUT_FOLDER, filename)

    try:
        result = model.transcribe(
            path,
            language="ne",
            fp16=False  # CPU-safe, no warnings
        )

        text = result["text"].strip()
        rows.append({
            "file": filename,
            "text": text
        })

        print(f"[{i+1}/{total_files}] ✔ Done: {filename}")

    except Exception as e:
        print(f"[{i+1}/{total_files}] ❌ Failed: {filename} | Error: {e}")

# ---------- SAVE CSV ----------
df = pd.DataFrame(rows)
df.to_csv(OUTPUT_CSV, index=False)

print(f"\n🎉 All done! Saved {len(rows)} rows to '{OUTPUT_CSV}'")
