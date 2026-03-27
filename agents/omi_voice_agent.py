"""Omi Dimension AI — Voice Agent Integration for PlantPulse"""

import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

OMI_API_KEY = os.getenv("OMI_API_KEY", "")


def build_context_breakdown(risk_data, df, schedule=None):
    """
    Build full context_breakdown with 100% live machine data.
    Includes: per-machine risk, ML anomaly, failure window, incident history,
    repair actions, cascade map, schedule, and cost summary.
    """
    now = datetime.now()

    # ── Per-machine full detail ───────────────────────────────────────────────
    machine_lines = []
    for r in risk_data:
        mid        = r['machine_id']
        logs       = df[df['machine_id'] == mid]
        recent_7d  = len(logs[logs['date'] >= now - timedelta(days=7)])
        recent_30d = len(logs[logs['date'] >= now - timedelta(days=30)])
        top_issue  = logs['issue_type'].mode()[0] if len(logs) > 0 else "unknown"
        temp_fixes = len(logs[logs['action_taken'] == 'temporary_fix'])
        total_down = int(logs['downtime_minutes'].sum())
        total_inc  = r.get('total_incidents', len(logs))
        ml_flag    = (
            f"ML Anomaly detected ({r.get('ml_confidence', 0)}% confidence)"
            if r.get('ml_anomaly') else "ML Normal"
        )
        window     = r.get('predicted_window', _score_to_window(r['risk_score']))
        prod_line  = logs.iloc[0]['production_line'] if len(logs) > 0 else "Unknown"
        factors    = ". ".join(r.get('factors', [])[:4])

        # Issue breakdown
        issue_counts = logs['issue_type'].value_counts()
        issue_summary = ", ".join(
            f"{issue} x{cnt}" for issue, cnt in issue_counts.items()
        ) if len(issue_counts) > 0 else "no issues recorded"

        # Criticality breakdown
        crit_count = len(logs[logs['criticality'].isin(['High', 'Critical'])])

        machine_lines.append(
            f"{mid} | Line: {prod_line} | Risk: {r['risk_level']} ({r['risk_score']}/100) | "
            f"Failure window: {window} | {ml_flag} | "
            f"Total incidents: {total_inc} | Last 30 days: {recent_30d} | Last 7 days: {recent_7d} | "
            f"Temp fixes: {temp_fixes} | Critical/High incidents: {crit_count} | "
            f"Total downtime: {total_down} min | Main issue: {top_issue} | "
            f"Issue breakdown: {issue_summary} | Key factors: {factors}"
        )

    machine_status_block = "\n".join(machine_lines)

    # ── Risk tier summaries ───────────────────────────────────────────────────
    critical = [r for r in risk_data if r['risk_level'] == 'Critical']
    high     = [r for r in risk_data if r['risk_level'] == 'High']
    medium   = [r for r in risk_data if r['risk_level'] == 'Medium']
    low      = [r for r in risk_data if r['risk_level'] == 'Low']

    critical_txt = ", ".join(
        f"{r['machine_id']} (score {r['risk_score']}, window {r.get('predicted_window', _score_to_window(r['risk_score']))})"
        for r in critical
    ) or "None"
    high_txt = ", ".join(
        f"{r['machine_id']} (score {r['risk_score']})" for r in high
    ) or "None"
    medium_txt = ", ".join(r['machine_id'] for r in medium) or "None"
    low_txt    = ", ".join(r['machine_id'] for r in low)    or "None"

    # ── Production line cascade map ───────────────────────────────────────────
    line_map = {}
    for r in risk_data:
        mid  = r['machine_id']
        logs = df[df['machine_id'] == mid]
        if len(logs) > 0:
            line = logs.iloc[0]['production_line']
            line_map.setdefault(line, []).append(mid)

    cascade_lines = []
    for line, machines in sorted(line_map.items()):
        # Find highest risk machine on this line
        line_risks = [r for r in risk_data if r['machine_id'] in machines]
        line_risks.sort(key=lambda x: x['risk_score'], reverse=True)
        top = line_risks[0] if line_risks else None
        top_info = f" — highest risk: {top['machine_id']} score {top['risk_score']}" if top else ""
        cascade_lines.append(f"{line}: {', '.join(sorted(machines))}{top_info}")
    cascade_block = "\n".join(cascade_lines)

    # ── Schedule block ────────────────────────────────────────────────────────
    schedule_block = "No maintenance currently scheduled."
    if schedule:
        sched_lines = []
        for item in schedule[:10]:
            flag = item.get('urgency_flag', '')
            actions = ", ".join(item.get('recommended_actions', [])[:2])
            sched_lines.append(
                f"{item['machine_id']} | {item['priority']} | {item['scheduled_time']} | "
                f"Duration: {item['estimated_duration']} | Line: {item['production_line']} | "
                f"{flag} | Actions: {actions}"
            )
        schedule_block = "\n".join(sched_lines)

    # ── Today's urgent faults ─────────────────────────────────────────────────
    today = now.date()
    today_logs = df[pd.to_datetime(df['date']).dt.date == today]
    urgent_today = today_logs['machine_id'].unique().tolist()
    urgent_txt = ", ".join(urgent_today) if urgent_today else "None"

    # ── Cost summary ──────────────────────────────────────────────────────────
    total_downtime_hrs = round(df['downtime_minutes'].sum() / 60, 1)
    total_cost_inr     = int(total_downtime_hrs * 42000)
    total_incidents    = len(df)
    avg_downtime_per_incident = round(df['downtime_minutes'].mean(), 1)

    # ── ML anomaly summary ────────────────────────────────────────────────────
    anomaly_machines = [r for r in risk_data if r.get('ml_anomaly')]
    anomaly_txt = ", ".join(
        f"{r['machine_id']} ({r.get('ml_confidence', 0)}%)" for r in anomaly_machines
    ) or "None"

    # ─────────────────────────────────────────────────────────────────────────
    return [
        {
            "title": "Agent Identity & Purpose",
            "body": (
                "# AGENT GLOBAL INSTRUCTIONS\n"
                "## PERSONA\n"
                "You are PlantPulse, an industrial maintenance voice assistant for a smart factory.\n"
                "You monitor 10 machines (M1 through M10) across multiple production lines.\n"
                "You speak to maintenance engineers and factory staff.\n"
                "Your purpose: give accurate, real-time machine status, risk levels, fault details, "
                "maintenance schedules, cascade risks, and repair recommendations.\n"
                "Tone: professional, clear, direct — like a senior maintenance engineer.\n\n"
                "# RESPONSE RULES FOR VOICE\n"
                "Your responses are read aloud by text-to-speech.\n"
                "Use short, simple, conversational sentences.\n"
                "Never use bullet points, symbols, markdown, or numbered lists in spoken responses.\n"
                "End with a natural conversational hook when appropriate.\n\n"
                "# SCOPE\n"
                "Answer questions about machine faults, risk levels, maintenance schedules, "
                "cascade dependencies, repair recommendations, and platform capabilities.\n"
                "Redirect non-maintenance queries politely.\n\n"
                "# GUARDRAILS\n"
                "Never provide incorrect information. Never guarantee outcomes. "
                "Always base answers on the live data provided in this context."
            ),
            "is_enabled": True
        },
        {
            "title": "Live Machine Status — Real-Time Data",
            "body": (
                f"# LIVE MACHINE STATUS — Updated {now.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"CRITICAL (failure in 1-7 days): {critical_txt}\n"
                f"HIGH risk (failure in 1-2 weeks): {high_txt}\n"
                f"MEDIUM risk (failure in 2-4 weeks): {medium_txt}\n"
                f"LOW risk (failure in 4+ weeks): {low_txt}\n\n"
                f"URGENT — Faults reported TODAY: {urgent_txt}\n\n"
                f"ML ANOMALIES detected: {anomaly_txt}\n\n"
                "# FULL MACHINE DETAILS (one line per machine)\n"
                f"{machine_status_block}\n\n"
                "# RISK SCORE THRESHOLDS\n"
                "Critical: 70-100. High: 50-69. Medium: 30-49. Low: below 30.\n\n"
                "# ML STATUS EXPLANATION\n"
                "ML Anomaly means the machine behavior is statistically unusual compared to all other machines, "
                "detected by Isolation Forest algorithm. "
                "ML Status is independent from Risk Level — a machine can be Critical risk but ML Normal, "
                "or Low risk but ML Anomaly."
            ),
            "is_enabled": True
        },
        {
            "title": "Production Line Layout and Cascade Risk",
            "body": (
                "# PRODUCTION LINE LAYOUT\n"
                f"{cascade_block}\n\n"
                "# CASCADE RISK RULES\n"
                "When a machine fails, other machines on the same production line face cascade risk.\n"
                "Cascade probability calculation:\n"
                "Base 40 percent for being on the same production line.\n"
                "Plus 20 percent if they share the same issue types.\n"
                "Plus 15 percent if the dependent machine had more than 2 incidents in the last 30 days.\n"
                "Maximum cascade probability is 85 percent.\n\n"
                "When answering cascade questions: identify the production line, name the machines at risk, "
                "give the cascade probability, and recommend pre-emptive inspection."
            ),
            "is_enabled": True
        },
        {
            "title": "Machine Status Inquiry Guide",
            "body": (
                "# HOW TO ANSWER MACHINE STATUS QUESTIONS\n"
                "When asked about a specific machine, look it up in the Live Machine Status section and state:\n"
                "1. Risk level and score out of 100.\n"
                "2. Predicted failure window.\n"
                "3. Most common issue type.\n"
                "4. ML anomaly status.\n"
                "5. Single most important recommended action.\n\n"
                "Keep the answer to 3 sentences maximum.\n\n"
                "Example:\n"
                "M3 is at Critical risk with a score of 82, expected to fail within 7 days due to vibration. "
                "No ML anomaly detected. I recommend inspecting the bearings immediately."
            ),
            "is_enabled": True
        },
        {
            "title": "Faults and Repair Recommendations",
            "body": (
                "# HOW TO ANSWER FAULT QUESTIONS\n"
                "List Critical machines first, then High risk.\n"
                "For each: state machine ID, risk score, main issue type, and predicted failure window.\n"
                "Recommend the most urgent action.\n\n"
                "# REPAIR ACTIONS BY ISSUE TYPE\n"
                "Vibration: inspect and replace bearings, check shaft alignment and balance.\n"
                "Overheating: clean cooling system, check motor windings, replace cooling fan.\n"
                "Lubrication failure: full lubrication service, replace seals.\n"
                "Electrical fault: inspect connections, test voltage and current.\n"
                "Mechanical wear: check belts and couplings, inspect for wear.\n"
                "Hydraulic failure: check hydraulic pressure, inspect seals and hoses."
            ),
            "is_enabled": True
        },
        {
            "title": "Live Maintenance Schedule",
            "body": (
                f"# CURRENT MAINTENANCE SCHEDULE — {now.strftime('%Y-%m-%d')}\n\n"
                f"{schedule_block}\n\n"
                "# SCHEDULING RULES\n"
                "Machines with faults reported today get URGENT priority — scheduled within the next available hour.\n"
                "High risk machines are scheduled next.\n"
                "Weekend slots: 8 AM, 2 PM, 6 PM to minimize production disruption.\n"
                "Weekday slots: 6 PM onwards.\n"
                "Estimated duration: 2-3 hours for urgent, 1.5-2 hours for high priority."
            ),
            "is_enabled": True
        },
        {
            "title": "Cost and Downtime Data",
            "body": (
                "# COST DATA — All amounts in Indian Rupees\n\n"
                f"Total recorded incidents: {total_incidents}\n"
                f"Total recorded downtime: {total_downtime_hrs} hours\n"
                f"Average downtime per incident: {avg_downtime_per_incident} minutes\n"
                f"Estimated total downtime cost: {total_cost_inr:,} rupees\n\n"
                "Cost rates:\n"
                "Downtime costs 42,000 rupees per hour.\n"
                "Labor is 1,500 rupees per incident.\n"
                "Parts average 5,000 rupees per replacement.\n"
                "Predictive maintenance can save up to 70 percent of downtime costs by catching failures early."
            ),
            "is_enabled": True
        },
        {
            "title": "Platform Functionality",
            "body": (
                "# WHAT PLANTPULSE AI DOES\n"
                "PlantPulse AI is a predictive maintenance intelligence system monitoring 10 industrial machines.\n\n"
                "Key capabilities:\n"
                "7-factor risk scoring algorithm calculates failure probability for each machine.\n"
                "Isolation Forest machine learning detects anomalous machine behavior.\n"
                "7 AI models compared simultaneously for maintenance recommendations: "
                "MiniMax, Kimi, GLM-5, DeepSeek, Qwen3-Next 80B, Gemini, and GPT-3.5.\n"
                "Urgent priority scheduling puts today's faults first.\n"
                "Failure cascade prediction shows which machines are at risk if one fails.\n"
                "PDF report export includes full AI recommendations for any machine.\n"
                "Real-time updates in under 500 milliseconds when new logs are added."
            ),
            "is_enabled": True
        },
        {
            "title": "FAQ Examples",
            "body": (
                "User: Which machines need immediate attention?\n"
                f"Agent: The most critical machines right now are {critical_txt}. "
                "These need inspection within the next 7 days to prevent failure.\n\n"
                "User: Are there any faults today?\n"
                f"Agent: Today's urgent faults are on {urgent_txt}. These have been given immediate priority in the schedule.\n\n"
                "User: Which machines have ML anomalies?\n"
                f"Agent: The machines with ML-detected anomalies are {anomaly_txt}. "
                "This means their behavior is statistically unusual compared to the rest of the fleet.\n\n"
                "User: What is the status of M3?\n"
                "Agent: [Look up M3 in Live Machine Status and give risk level, score, issue type, "
                "failure window, ML status, and top action in 3 sentences.]\n\n"
                "User: What happens if M5 fails?\n"
                "Agent: [Look up M5's production line in the Production Line Layout section. "
                "Name the other machines on that line and calculate cascade probability.]\n\n"
                "User: What does this platform do?\n"
                "Agent: PlantPulse AI predicts machine failures before they happen using machine learning "
                "and 7 AI models. It monitors 10 machines, recommends repairs, schedules maintenance, "
                "and exports detailed PDF reports to minimize downtime and costs."
            ),
            "is_enabled": True
        },
        {
            "title": "Closing Statement",
            "body": (
                "# CLOSING\n"
                "End calls politely and professionally.\n\n"
                "Example: Thank you for using PlantPulse. Stay safe on the floor and have a productive day."
            ),
            "is_enabled": True
        },
    ]


