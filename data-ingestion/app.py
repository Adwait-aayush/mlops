import pandas as pd
import os
import json
import logging
import urllib.request
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OUTPUT_DIR  = "/app/shared/data"
DATA_PATH   = os.path.join(OUTPUT_DIR, "dataset.csv")
REPORT_PATH = os.path.join(OUTPUT_DIR, "ingestion_report.json")

#  SMS spam dataset 
DATASET_URL = "https://raw.githubusercontent.com/mohitgupta-omg/Kaggle-SMS-Spam-Collection-Dataset-/master/spam.csv"


def fetch_data():
    log.info("Downloading SMS spam dataset...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tmp_path = "/tmp/spam.csv"
    urllib.request.urlretrieve(DATASET_URL, tmp_path)

    
    raw = pd.read_csv(tmp_path, encoding="latin-1", usecols=[0, 1])
    raw.columns = ["label_text", "text"]

    raw["label_text"] = raw["label_text"].astype(str).str.strip().str.lower()
    raw["label"]      = raw["label_text"].map({"ham": 0, "spam": 1})
    raw["text"]       = raw["text"].astype(str)

    df = raw[["text", "label"]].copy()

    log.info(f"Fetched {len(df)} rows.")
    log.info(f"Spam: {int(df['label'].sum())} | Ham: {int((df['label'] == 0).sum())}")
    return df


def validate(df):
    log.info("Validating data...")
    checks = {
        "enough_rows":  bool(len(df) >= 500),
        "no_nulls":     bool(df.isnull().sum().sum() == 0),
        "both_classes": bool(df["label"].nunique() == 2),
    }
    passed = all(checks.values())
    log.info(f"Validation {'PASSED' if passed else 'FAILED'}: {checks}")
    return passed, checks


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df             = fetch_data()
    passed, checks = validate(df)

    if not passed:
        log.error("Validation failed. Stopping.")
        raise SystemExit(1)

  
    df = df.dropna()
    df = df[df["text"].str.strip().str.len() > 5].reset_index(drop=True)
    df.to_csv(DATA_PATH, index=False)
    log.info(f"Saved {len(df)} rows to {DATA_PATH}")

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "rows":      int(len(df)),
        "spam":      int(df["label"].sum()),
        "ham":       int((df["label"] == 0).sum()),
        "checks":    checks,
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    log.info("Ingestion complete.")
    log.info(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()