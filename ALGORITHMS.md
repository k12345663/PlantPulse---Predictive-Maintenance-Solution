# Algorithms — PlantPulse AI

## 1. Risk Scoring Algorithm (7-Factor Weighted)

**File:** `agents/failure_predictor_ml.py` → `calculate_risk_score()`

Each machine gets a score 0–100 built from 7 independent factors:

| # | Factor | Max Points | Logic |
|---|--------|-----------|-------|
| 1 | Recent incident frequency | 30 | incidents in last 30 days × 5, capped at 30 |
| 2 | Repeated issues | 25 | unique repeated issue types × 8, capped at 25 |
| 3 | Temporary fixes | 20 | temp fix count × 7, capped at 20 |
| 4 | Critical incidents | 15 | high/critical severity count × 5, capped at 15 |
| 5 | Total downtime | 10 | total downtime hours, capped at 10 |
| 6 | Recent acceleration | 10 | incidents in last 7 days × 3 (only if > 2) |
| 7 | ML anomaly boost | 10 | Isolation Forest confidence / 10 |

**Risk Levels:**
- Critical: ≥ 70
- High: 50–69
- Medium: 30–49
- Low: < 30

---

## 2. ML Anomaly Detection — Isolation Forest

**File:** `agents/failure_predictor_ml.py` → `_train_anomaly_detector()` / `detect_ml_anomalies()`

**Model:** `sklearn.ensemble.IsolationForest` (contamination=0.3)

**Feature vector per machine (6 features):**
```
incident_count       — total log entries
avg_downtime         — mean downtime in minutes
temp_fix_ratio       — temporary fixes / total incidents
critical_ratio       — high+critical incidents / total
recent_incidents     — incidents in last 7 days
issue_diversity      — count of unique issue types
```

**Flow:**
1. Features extracted for all machines → StandardScaler normalizes
2. IsolationForest trained on all machines
3. Per-machine prediction: `-1` = anomaly, `1` = normal
4. `score_samples()` gives raw anomaly score → converted to 0–100 confidence
5. If anomaly detected → adds up to 10 points to risk score + flags `ml_anomaly: True`

**Key property:** ML Status and Risk Level are independent. A machine can be Critical risk but ML Normal (high incidents but expected pattern), or Low risk but ML Anomaly (unusual behavior even with few incidents).

---

## 3. Urgent Priority Scheduling Algorithm

**File:** `agents/scheduler_urgent.py` → `generate_schedule()`

**Steps:**
1. Identify today's faults from logs (date == today)
2. Boost their risk score by +50 points → guaranteed top priority
3. Sort all machines into three buckets: High (≥50), Medium (30–49), Low (<30)
4. Generate time slots — urgent slots first (next available hour today, or 06:00 tomorrow if after 18:00)
5. Weekend slots: 08:00, 14:00, 18:00 — weekday slots: 18:00 off-hours
6. Assign slots: URGENT → High → Medium → Low

**Output per scheduled item:** machine_id, risk_score, priority, scheduled_time, estimated_duration, reason, recommended_actions, urgency_flag

---

## 4. Failure Window Prediction

**File:** `agents/failure_predictor_ml.py` → `predict_failure_window()`

Simple threshold mapping on risk score:

| Risk Score | Predicted Window | Urgency |
|-----------|-----------------|---------|
| ≥ 70 | 1–7 days | Immediate |
| 50–69 | 1–2 weeks | High |
| 30–49 | 2–4 weeks | Medium |
| < 30 | 4+ weeks | Low |

---

## 5. Failure Cascade Prediction

**File:** `agents/insights_engine.py` → `predict_failure_cascade()`

When a machine is selected:
1. Find its production line
2. Find all other machines on the same line
3. For each dependent machine calculate cascade probability:
   - Base: 40 (same production line)
   - +20 if shared issue types with failing machine
   - +15 if > 2 incidents in last 30 days
4. Cap at 85%, return top 3 sorted by probability

---

## 6. Maintenance Efficiency Score

**File:** `agents/insights_engine.py` → `calculate_maintenance_efficiency_score()`

```
score = 50 (base)
+ (permanent_fixes / total) × 20
+ (inspections / total) × 15
- (temp_fixes / total) × 15
- (repeated_issues / total) × 10
- (critical_incidents / total) × 10
```
Clamped to 0–100. Grades: A+ (≥85), A (≥75), B (≥65), C (≥50), D (<50)

---

## 7. LLM Quality Scoring

**File:** `agents/llm_comparison.py` → `_score_response()`

Each LLM response scored on 5 criteria (20 pts each = 100 max):

| Criterion | Keywords checked |
|-----------|----------------|
| Root Cause | "cause", "root", "reason", "due to", "because" |
| Immediate Action | "immediate", "24 hour", "urgent", "now", "asap" |
| Long-term Fix | "long-term", "permanent", "replace", "overhaul" |
| Priority/Confidence | "priority", "critical", "high", "confidence", "%" |
| Response Length | ≥80 words = 20pts, ≥40 words = 10pts |

**Best LLM selection:** `quality_score × 0.7 + speed_score × 0.3`

---

## 8. Log Pattern Analysis

**File:** `agents/log_analyzer.py` → `extract_patterns()` / `_find_repeated_issues()`

- Keyword search across `technician_note` and `issue_type` fields
- Repeated issue detection: any issue type appearing ≥ 2 times per machine
- Timeline analysis: incident count over configurable day window, trend = "increasing" if count > 3

---

## 9. Anomaly Detection (Rule-Based, Insights Engine)

**File:** `agents/insights_engine.py` → `detect_anomalies()`

Four rule-based anomaly checks run on every page load:

1. **Incident spike** — last 7 days > 1.5× weekly average
2. **New issue pattern** — machine shows issue type not seen in its historical logs
3. **Weekend pattern** — weekend incidents > 20% of total
4. **Rapid deterioration** — 3 incidents within 7 days for same machine

---

## 10. Cost Impact Calculation

**File:** `agents/insights_engine.py` → `calculate_cost_impact()`

```
cost_per_hour = ₹42,000 (Indian manufacturing average)
labor_per_incident = ₹1,500
parts_avg = ₹5,000

downtime_cost = total_downtime_hours × 42,000
labor_cost = incident_count × 1,500
parts_cost = parts_replaced_count × 5,000
total_cost = downtime_cost + labor_cost + parts_cost

prevented_cost = temp_fix_count × 0.7 × 42,000 × 4
ROI = prevented_cost / total_cost × 100
```
