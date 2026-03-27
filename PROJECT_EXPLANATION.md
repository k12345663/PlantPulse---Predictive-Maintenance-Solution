# PlantPulse AI — Complete Project Explanation

**Project:** PlantPulse AI — Predictive Maintenance Intelligence System  
**Stack:** Python · Streamlit · SQLite · scikit-learn · Ollama · Zhipu GLM · Google Gemini · OpenAI · fpdf2 · plotly  
**Status:** Production-Ready

---

## 1. What Is PlantPulse AI?

PlantPulse AI is a predictive maintenance platform for manufacturing plants. It reads technician maintenance logs, runs them through a multi-agent AI pipeline, calculates a risk score for every machine, predicts when each machine will fail, and recommends exactly what to repair — all in under 500ms.

The core idea: instead of waiting for a machine to break (reactive maintenance), the system detects deterioration patterns early and acts before failure happens (predictive maintenance).

**End-to-end flow:**
```
Technician writes log
        ↓
Log Analyzer classifies issue type
        ↓
Failure Predictor ML calculates 7-factor risk score + Isolation Forest anomaly
        ↓
Insights Engine detects plant-wide patterns
        ↓
Repair Recommender maps issue → component + cost + YouTube tutorials
        ↓
Scheduler generates urgency-sorted maintenance schedule
        ↓
LLM Comparison Engine queries 4 LLMs with same prompt, scores, picks best
        ↓
UI updates all pages in real-time (<500ms)
```

Every time a new log is added, the entire pipeline re-runs. No batch jobs. No overnight processing.

---

## 2. System Architecture — Multi-Agent Design

The system is built as a collection of specialized agents. Each agent has one job and does it well. They are orchestrated by `app.py` which initializes all agents on startup and passes data between them.

```
┌─────────────────────────────────────────────────────────────────┐
│                        app.py (Orchestrator)                    │
│                                                                 │
│  ┌─────────────────┐   ┌──────────────────────┐                │
│  │  LogAnalyzer    │   │  FailurePredictorML  │                │
│  │  Agent          │   │  Agent               │                │
│  └─────────────────┘   └──────────────────────┘                │
│  ┌─────────────────┐   ┌──────────────────────┐                │
│  │  InsightsEngine │   │  RepairRecommender   │                │
│  └─────────────────┘   └──────────────────────┘                │
│  ┌─────────────────┐   ┌──────────────────────┐                │
│  │  Urgent         │   │  LLMComparison       │                │
│  │  Scheduler      │   │  Engine              │                │
│  └─────────────────┘   └──────────────────────┘                │
│  ┌─────────────────┐                                           │
│  │  Assistant      │                                           │
│  │  Agent          │                                           │
│  └─────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

**Initialization in `app.py`:**
```python
log_analyzer = LogAnalyzerAgent(df)
failure_predictor = FailurePredictorMLAgent(df)
risk_data = failure_predictor.get_all_risk_scores()
scheduler = UrgentMaintenanceScheduler(risk_data, df)
assistant = AIAssistantAgent(log_analyzer, failure_predictor, scheduler)
insights_engine = InsightsEngine(df)
```

---

## 3. The Agents — How Each One Works

### 3.1 Log Analyzer Agent (`agents/log_analyzer.py`)

**Purpose:** Reads raw maintenance data and extracts structured patterns.

**Key methods:**
- `extract_patterns(machine_id)` — returns incident count, issue distribution, repeated issues, downtime totals, temporary fix count, critical incident count
- `get_machine_history(machine_id)` — returns last 10 logs, total incidents, issue types, total downtime, last incident date, temp fix count
- `search_logs(query)` — keyword search across technician notes and issue types
- `get_timeline_analysis(machine_id, days)` — incident count and trend for a time window

**How it classifies issues:** The data already has structured `issue_type` field (vibration, overheating, lubrication, electrical, mechanical, hydraulic). The Log Analyzer reads and aggregates these, finds repeated patterns (issues appearing 2+ times), and feeds structured data to all downstream agents.

**Repeated issue detection:**
```python
issue_counts = machine_logs['issue_type'].value_counts()
repeated_issues = issue_counts[issue_counts >= 2]  # 2+ occurrences = repeated
```

---

### 3.2 Failure Predictor ML Agent (`agents/failure_predictor_ml.py`)

**Purpose:** Calculates a 0–100 risk score for each machine using 7 weighted factors, runs Isolation Forest anomaly detection, and predicts failure window.

**Step 1 — Train Isolation Forest on startup:**
```python
features per machine:
  - incident_count
  - avg_downtime
  - temp_fix_ratio
  - critical_ratio
  - recent_incidents (last 7 days)
  - issue_diversity

