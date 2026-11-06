import json
import os
import pandas as pd

RAW_DIR = os.path.join("data", "raw")             
CSV_DIR = os.path.join("data", "csvfiles")        
os.makedirs(CSV_DIR, exist_ok=True)               

def load(name):
    path = os.path.join(RAW_DIR, f"raw_{name}.json")   
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ---------- 1) Categories + Competitions ----------
comp_rows, cat_rows = [], []
for c in load("competitions").get("competitions", []):
    cat = c.get("category") or {}
    cat_rows.append({"category_id": cat.get("id"),
                     "category_name": cat.get("name")})
    comp_rows.append({"competition_id": c.get("id"),
                      "competition_name": c.get("name"),
                      "parent_id": c.get("parent_id"),   # missing for some -> NaN (normal)
                      "type": c.get("type"),
                      "gender": c.get("gender"),
                      "level": c.get("level"),           # NEW: exists in JSON (731 rows)
                      "category_id": cat.get("id")})
categories = pd.DataFrame(cat_rows).dropna().drop_duplicates("category_id")
competitions = pd.DataFrame(comp_rows).drop_duplicates("competition_id")

# ---------- 2) Complexes + Venues ----------
cx_rows, ven_rows = [], []
for cx in load("complexes").get("complexes", []):
    cx_rows.append({"complex_id": cx.get("id"),
                    "complex_name": cx.get("name")})
    for v in cx.get("venues", []):                       # 'venues' missing in 161 complexes
        ven_rows.append({"venue_id": v.get("id"),
                         "venue_name": v.get("name"),
                         "city_id": v.get("city_id"),    # NEW: exists in JSON
                         "city_name": v.get("city_name"),
                         "country_name": v.get("country_name"),
                         "country_code": v.get("country_code"),
                         "timezone": v.get("timezone"),
                         "complex_id": cx.get("id")})
complexes = pd.DataFrame(cx_rows).drop_duplicates("complex_id")
venues = pd.DataFrame(ven_rows).drop_duplicates("venue_id")

# ---------- 3) Competitors + Competitor_Rankings ----------
cp_rows, rk_rows = [], []
for group in load("doubles_rankings").get("rankings", []):
    # group-level fields: name (ATP/WTA), gender, year, week, type_id
    for item in group.get("competitor_rankings", []):
        p = item.get("competitor") or {}
        cp_rows.append({"competitor_id": p.get("id"),
                        "name": p.get("name"),
                        "country": p.get("country"),
                        "country_code": p.get("country_code"),  # missing for some -> NaN
                        "abbreviation": p.get("abbreviation")})
        rk_rows.append({"rank": item.get("rank"),
                        "movement": item.get("movement", 0),
                        "points": item.get("points"),
                        "competitions_played": item.get("competitions_played"),
                        "competitor_id": p.get("id"),
                        "tour": group.get("name"),      # NEW: ATP / WTA
                        "gender": group.get("gender"),  # NEW
                        "year": group.get("year"),      # NEW
                        "week": group.get("week")})     # NEW
competitors = pd.DataFrame(cp_rows).drop_duplicates("competitor_id")
rankings = pd.DataFrame(rk_rows)

# ---------- Save + quick check ----------
tables = {"categories": categories, "competitions": competitions,
          "complexes": complexes, "venues": venues,
          "competitors": competitors, "competitor_rankings": rankings}
for name, df in tables.items():
    df.to_csv(os.path.join(CSV_DIR, f"{name}.csv"), index=False)
    print(f"{name:22s} rows={len(df):5d}  nulls={int(df.isna().sum().sum())}")
    

# Check Null values in the tablesimport pandas as pd
for t in ["competitions", "competitors"]:
    df = pd.read_csv(f"{t}.csv")
    print(t); print(df.isna().sum()[df.isna().sum() > 0], "\n")