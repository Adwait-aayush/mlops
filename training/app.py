import pandas as pd
import pickle
import json
import os
import logging
from datetime import datetime
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATA_PATH    = "/app/shared/data/dataset.csv"
MODEL_DIR    = "/app/shared/models"
MODEL_PATH   = os.path.join(MODEL_DIR, "model.pkl")
REPORT_PATH  = os.path.join(MODEL_DIR, "training_report.json")


BASELINE_ACC = 0.80


def load_data():
    log.info("Loading dataset...")
    df = pd.read_csv(DATA_PATH).dropna()
    log.info(f"Loaded {len(df)} rows.")
    return df["text"].tolist(), df["label"].tolist()


def train(X_train, y_train):
    log.info("Training model...")
    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=10000,     
            stop_words="english",
            ngram_range=(1, 2),     
            min_df=2,              
            sublinear_tf=True     
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=5.0,                  
            solver="lbfgs"
        ))
    ])
    model.fit(X_train, y_train)
    log.info("Training done.")
    return model


def evaluate(model, X_test, y_test):
    preds = model.predict(X_test)
    acc   = accuracy_score(y_test, preds)
    log.info(f"Accuracy: {acc:.4f}")
    return round(acc, 4)


def save(model, acc):
    os.makedirs(MODEL_DIR, exist_ok=True)

    
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

   
    report = {
        "timestamp":   datetime.utcnow().isoformat(),
        "accuracy":    float(acc),
        "passed_gate": bool(acc >= BASELINE_ACC),
        "model_path":  MODEL_PATH
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    log.info(f"Model saved to {MODEL_PATH}")
    return report


def main():
    X, y = load_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model  = train(X_train, y_train)
    acc    = evaluate(model, X_test, y_test)
    report = save(model, acc)

    
    if not report["passed_gate"]:
        log.error(f"Accuracy {acc} is below baseline {BASELINE_ACC}. Failing.")
        raise SystemExit(1)

    log.info("Quality gate PASSED. Model is ready to serve.")


if __name__ == "__main__":
    main()