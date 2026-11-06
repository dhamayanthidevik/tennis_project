import os, time, json, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SPORTRADAR_KEY")
BASE = "https://api.sportradar.com/tennis/trial/v3/en"

RAW_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)   

FEEDS = {
    "competitions": "competitions",
    "complexes": "complexes",
    "doubles_rankings": "double_competitors_rankings",
}

for name, path in FEEDS.items():
    out = os.path.join(RAW_DIR, f"raw_{name}.json")
    if os.path.exists(out):
        print(name, "already saved, skipping")
        continue
    time.sleep(1.5)                       # respect 1 call/second
    r = requests.get(f"{BASE}/{path}.json",
                     headers={"x-api-key": API_KEY}, timeout=30)
    print(name, "->", r.status_code)
    r.raise_for_status()
    with open(out, "w", encoding="utf-8") as f:
       json.dump(r.json(),f, indent=2)
    print("   top-level keys:", list(r.json().keys()))