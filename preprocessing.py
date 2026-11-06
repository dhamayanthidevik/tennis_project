import os
import pandas as pd

CSV_DIR = os.path.join("data", "csvfiles")        
CLEAN_DIR = os.path.join("data", "clean")         
os.makedirs(CLEAN_DIR, exist_ok=True)             

# Fill missing values only in NOT NULL columns, and report how many
FILL = {
    "competitions": {"type": "unknown", "gender": "unknown"},
    "venues": {"city_name": "Unknown", "country_name": "Unknown",
               "country_code": "UNK", "timezone": "Unknown"},
    "competitors": {"country": "Unknown", "country_code": "NEU",
                    "abbreviation": "UNK"},
}

# Columns that exist in the CSV but not in your MySQL tables
DROP = {
    "competitions": ["level"],
    # "competitor_rankings": ["tour", "gender", "year", "week"],  
}

TABLES = ["categories", "competitions", "complexes", "venues",
          "competitors", "competitor_rankings"]

for t in TABLES:
    df = pd.read_csv(os.path.join(CSV_DIR, f"{t}.csv"))            
    df = df.drop(columns=DROP.get(t, []), errors="ignore")

    for col, val in FILL.get(t, {}).items():
        n = int(df[col].isna().sum())
        if n:
            print(f"{t}.{col}: filled {n} missing values with '{val}'")
            df[col] = df[col].fillna(val)

    df.to_csv(os.path.join(CLEAN_DIR, f"{t}.csv"), index=False)    
    print(f"{t}: saved {len(df)} rows to {CLEAN_DIR}/{t}.csv")     