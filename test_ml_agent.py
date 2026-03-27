"""Test ML Agent initialization"""
import pandas as pd
from agents.failure_predictor_ml import FailurePredictorMLAgent

# Load data
df = pd.read_csv('data/maintenance_logs.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.rename(columns={'issue_category': 'issue_type'})

print("Loading data...")
print(f"Total logs: {len(df)}")
print(f"Machines: {sorted(df['machine_id'].unique())}")

# Initialize ML agent
print("\nInitializing ML Agent...")
predictor = FailurePredictorMLAgent(df)
print("✅ ML Agent initialized successfully!")

# Calculate risk scores
print("\nCalculating risk scores...")
risks = predictor.get_all_risk_scores()
print(f"✅ Risk scores calculated for {len(risks)} machines")

# Show top 3 risks
print("\nTop 3 High-Risk Machines:")
for i, risk in enumerate(risks[:3], 1):
    print(f"{i}. {risk['machine_id']}: {risk['risk_score']}/100 ({risk['risk_level']})")
    if risk['ml_anomaly']:
        print(f"   🤖 ML Anomaly detected ({risk['ml_confidence']}% confidence)")

print("\n✅ System is working perfectly!")