→ StandardScaler normalizes features
→ IsolationForest(contamination=0.3).fit(feature_matrix)
```

**Step 2 — Calculate 7-Factor Risk Score:**

| Factor | Max Points | Logic |
|--------|-----------|-------|
| Recent incident frequency | 30 pts | incidents in last 30 days × 5, capped at 30 |
| Repeated issues | 25 pts | repeated issue types × 8, capped at 25 |
| Temporary fixes | 20 pts | temp fix count × 7, capped at 20 |
| Critical incidents | 15 pts | critical/high severity count × 5, capped at 15 |
| Total downtime | 10 pts | total_downtime_hours, capped at 10 |
| Recent acceleration | 10 pts | if 2+ incidents in last 7 days: incidents × 3 |
| ML anomaly boost | 10 pts | if Isolation Forest flags anomaly: confidence/10 |

**Total max = 120, capped at 100.**

**Risk level thresholds:**
- 0–29 → Low (green) → predicted failure: 4+ weeks
- 30–49 → Medium (yellow) → predicted failure: 2–4 weeks
- 50–69 → High (orange) → predicted failure: 1–2 weeks
- 70–100 → Critical (red) → predicted failure: 1–7 days

**Step 3 — Isolation Forest anomaly detection:**
```python
prediction = ml_model.predict(feature_scaled)  # -1 = anomaly, 1 = normal
anomaly_score = ml_model.score_samples(feature_scaled)
confidence = min(100, int(abs(anomaly_score) * 100))
```

**Important distinction:** ML Status (Isolation Forest) and Risk Level (rule-based score) are two independent indicators. A machine can be Low risk but still flagged as anomalous if its behavior pattern is unusual compared to other machines.

---

### 3.3 Insights Engine (`agents/insights_engine.py`)

**Purpose:** Detects plant-wide patterns and anomalies that individual machine analysis would miss.

**Anomaly detection — 4 types:**

1. **Incident Spike** — recent 7-day count > 1.5× weekly average → plant-wide alert
2. **New Issue Pattern** — machine showing an issue type it has never had before (compares last 2 logs vs historical)
3. **Weekend Pattern** — >20% of incidents on weekends → staffing/operations alert
4. **Rapid Deterioration** — 3 incidents within 7 days for same machine → critical alert

Each anomaly includes `machine_id` so repair recommendations and YouTube links appear inline where the alert is shown.

**Failure Cascade Prediction:**
```python
# Find machines on same production line
line_machines = df[df['production_line'] == prod_line]['machine_id'].unique()

# Calculate cascade risk per dependent machine
same_line_risk = 40       # base risk for same line
issue_correlation = 20    # if shared issue types
recent_issues = 15        # if 2+ incidents in last 30 days
cascade_probability = min(same_line_risk + issue_correlation + recent_issues, 85)
```

**Cost Impact Calculation (INR):**
- Downtime cost: total_downtime_hours × ₹42,000/hour
- Labor cost: incident_count × ₹1,500/incident
- Parts cost: parts_replaced_count × ₹5,000 average
- Prevented cost: temp_fix_count × 0.7 × ₹42,000 × 4 hours

**Maintenance Efficiency Score (0–100):**
Scores the maintenance team's performance. Positive: permanent fixes, inspections. Negative: temporary fixes, repeated issues, critical incidents.

**Smart Insights (4 auto-generated):**
- Peak failure hour (most incidents at which hour)
- Issue correlation (which issue type most often follows another)
- Response time opportunity (if avg downtime > 60 min)
- Production line variance (worst vs best line comparison)

---

### 3.4 Urgent Maintenance Scheduler (`agents/scheduler_urgent.py`)

**Purpose:** Generates a maintenance schedule sorted by urgency, with today's faults getting immediate priority.

**Algorithm:**

```
Step 1: Find today's faults
  today_faults = df[df['date'].dt.date == today]
  urgent_machines = today_faults['machine_id'].unique()

