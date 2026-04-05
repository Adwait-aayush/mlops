import pickle
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

MODEL_PATH = "/app/shared/models/model.pkl"

app    = FastAPI(title="Spam Classifier API")
model  = None

# Allow the React dashboard to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Load model on startup ----------
@app.on_event("startup")
def load_model():
    global model
    if not os.path.exists(MODEL_PATH):
        log.error(f"Model not found at {MODEL_PATH}")
        raise RuntimeError("Model file missing. Run training first.")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    log.info("Model loaded successfully.")


# ---------- Request / Response shapes ----------
class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    text:       str
    prediction: str        # "spam" or "not spam"
    confidence: float      # how confident the model is


# ---------- Routes ----------
@app.get("/health")
def health():
    """Jenkins and monitoring use this to check if the service is up."""
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")

    prediction  = model.predict([req.text])[0]
    confidence  = max(model.predict_proba([req.text])[0])
    label       = "spam" if prediction == 1 else "not spam"

    log.info(f"Prediction: {label} (confidence: {confidence:.2f}) for: {req.text[:50]}")

    return PredictResponse(
        text        = req.text,
        prediction  = label,
        confidence  = round(float(confidence), 4)
    )


@app.get("/model-info")
def model_info():
    """Returns basic info about the loaded model."""
    import json
    report_path = "/app/shared/models/training_report.json"
    if os.path.exists(report_path):
        with open(report_path) as f:
            return json.load(f)
    return {"info": "No training report found."}