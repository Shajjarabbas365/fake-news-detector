import time
from transformers import pipeline

print("🚀 'Ziddi' Downloader Shuru ho raha hai...")
print("Ab agar internet band bhi hua, to ye crash nahi hoga, balkay wahi se dobara shuru karega!")

koshish = 1
success = False

while not success:
    try:
        print(f"\n--- Koshish #{koshish} ---")
        # pipeline function automatically adhi downloaded file ko detect karke aage se shuru karta hai
        ai_detector = pipeline("text-classification", model="hamzab/roberta-fake-news-classification")
        success = True
        print("\n✅ Mubarrak ho! Model 100% Download ho gaya hai!!")
        
    except Exception as e:
        print(f"⚠️ Internet ka jhatka laga. Tension nahi, 3 second mein wahi se resume kar raha hoon...")
        koshish += 1
        time.sleep(3)