Step 2: Classify machines
  if machine in urgent_machines → priority_score = risk_score + 50 (URGENT boost)
  elif risk_score >= 50 → High priority
  elif risk_score >= 30 → Medium priority
  else → Low priority

Step 3: Sort each group by boosted score (descending)

Step 4: Generate time slots
  if current_hour < 18:
    urgent slots = today, next available hour, 2-hour intervals
  else:
    urgent slots = tomorrow 06:00, 2-hour intervals
  regular slots = weekday off-hours (18:00) + weekend slots (08:00, 14:00, 18:00)

Step 5: Assign machines to slots in priority order
```

**Recommended actions per machine** are generated by checking which issue types appear in that machine's history and mapping them to specific repair actions (e.g., vibration → "Inspect and replace bearings", "Check alignment and balance").

---

### 3.5 Repair Recommender (`agents/repair_recommender.py`)

**Purpose:** Maps issue type to a specific component, repair instructions, cost estimate, tools, safety precautions, and YouTube tutorial links.

**Issue → Component mapping:**

| Issue Type | Primary Component | Temp Fix | Permanent Fix | Cost (INR) | Time |
|------------|------------------|----------|---------------|-----------|------|
| Vibration | Bearing | Tighten bolts, check alignment | Replace worn bearings | ₹8,500 | 2 hrs |
| Overheating | Cooling Fan | Clean ventilation, reduce load | Replace cooling fan | ₹12,000 | 3 hrs |
| Lubrication | Oil Seal | Add lubricant, check level | Replace seals, change oil | ₹6,500 | 1.5 hrs |
| Electrical | Contactor | Tighten connections, reset breaker | Replace faulty contactor | ₹4,500 | 1 hr |
| Mechanical | Belt | Adjust belt tension | Replace worn belt | ₹3,200 | 0.5 hrs |
| Hydraulic | Hydraulic Pump | Check fluid level, bleed air | Replace pump or seals | ₹28,000 | 4 hrs |

Each entry also includes:
- All affected components (not just primary)
- Tools required list
- Safety precautions list
- 2 YouTube repair tutorial links with title, duration, and URL

**YouTube links appear where the problem is shown** — not in a separate page. They appear in:
- Visual Overview → "Machines Requiring Attention" expander
- Insights Dashboard → anomaly alerts (via machine_id)
- PDF Report → Section 6

---

### 3.6 LLM Comparison Engine (`agents/llm_comparison.py`)

**Purpose:** Queries 4 LLMs with the same maintenance prompt, scores each response on 5 dimensions, and picks the best recommendation.

**The 4 LLMs:**

| Model | Provider | Type | Avg Latency |
|-------|----------|------|-------------|
| qwen3:8b via Ollama | Open Source | Local, fully offline | ~8s |
| GLM-4.5-air | Zhipu AI | Cloud API | ~1.2s |
| Gemini-2.0-flash | Google | Cloud API | ~0.9s |
| GPT-3.5-turbo | OpenAI | Cloud API | ~1.5s |

**The prompt (identical for all 4 — fair comparison):**
```
Machine: {machine_id}
Issue Type: {issue_type}
Risk Score: {risk_score}/100 ({risk_level})
Recent Incidents (7 days): {recent_incidents}
Total Downtime: {downtime_minutes} minutes
Temporary Fixes Applied: {temp_fix_count}
Key Risk Factors: {top_factors}

