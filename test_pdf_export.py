"""Quick test — generate a PDF for M1 and save it locally"""
import pandas as pd, os, sys
sys.path.insert(0, '.')

from database import MaintenanceDatabase
from agents.failure_predictor_ml import FailurePredictorMLAgent
from agents.repair_recommender import RepairRecommender
from utils.pdf_exporter import generate_machine_pdf

# Load data
db = MaintenanceDatabase()
df = db.get_all_logs()
df = df.rename(columns={'log_date': 'date', 'issue_category': 'issue_type'})
df['date'] = pd.to_datetime(df['date'])

machine_id = df['machine_id'].iloc[0]
print(f"Testing PDF for: {machine_id}")

predictor   = FailurePredictorMLAgent(df)
risk_info   = predictor.calculate_risk_score(machine_id)
fail_window = predictor.predict_failure_window(machine_id)

machine_logs = df[df['machine_id'] == machine_id]
most_common  = machine_logs['issue_type'].mode()[0]

recommender = RepairRecommender()
repair_rec  = recommender.get_repair_recommendation(most_common)

pdf_bytes = generate_machine_pdf(
    machine_id=machine_id,
    machine_logs_df=machine_logs,
    risk_info=risk_info,
    repair_recommendation=repair_rec,
    failure_window=fail_window,
)

out = f"test_report_{machine_id}.pdf"
with open(out, 'wb') as f:
    f.write(pdf_bytes)

print(f"✅ PDF generated: {out}  ({len(pdf_bytes):,} bytes)")
print(f"   Risk: {risk_info['risk_level']} ({risk_info['risk_score']}/100)")
print(f"   Logs: {len(machine_logs)}")
print(f"   Issue: {most_common} → Component: {repair_rec['primary_component']}")
