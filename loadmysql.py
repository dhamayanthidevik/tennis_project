import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus

load_dotenv()
pw = quote_plus(os.getenv("DB_PASSWORD"))
engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{pw}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

ORDER = ["categories", "competitions", "complexes", "venues",
         "competitors", "competitor_rankings"]

for t in ORDER:
    df = pd.read_csv(os.path.join("data", "clean", f"{t}.csv"))
    df.to_sql(t, engine, if_exists="append", index=False)
    print(f"{t}: loaded {len(df)} rows")