Provide:
1. Root Cause Analysis
2. Immediate Action (next 24 hours)
3. Long-term Fix
4. Estimated Downtime for repair
5. Priority Level (Critical/High/Medium/Low)
6. Confidence in recommendation (%)
```

**Scoring — 5 dimensions × 20 pts = 100 max:**

| Dimension | Trigger Words | Points |
|-----------|--------------|--------|
| Root Cause | "cause", "root", "reason", "due to", "because" | 20 |
| Immediate Action | "immediate", "24 hour", "urgent", "now", "asap" | 20 |
| Long-term Fix | "long-term", "permanent", "replace", "overhaul" | 20 |
| Priority/Confidence | "priority", "critical", "high", "confidence", "%" | 20 |
| Adequate Length | 80+ words = 20pts, 40–79 words = 10pts | 20 |

**Best LLM selection:**
```python
speed_score = (1 - latency_ms / max_latency) * 100
combined_score = quality_score * 0.7 + speed_score * 0.3
best = max(results, key=lambda x: x['combined_score'])
```

**Demo fallback:** When APIs have quota/billing issues, the engine returns realistic pre-written demo responses with a "DEMO" badge. This ensures the comparison feature always works during presentations.

**Where results appear:**
- Dedicated LLM Comparison page (radar chart, bar charts, side-by-side text, scoring breakdown)
- Inline "Get AI Recommendation" button inside each problem machine card on Visual Overview

---

### 3.7 Assistant Agent (`agents/assistant.py`)

**Purpose:** Natural language Q&A about any machine or the plant overall.

**How it works:**
1. Parses the question for machine IDs mentioned
2. Gathers context: machine history, risk score, schedule
3. If Ollama is running → sends prompt + context to Ollama API
4. If Ollama is not running → falls back to rule-based responses

**Rule-based fallback covers:**
- "high risk" / "likely to fail" → lists top risk machines
- Machine ID mentioned → shows risk score, incidents, downtime, factors
- "schedule" / "when" → shows upcoming maintenance slots
- Default → shows what it can answer

**Ollama API call:**
```python
requests.post(
    f"{ollama_url}/api/generate",
    json={"model": ollama_model, "prompt": prompt, "stream": False},
    timeout=30
)
```

---

## 4. ML Algorithms

### 4.1 Isolation Forest (Primary Anomaly Detection)

Used in `FailurePredictorMLAgent` for detecting machines with unusual behavior patterns.

**How it works:**
- Builds random decision trees that recursively partition the feature space
- Anomalies are "isolated" in fewer splits because they are rare and different
- Normal points require many splits to isolate
- `contamination=0.3` means it expects ~30% of machines to be anomalous
- Output: -1 (anomaly) or 1 (normal), plus a score used for confidence %

**Features used:** incident_count, avg_downtime, temp_fix_ratio, critical_ratio, recent_incidents, issue_diversity

**Preprocessing:** StandardScaler normalizes all features before training.

### 4.2 6 ML Algorithms Benchmarked (ML Comparison Page)

The ML Comparison page trains and evaluates 6 algorithms on the same dataset and shows which performs best:

| Algorithm | Type | Key Characteristic |
|-----------|------|-------------------|
| Isolation Forest | Unsupervised | No labels needed, fast, production-ready |
| One-Class SVM | Unsupervised | Good for small datasets, kernel-based boundary |
| Local Outlier Factor | Unsupervised | Density-based, catches local anomalies |
| Random Forest | Supervised | High accuracy, feature importance, interpretable |
| Gradient Boosting | Supervised | Best overall accuracy, sequential error correction |
| Neural Network (MLP) | Supervised | Learns complex non-linear patterns |

**Metrics shown:** Accuracy, Precision, Recall, F1 Score, Training Time  
**Visualizations:** Bar chart comparison, radar chart, recommendation for production use

### 4.3 StandardScaler (Preprocessing)

All ML features are normalized using `StandardScaler` before training:
```python
feature_matrix = scaler.fit_transform(feature_df)
```
This ensures features with different scales (e.g., incident_count vs temp_fix_ratio) don't dominate the model.

---

## 5. AI Integration — How It All Connects

### 5.1 Real-Time Pipeline

When a new log is added via the "Add Log" page:
```python
# 1. Save to database
db.add_log(machine_id, issue_type, action_taken, ...)

# 2. Reload data
df_updated = load_data(db)

# 3. Re-initialize all agents with new data
predictor_updated = FailurePredictorMLAgent(df_updated)
risk_data_updated = predictor_updated.get_all_risk_scores()
scheduler_updated = UrgentMaintenanceScheduler(risk_data_updated, df_updated)

# 4. All pages now reflect updated risk scores
```

This entire cycle completes in under 500ms for 500 logs.

### 5.2 LLM Integration Points

**Ollama (local):**
- AI Assistant chat (always-on, no API cost)
- LLM Comparison (one of 4 models)

**Zhipu GLM API:**
- LLM Comparison only
- Endpoint: `https://open.bigmodel.cn/api/paas/v4/chat/completions`
- Model: `glm-4.5-air`

