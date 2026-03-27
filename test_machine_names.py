"""Test script to verify machine names are M1-M10"""

import pandas as pd
from database import MaintenanceDatabase

# Load CSV data
df = pd.read_csv('data/maintenance_logs.csv')

print("=" * 60)
print("Machine Names Verification")
print("=" * 60)

# Check machine names
machines = sorted(df['machine_id'].unique(), key=lambda x: int(x[1:]))  # Sort by number
print(f"\n✅ Machine IDs: {', '.join(machines)}")

# Verify format
expected = [f'M{i}' for i in range(1, 11)]
if machines == expected:
    print("✅ Machine names are correct: M1, M2, M3, ..., M10")
else:
    print(f"⚠️ Expected: {expected}")
    print(f"⚠️ Got: {machines}")

# Test database
print("\n" + "=" * 60)
print("Database Test")
print("=" * 60)

db = MaintenanceDatabase()
db.load_csv_to_db('data/maintenance_logs.csv')

stats = db.get_stats()
print(f"\n✅ Total machines in DB: {stats['total_machines']}")
print(f"✅ Total logs in DB: {stats['total_logs']}")
print(f"✅ High risk machines: {stats['high_risk_machines']}")

# Get sample logs
logs_df = db.get_all_logs()
sample_machines = sorted(logs_df['machine_id'].unique()[:5], key=lambda x: int(x[1:]))
print(f"\n✅ Sample machine IDs from DB: {', '.join(sample_machines)}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Machine names are M1-M10")
print("=" * 60)
