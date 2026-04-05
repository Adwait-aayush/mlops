import React, { useState, useEffect } from "react";

const SERVING_URL    = "http://localhost:8000";
const MONITORING_URL = "http://localhost:8001";

// ── Simple styles ───────────────────────────────────────────────
const styles = {
  app: {
    fontFamily: "monospace",
    backgroundColor: "#0f172a",
    color: "#e2e8f0",
    minHeight: "100vh",
    padding: "24px",
  },
  header: {
    fontSize: "24px",
    fontWeight: "bold",
    color: "#38bdf8",
    marginBottom: "8px",
  },
  subtitle: {
    color: "#64748b",
    marginBottom: "32px",
    fontSize: "14px",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "16px",
    marginBottom: "24px",
  },
  card: {
    backgroundColor: "#1e293b",
    borderRadius: "8px",
    padding: "20px",
    border: "1px solid #334155",
  },
  cardTitle: {
    fontSize: "12px",
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: "1px",
    marginBottom: "8px",
  },
  cardValue: {
    fontSize: "28px",
    fontWeight: "bold",
    color: "#f1f5f9",
  },
  badge: (healthy) => ({
    display: "inline-block",
    padding: "4px 12px",
    borderRadius: "20px",
    fontSize: "13px",
    fontWeight: "bold",
    backgroundColor: healthy ? "#14532d" : "#7f1d1d",
    color: healthy ? "#4ade80" : "#f87171",
  }),
  input: {
    width: "100%",
    padding: "10px",
    backgroundColor: "#0f172a",
    border: "1px solid #334155",
    borderRadius: "6px",
    color: "#e2e8f0",
    fontSize: "14px",
    marginBottom: "10px",
    boxSizing: "border-box",
  },
  button: {
    padding: "10px 24px",
    backgroundColor: "#0284c7",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "bold",
  },
  resultBox: (prediction) => ({
    marginTop: "16px",
    padding: "16px",
    borderRadius: "6px",
    backgroundColor: prediction === "spam" ? "#7f1d1d" : "#14532d",
    border: `1px solid ${prediction === "spam" ? "#f87171" : "#4ade80"}`,
  }),
  historyItem: (healthy) => ({
    padding: "8px 12px",
    borderRadius: "4px",
    marginBottom: "6px",
    backgroundColor: healthy ? "#14532d33" : "#7f1d1d33",
    borderLeft: `3px solid ${healthy ? "#4ade80" : "#f87171"}`,
    fontSize: "13px",
  }),
  sectionTitle: {
    fontSize: "16px",
    fontWeight: "bold",
    color: "#94a3b8",
    marginBottom: "12px",
    marginTop: "24px",
  },
};

export default function App() {
  const [modelInfo,   setModelInfo]   = useState(null);
  const [status,      setStatus]      = useState(null);
  const [history,     setHistory]     = useState([]);
  const [inputText,   setInputText]   = useState("");
  const [prediction,  setPrediction]  = useState(null);
  const [loading,     setLoading]     = useState(false);

  // ── Fetch data every 10 seconds ─────────────────────────────
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 10000);
    return () => clearInterval(interval);
  }, []);

  async function fetchAll() {
    try {
      const [infoRes, statusRes, histRes] = await Promise.all([
        fetch(`${SERVING_URL}/model-info`),
        fetch(`${MONITORING_URL}/status`),
        fetch(`${MONITORING_URL}/history`),
      ]);
      setModelInfo(await infoRes.json());
      setStatus(await statusRes.json());
      const h = await histRes.json();
      setHistory(h.checks || []);
    } catch (e) {
      console.error("Fetch error:", e);
    }
  }

  async function handlePredict() {
    if (!inputText.trim()) return;
    setLoading(true);
    setPrediction(null);
    try {
      const res  = await fetch(`${SERVING_URL}/predict`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ text: inputText }),
      });
      const data = await res.json();
      setPrediction(data);
    } catch (e) {
      console.error("Predict error:", e);
    }
    setLoading(false);
  }

  // ── Render ───────────────────────────────────────────────────
  return (
    <div style={styles.app}>
      <div style={styles.header}>🤖 MLOps Platform Dashboard</div>
      <div style={styles.subtitle}>
        Live model monitoring · Spam Classifier · Auto-refreshes every 10s
      </div>

      {/* ── Stats Row ── */}
      <div style={styles.grid}>
        <div style={styles.card}>
          <div style={styles.cardTitle}>Model Accuracy</div>
          <div style={styles.cardValue}>
            {modelInfo?.accuracy ? `${(modelInfo.accuracy * 100).toFixed(1)}%` : "—"}
          </div>
        </div>

        <div style={styles.card}>
          <div style={styles.cardTitle}>Model Status</div>
          <div style={{ marginTop: "4px" }}>
            {status?.healthy != null
              ? <span style={styles.badge(status.healthy)}>
                  {status.healthy ? "✅ Healthy" : "❌ Unhealthy"}
                </span>
              : "—"}
          </div>
        </div>

        <div style={styles.card}>
          <div style={styles.cardTitle}>Avg Confidence</div>
          <div style={styles.cardValue}>
            {status?.avg_confidence ? `${(status.avg_confidence * 100).toFixed(1)}%` : "—"}
          </div>
        </div>

        <div style={styles.card}>
          <div style={styles.cardTitle}>Last Trained</div>
          <div style={{ fontSize: "14px", marginTop: "4px", color: "#94a3b8" }}>
            {modelInfo?.timestamp
              ? new Date(modelInfo.timestamp).toLocaleString()
              : "—"}
          </div>
        </div>
      </div>

      {/* ── Predict ── */}
      <div style={styles.card}>
        <div style={styles.sectionTitle}>🔍 Try a Prediction</div>
        <textarea
          style={{ ...styles.input, height: "80px", resize: "vertical" }}
          placeholder="Type any text here and click Predict..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        />
        <button style={styles.button} onClick={handlePredict} disabled={loading}>
          {loading ? "Predicting..." : "Predict"}
        </button>

        {prediction && (
          <div style={styles.resultBox(prediction.prediction)}>
            <div style={{ fontWeight: "bold", fontSize: "18px", marginBottom: "6px" }}>
              {prediction.prediction === "spam" ? "🚨 SPAM" : "✅ NOT SPAM"}
            </div>
            <div style={{ fontSize: "13px", color: "#94a3b8" }}>
              Confidence: {(prediction.confidence * 100).toFixed(1)}%
            </div>
          </div>
        )}
      </div>

      {/* ── Monitor History ── */}
      <div style={styles.sectionTitle}>📊 Monitoring History</div>
      {history.length === 0 && (
        <div style={{ color: "#64748b", fontSize: "14px" }}>
          No checks yet. Monitoring runs every 15 seconds.
        </div>
      )}
      {[...history].reverse().slice(0, 8).map((check, i) => (
        <div key={i} style={styles.historyItem(check.healthy)}>
          <span style={{ color: check.healthy ? "#4ade80" : "#f87171" }}>
            {check.healthy ? "✅ Healthy" : "❌ Unhealthy"}
          </span>
          {"  "}
          Accuracy: {check.correct}/{check.total_checks}
          {"  ·  "}
          Confidence: {(check.avg_confidence * 100).toFixed(1)}%
          {"  ·  "}
          <span style={{ color: "#475569" }}>
            {new Date(check.timestamp).toLocaleTimeString()}
          </span>
        </div>
      ))}
    </div>
  );
}