**Google Gemini API:**
- LLM Comparison only
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`

**OpenAI API:**
- LLM Comparison only
- Endpoint: `https://api.openai.com/v1/chat/completions`
- Model: `gpt-3.5-turbo`

All 4 LLMs receive the exact same `build_maintenance_prompt()` output. No model gets extra context. This makes the comparison fair.

### 5.3 PDF Generation Integration

When "Export Machine PDF Report" is clicked (from Dashboard or Logs page):
```python
predictor = FailurePredictorMLAgent(df)
risk_info = predictor.calculate_risk_score(machine_id)       # 7-factor score
fail_window = predictor.predict_failure_window(machine_id)   # failure window
repair_rec = RepairRecommender().get_repair_recommendation(most_common_issue)

pdf_bytes = generate_machine_pdf(
    machine_id, machine_logs_df, risk_info, repair_rec, fail_window
)
```

The PDF is generated in-memory using `fpdf2` and returned as bytes for `st.download_button`.

---

## 6. Platform Features — All 10 Pages

### Page 1: Visual Overview
- 2-row grid of machine cards (M1–M10), color-coded by risk level
- Each card shows: risk score, risk level, incident counts, predicted failure window, ML anomaly flag
- "Machines Requiring Attention" section (Critical + High machines):
  - 4 metrics: Total Incidents, Recent (7d), Predicted Failure, ML Status
  - Issue breakdown
  - Repair recommendation: component, cost, time, temp fix, permanent fix
  - YouTube repair tutorial links (2 per machine, inline)
  - "Get AI Recommendation" button → queries all 4 LLMs, shows results in tabs
  - Key risk factors
  - Recent maintenance log history (last 5 entries)
- Incident trend chart (last 30 days)
- Issue distribution bar chart

### Page 2: Insights Dashboard
- Plant-wide anomaly detection (up to 5 anomalies)
- Each anomaly shows: type, severity, description, recommendation
- Rapid deterioration and new issue pattern anomalies include machine_id → shows repair solution + YouTube links inline
- Failure cascade prediction: select a high-risk machine, see which other machines on the same production line are at risk
- Cost impact analysis in INR
- Maintenance efficiency score with grade (A+/A/B/C/D)
- Smart insights (4 auto-generated observations)
- Parts inventory prediction

### Page 3: ML Comparison
- Trains and benchmarks 6 ML algorithms on the current dataset
- Metrics table: Accuracy, Precision, Recall, F1, Training Time
- Bar chart comparison
- Radar chart (5-dimension)
- Recommendation for which algorithm to use in production

### Page 4: LLM Comparison
- Machine selector + issue type input
- Queries all 4 LLMs with same prompt
- Summary table: quality score, latency, word count, demo badge
- Bar charts: response quality, latency, verbosity
- Radar chart: 5-dimension comparison
- Side-by-side recommendation text in tabs
- Scoring breakdown per LLM
- Consensus recommendation (best LLM highlighted)

### Page 5: Dashboard
- 4 KPI metrics: Total Machines, High Risk Machines, Total Downtime, Total Incidents
- Risk distribution pie chart
- Issue type distribution bar chart
- Top 5 risk machines with expandable risk factors
- Machine PDF export: select any machine → generate → download full 9-section PDF

### Page 6: Maintenance Logs
- Searchable, filterable log table (filter by machine, issue type, keyword)
- Shows: machine_id, date, technician_note, issue_type, action_taken, downtime_minutes, criticality
- Export to CSV
- Export to PDF (only when specific machine selected, not "All")

### Page 7: Add Log
- Form: machine_id, issue_type, action_taken, downtime_minutes, criticality, technician_note, production_line
- On submit: saves to SQLite, reloads data, re-runs full AI pipeline
- Shows updated risk score immediately
- Pattern detection: if overheating + vibration in recent issues → motor bearing failure warning

### Page 8: Risk Analysis
- Color-coded risk table for all machines
- Risk score bar chart (color by risk level)
- Machine selector → detailed analysis:
  - Risk Score metric, Risk Level metric, Predicted Failure Window metric
  - Risk factors list

