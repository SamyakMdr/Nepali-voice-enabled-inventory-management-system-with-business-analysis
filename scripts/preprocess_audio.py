import os
import librosa
import soundfile as sf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DIR = os.path.join(BASE_DIR, "voice_dataset")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed_audio")

os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_SR = 16000

for filename in os.listdir(INPUT_DIR):
    if not filename.lower().endswith(".wav"):
        continue

    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)

    try:
        # Load audio as mono, 16kHz
        audio, sr = librosa.load(input_path, sr=TARGET_SR, mono=True)

        # Trim silence
        audio, _ = librosa.effects.trim(audio, top_db=20)

        # Save processed audio
        sf.write(output_path, audio, TARGET_SR)

        print(f"✔ Processed: {filename}")

    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")

print("\n✅ Preprocessing completed.")