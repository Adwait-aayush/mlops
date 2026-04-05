import requests
import json
import os
import time
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Where the serving service lives (container name in docker-compose)
SERVING_URL     = os.getenv("SERVING_URL", "http://serving:8000")
REPORT_PATH     = "/app/shared/monitoring/report.json"
CHECK_INTERVAL  = 15       # seconds between each check
MIN_CONFIDENCE  = 0.55     # if avg confidence drops below this → unhealthy

app = FastAPI(title="Monitoring Service")

# Allow the React dashboard to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store of recent checks
recent_checks = []


# ---------- Test samples ----------
# These are sent to the serving service to check it's working correctly
TEST_SAMPLES = [
    {"text": "WINNER! You have been selected for a cash prize of 1000 pounds. Call now!", "expected": "spam"},
    {"text": "Free entry in 2 a weekly competition to win FA Cup final tickets",           "expected": "spam"},
    {"text": "Hey I will be late for dinner, save me some food please",                    "expected": "not spam"},
    {"text": "Are you coming to the match tonight? Let me know what time",                 "expected": "not spam"},
]


def check_serving():
    """Send test samples to serving, record confidence scores."""
    results = []

    for sample in TEST_SAMPLES:
        try:
            res = requests.post(
                f"{SERVING_URL}/predict",
                json={"text": sample["text"]},
                timeout=5
            )
            if res.status_code == 200:
                data = res.json()
                results.append({
                    "text":       sample["text"],
                    "expected":   sample["expected"],
                    "got":        data["prediction"],
                    "confidence": data["confidence"],
                    "correct":    data["prediction"] == sample["expected"]
                })
        except Exception as e:
            log.warning(f"Could not reach serving: {e}")

    return results


def save_report(results, healthy):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    report = {
        "timestamp":    datetime.utcnow().isoformat(),
        "healthy":      healthy,
        "total_checks": len(results),
        "correct":      sum(r["correct"] for r in results),
        "avg_confidence": round(
            sum(r["confidence"] for r in results) / len(results), 4
        ) if results else 0,
        "results": results
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    return report


def monitor_loop():
    """Runs forever in background — checks serving every N seconds."""
    log.info("Monitor loop started.")
    while True:
        results = check_serving()

        if results:
            avg_conf    = sum(r["confidence"] for r in results) / len(results)
            accuracy    = sum(r["correct"] for r in results) / len(results)
            healthy     = avg_conf >= MIN_CONFIDENCE

            report = save_report(results, healthy)
            recent_checks.append(report)

            # Keep only last 20 checks in memory
            if len(recent_checks) > 20:
                recent_checks.pop(0)

            status = "✅ HEALTHY" if healthy else "❌ UNHEALTHY"
            log.info(f"{status} | accuracy={accuracy:.2f} | avg_confidence={avg_conf:.2f}")
        else:
            log.warning("No results — serving may be down.")

        time.sleep(CHECK_INTERVAL)


# ---------- Routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    """Jenkins calls this to decide rollback or full rollout."""
    if not recent_checks:
        return {"healthy": None, "message": "No checks done yet."}
    latest = recent_checks[-1]
    return {
        "healthy":          latest["healthy"],
        "avg_confidence":   latest["avg_confidence"],
        "correct":          latest["correct"],
        "total":            latest["total_checks"],
        "timestamp":        latest["timestamp"]
    }


@app.get("/history")
def history():
    """Full history of all checks — shown on the dashboard."""
    return {"checks": recent_checks}


# ---------- Start background monitor on startup ----------
@app.on_event("startup")
def start_monitor():
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    log.info("Background monitor thread started.")