### Page 9: Schedule
- Auto-generated schedule tab: slider for days ahead (7–30), generates urgency-sorted schedule
- Each schedule item shows: machine_id, risk score, priority, scheduled time, estimated duration, production line, reason, recommended actions, urgency flag, ML-enhanced flag
- Manual scheduling tab

### Page 10: AI Assistant
- Chat interface
- Powered by Ollama (local LLM, runs offline)
- Answers questions about any machine, risk status, schedule
- Falls back to rule-based responses if Ollama is not running

---

## 7. PDF Report — 9 Sections

Generated by `utils/pdf_exporter.py` using `fpdf2`. Returns raw bytes for download.

| Section | Content |
|---------|---------|
| 1. Machine Summary | Risk badge (color-coded), production line, total incidents, total downtime, temp fix count, predicted failure window, report date |
| 2. Risk Factors | Bulleted list of all risk factors from 7-factor score |
| 3. ML Anomaly Detection | Anomaly status with confidence %, color-coded banner |
| 4. Repair Recommendation | Issue type, primary component, all components, cost in INR, repair time, temp fix, permanent fix, urgency |
| 5. Tools & Safety | Two-column layout: tools required vs safety precautions |
| 6. YouTube Tutorials | Video title, duration, URL for each tutorial |
| 7. Issue Breakdown | Table: issue type, count, % of total (alternating row colors) |
| 8. Complete Log History | Full table of all logs: date, issue type, action taken, downtime, criticality (color-coded), technician note |
| 9. Summary & Next Steps | 7 actionable steps with deadlines and cost estimates |

PDF has custom header (blue bar with machine ID) and footer (page number + timestamp) on every page.

---

## 8. Data

**Dataset:** 500 synthetic maintenance logs across 10 machines (M1–M10)

**Schema:**
```
machine_id        : M1–M10
date              : datetime
issue_type        : vibration | overheating | lubrication | electrical | mechanical | hydraulic
action_taken      : temporary_fix | permanent_fix | inspection | replacement
downtime_minutes  : integer
criticality       : Low | Medium | High | Critical
technician_note   : free text
production_line   : Line A | Line B | Line C
```

**Database:** SQLite via `database.py`. `MaintenanceDatabase` class handles all reads/writes. `get_all_logs()` returns a DataFrame. `add_log()` inserts new entries. `get_stats()` returns aggregate counts.

---

## 9. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| UI | Streamlit | All 10 pages, charts, forms, download buttons |
| Language | Python 3.10+ | All backend logic |
| Database | SQLite + pandas | Log storage and querying |
| ML | scikit-learn | Isolation Forest, SVM, LOF, RF, GB, MLP |
| Preprocessing | StandardScaler | Feature normalization before ML |
| Local LLM | Ollama (qwen3:8b) | AI Assistant + LLM Comparison |
| Cloud LLMs | Zhipu GLM, Gemini, OpenAI | LLM Comparison |
| PDF | fpdf2 | 9-section machine report generation |
| Charts | plotly | All interactive visualizations |
| HTTP | requests | All LLM API calls |

---

## 10. Key Technical Highlights

**Real-time learning:** Every new log triggers full pipeline re-run in <500ms. Risk scores, anomaly detection, and schedule all update instantly.

**Two independent AI signals:** Risk Level (rule-based 7-factor score) and ML Status (Isolation Forest) are separate. A machine can be Low risk but anomalous — meaning its pattern changed suddenly even if absolute numbers are low.

**Fair LLM comparison:** All 4 models receive identical prompts via `build_maintenance_prompt()`. No model gets extra context. Scoring is objective (keyword presence + length).

**Graceful degradation:** If Ollama is offline → Assistant uses rule-based responses. If cloud APIs fail → LLM Comparison shows demo responses with DEMO badge. PDF export works with no LLM at all.

**Component-level repair:** Not just "fix the machine" — the system tells you exactly which component to replace, what tools to use, what safety steps to follow, estimated cost in INR, estimated time, and links to YouTube tutorials.

**PDF in-memory:** PDF is generated as bytes in RAM and passed directly to `st.download_button`. No temp files written to disk.