def _score_to_window(score):
    """Convert risk score to failure window string"""
    if score >= 70:
        return "1-7 days"
    elif score >= 50:
        return "1-2 weeks"
    elif score >= 30:
        return "2-4 weeks"
    return "4+ weeks"


def create_voice_agent(risk_data, df, schedule=None):
    """Create the PlantPulse voice agent on Omi Dimension AI"""
    if not OMI_API_KEY:
        return {"success": False, "error": "OMI_API_KEY not set in .env"}

    try:
        from omnidimension import Client
        client = Client(OMI_API_KEY)

        context = build_context_breakdown(risk_data, df, schedule)

        response = client.agent.create(
            name="PlantPulse AI — Industrial Maintenance Voice Assistant",
            welcome_message=(
                "Hello, I am PlantPulse, your industrial maintenance assistant. "
                "I can tell you about machine faults, risk levels, maintenance schedules, "
                "and repair recommendations. How can I assist you today?"
            ),
            context_breakdown=context,
            call_type="Incoming",
            transcriber={"provider": "Azure", "silence_timeout_ms": 400},
            model={"model": "gpt-4.1-mini", "temperature": 0.7},
            voice={"provider": "google", "voice_id": "en-in-Chirp3-HD-Despina"},
            languages=["English", "Marathi", "Hindi"],
            interruption={"enabled": True, "min_words": 2},
            noise_reduction=True,
            call_ending={"max_duration_sec": 600, "enabled": False},
            user_idle={
                "threshold_sec": 7,
                "first_message": "Are you still there?",
                "second_message": "Would you like to continue our conversation?",
                "last_message": "I'll leave you for now. Have a nice day!"
            },
        )
        return {"success": True, "response": response}

    except ImportError:
        return {"success": False, "error": "omnidimension package not installed. Run: pip install omnidimension"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_voice_agent(agent_id, risk_data, df, schedule=None):
    """Update existing agent with fresh live machine data"""
    if not OMI_API_KEY:
        return {"success": False, "error": "OMI_API_KEY not set in .env"}

    try:
        from omnidimension import Client
        client = Client(OMI_API_KEY)

        context = build_context_breakdown(risk_data, df, schedule)
        response = client.agent.update(agent_id, {"context_breakdown": context})
        return {"success": True, "response": response}

    except ImportError:
        return {"success": False, "error": "omnidimension package not installed. Run: pip install omnidimension"}
    except Exception as e:
        return {"success": False, "error": str(e)}
