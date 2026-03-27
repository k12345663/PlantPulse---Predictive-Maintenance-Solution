"""
Push live machine data into the PlantPulse voice agent on Omi Dimension AI.
Usage: python update_omi_agent.py <agent_id>
       python update_omi_agent.py   (uses AGENT_ID below)
"""

import sys
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("OMI_API_KEY", "")
AGENT_ID = "131316"   # override via CLI arg if needed


def load_live_data():
    """Load real machine data from the PlantPulse database"""
    from database import MaintenanceDatabase
    from agents.failure_predictor_ml import FailurePredictorMLAgent
    from agents.scheduler_urgent import UrgentMaintenanceScheduler

    db  = MaintenanceDatabase()
    df  = db.get_all_logs()
    df  = df.rename(columns={'log_date': 'date', 'issue_category': 'issue_type'})
    df['date'] = pd.to_datetime(df['date'])

    predictor = FailurePredictorMLAgent(df)
    risk_data  = predictor.get_all_risk_scores()

    # Add predicted_window to each risk entry
    for r in risk_data:
        pw = predictor.predict_failure_window(r['machine_id'])
        r['predicted_window'] = pw['predicted_window']

    scheduler = UrgentMaintenanceScheduler(risk_data, df)
    schedule  = scheduler.generate_schedule(days_ahead=7)

    return df, risk_data, schedule


def main():
    agent_id = sys.argv[1] if len(sys.argv) > 1 else AGENT_ID

    if not agent_id:
        print("❌ No agent ID provided.")
        print("   Usage: python update_omi_agent.py <agent_id>")
        sys.exit(1)

    print("📊 Loading live machine data from database...")
    try:
        df, risk_data, schedule = load_live_data()
        print(f"   ✅ {len(df)} logs | {len(risk_data)} machines | {len(schedule)} schedule items")
    except Exception as e:
        print(f"   ❌ Failed to load data: {e}")
        sys.exit(1)

    print("🔧 Building live context...")
    from agents.omi_voice_agent import build_context_breakdown
    context = build_context_breakdown(risk_data, df, schedule)
    print(f"   ✅ {len(context)} context sections built")

    print(f"📡 Updating agent {agent_id} on Omi Dimension AI...")
    try:
        from omnidimension import Client
        client   = Client(API_KEY)
        response = client.agent.update(agent_id, {"context_breakdown": context})
        print("✅ Agent updated successfully!")
        print(response)
    except Exception as e:
        print(f"❌ Update failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
