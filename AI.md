# AI Integration — PlantPulse AI

## Overview

PlantPulse AI uses a multi-agent architecture with 3 layers of AI:
1. **ML layer** — scikit-learn Isolation Forest for anomaly detection
2. **LLM comparison layer** — 6 models queried in parallel for maintenance recommendations
3. **Chat assistant layer** — qwen3:8b via Ollama for natural language Q&A

---

## Models in Use

| Model | Provider | Purpose | File |
|-------|----------|---------|------|
| Isolation Forest | scikit-learn (local) | Anomaly detection on machine behavior | `failure_predictor_ml.py` |
| qwen3:8b | Ollama (local) | AI Assistant chat | `assistant.py` |
| MiniMax-M2 | minimax-m2.7:cloud via Ollama | LLM Comparison | `llm_comparison.py` |
| DeepSeek-V3 | deepseek-v3.2:cloud via Ollama | LLM Comparison | `llm_comparison.py` |
| GLM-5 | glm-5:cloud via Ollama | LLM Comparison | `llm_comparison.py` |
| Kimi-K2 | kimi-k2.5:cloud via Ollama | LLM Comparison | `llm_comparison.py` |
| Qwen3-Next | qwen3-next via Ollama | LLM Comparison | `llm_comparison.py` |
| Gemini 2.0 Flash | Google API | LLM Comparison (demo fallback) | `llm_comparison.py` |
| GPT-3.5 Turbo | OpenAI API | LLM Comparison (demo fallback) | `llm_comparison.py` |

---

## Agent Architecture

```
PlantPulse AI
├── LogAnalyzerAgent          — pattern extraction, keyword search, timeline analysis
├── FailurePredictorMLAgent   — 7-factor risk scoring + Isolation Forest anomaly detection
├── UrgentMaintenanceScheduler — priority scheduling with today's fault boosting
├── InsightsEngine            — anomaly alerts, cascade prediction, cost analysis, smart insights
├── AIAssistantAgent          — natural language Q&A via Ollama (qwen3:8b)
├── LLMComparisonEngine       — 6-model parallel comparison with collective synthesis
├── RepairRecommender         — issue-to-repair mapping with YouTube tutorial links
└── MLComparisonAgent         — side-by-side ML algorithm comparison (Random Forest vs Isolation Forest)
```

---

## LLM Comparison Engine

**File:** `agents/llm_comparison.py`

### How it works

1. User selects a machine on the LLM Comparison page
2. One prompt is built from machine data (risk score, issue type, incidents, downtime, temp fixes, top factors)
3. All 6 models are queried **simultaneously** via `ThreadPoolExecutor`
4. Each response is scored on 5 criteria (0–100)
5. Best model selected by: `quality × 0.7 + speed × 0.3`
6. Collective recommendation synthesized algorithmically (no extra LLM call)

### Parallel execution
```python
with ThreadPoolExecutor(max_workers=len(self.llms)) as executor:
    futures = {executor.submit(query_llm, llm): llm for llm in self.llms}
    for future in as_completed(futures):
        llm, result = future.result()
```

### Model availability
- Ollama cloud models: only added to comparison if `ollama list` shows them pulled
- Cloud APIs (Gemini, OpenAI): always included, fall back to demo responses on quota errors
- Demo responses: pre-written realistic answers that still score correctly on quality rubric

### Collective recommendation (no extra LLM call)
- Priority: majority vote across all model responses
- Confidence: regex-extracted average from all responses
- Top actions: keyword frequency count across all response texts
- Agreement level: variance in quality scores

---

## ML Anomaly Detection

**File:** `agents/failure_predictor_ml.py`

### Training
- Runs once at startup on all machines
- 6 behavioral features per machine → StandardScaler → IsolationForest (contamination=0.3)
- Minimum 3 machines required to train

### Inference
- Per-machine feature vector → scaler.transform → model.predict
- `-1` = anomaly, `1` = normal
- `score_samples()` → raw score → confidence 0–100

### Independence from Risk Score
ML Status and Risk Level are two separate indicators:
- Risk Score = rule-based weighted formula (7 factors)
- ML Status = unsupervised pattern comparison against all other machines
- A machine can be Critical risk + ML Normal (many incidents but expected pattern)
- A machine can be Low risk + ML Anomaly (few incidents but unusual behavior pattern)

---

## AI Assistant

**File:** `agents/assistant.py`

- Default model: `qwen3:8b` via Ollama (local, no API key needed)
- Supports OpenAI and Gemini as alternative providers via `.env`
- Context injection: machine history, risk scores, schedule data injected into prompt before LLM call
- Fallback: rule-based keyword routing if Ollama not running

### Context gathering flow
```
user question
    → extract machine ID if mentioned
    → pull machine history + risk score
    → pull all high-risk machines
    → pull current schedule
    → inject into prompt
    → send to qwen3:8b
    → return response
```

---

## GenAI Validator

**File:** `agents/genai_validator.py`

Validates LLM responses before displaying:
- Checks response is non-empty
- Checks minimum word count
- Checks required sections present (root cause, immediate action, priority)
- Returns validation status + warnings

---

## Real-Time Learning

The system updates in < 500ms when new logs are added:
- New log added via "Add New Log" page → written to SQLite
- `load_data()` re-reads from DB
- `initialize_agents()` re-runs with fresh DataFrame
- All risk scores, anomaly detection, and schedules recalculate
- No model retraining needed for rule-based components
- Isolation Forest retrains on next app initialization

---

## API Keys & Configuration

**File:** `.env`

```
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
```

Ollama cloud models require:
```bash
ollama pull minimax-m2.7:cloud
ollama pull deepseek-v3.2:cloud
ollama pull glm-5:cloud
ollama pull kimi-k2.5:cloud
ollama pull qwen3:8b
```

---

## Where AI Appears in the UI

| Page | AI Feature |
|------|-----------|
| Visual Overview | Inline "Get AI Recommendation" button per problem machine — queries all models, shows collective summary + tabs |
| Insights Dashboard | Anomaly alerts with machine-specific repair recommendations |
| LLM Comparison | Full 6-model comparison with charts, radar, side-by-side responses, collective recommendation |
| ML Comparison | Isolation Forest vs Random Forest algorithm comparison |
| Risk Analysis | ML anomaly flag per machine |
| Schedule | ML-enhanced flag on scheduled items |
| Dashboard | PDF export includes ML status and AI recommendation |
| AI Assistant | Natural language chat powered by qwen3:8b |
