import pandas as pd
import random
from datetime import datetime, timedelta

def generate_maintenance_logs(num_records=200):
    """Generate realistic manufacturing maintenance log data with proper risk distribution"""
    
    # Manufacturing machines with simple naming
    machines = {
        'M1': {'type': 'CNC Machine', 'line': 'Production-A', 'cost_per_hour': 45000, 'risk_profile': 'high'},
        'M2': {'type': 'CNC Machine', 'line': 'Production-A', 'cost_per_hour': 45000, 'risk_profile': 'medium'},
        'M3': {'type': 'Lathe Machine', 'line': 'Production-B', 'cost_per_hour': 35000, 'risk_profile': 'high'},
        'M4': {'type': 'Lathe Machine', 'line': 'Production-B', 'cost_per_hour': 35000, 'risk_profile': 'low'},
        'M5': {'type': 'Milling Machine', 'line': 'Production-A', 'cost_per_hour': 40000, 'risk_profile': 'medium'},
        'M6': {'type': 'Hydraulic Press', 'line': 'Production-C', 'cost_per_hour': 50000, 'risk_profile': 'critical'},
        'M7': {'type': 'Hydraulic Press', 'line': 'Production-C', 'cost_per_hour': 50000, 'risk_profile': 'high'},
        'M8': {'type': 'Welding Robot', 'line': 'Assembly', 'cost_per_hour': 38000, 'risk_profile': 'medium'},
        'M9': {'type': 'Conveyor System', 'line': 'Assembly', 'cost_per_hour': 25000, 'risk_profile': 'low'},
        'M10': {'type': 'Air Compressor', 'line': 'Utility', 'cost_per_hour': 30000, 'risk_profile': 'low'}
    }
    
    # Issue templates (English only)
    issue_templates = {
        'vibration': [
            "Abnormal vibration observed. Bearing checked.",
            "Excessive vibration in machine. Temporary adjustment done.",
            "Vibration level increasing. Bearing replacement needed.",
            "Abnormal vibration near shaft. Alignment checked."
        ],
        'overheating': [
            "Motor hotter than normal. Cooling system checked.",
            "Overheating detected. Temporary cooling applied.",
            "Temperature spike during peak load. Investigation needed.",
            "Motor running hot. Ventilation cleared."
        ],
        'lubrication': [
            "Low lubrication level. Oil added.",
            "Lubrication system leak. Temporary seal applied.",
            "Bearing lubrication insufficient. Maintenance scheduled.",
            "Oil contamination found. Partial replacement done."
        ],
        'electrical': [
            "Electrical connection loose. Tightened and tested.",
            "Power fluctuation observed. Wiring inspected.",
            "Circuit breaker tripped twice. Load checked.",
            "Voltage irregularity detected. Under observation."
        ],
        'mechanical': [
            "Belt tension adjusted. Wear visible.",
            "Coupling misalignment corrected.",
            "Bearing noise detected. Replacement recommended.",
            "Shaft wobble observed. Detailed inspection needed."
        ],
        'hydraulic': [
            "Hydraulic pressure drop. Pump checked.",
            "Hydraulic oil leak. Seal replaced.",
            "Pressure unstable. Filter cleaned.",
            "Air in hydraulic system. Bleeding done."
        ]
    }
    
    # Spare parts with INR costs
    spare_parts = {
        'bearing': 8500,
        'belt': 3200,
        'seal': 1500,
        'sensor': 4500,
        'motor': 45000,
        'pump': 28000,
        'filter': 2800,
        'valve': 6500
    }
    
    action_types = ['temporary_fix', 'adjustment', 'part_replacement', 'inspection', 'monitoring']
    criticality = ['Low', 'Medium', 'High', 'Critical']
    
    # Technician names
    technicians = ['Rajesh Kumar', 'Amit Sharma', 'Priya Patel', 'Suresh Reddy', 'Ankit Verma', 
                   'Deepak Singh', 'Rahul Gupta', 'Vijay Kumar', 'Sanjay Yadav', 'Manoj Tiwari']
    
    logs = []
    start_date = datetime.now() - timedelta(days=90)
    
    # Risk-based incident distribution
    # Critical: 30-35 incidents, High: 25-30, Medium: 15-20, Low: 8-12
    risk_distribution = {
        'critical': 33,  # M6
        'high': 27,      # M1, M3, M7 (split)
        'medium': 17,    # M2, M5, M8 (split)
        'low': 10        # M4, M9, M10 (split)
    }
    
    # Assign incidents per machine based on risk profile
    machine_incidents = {
        'M1': 28,   # High risk
        'M2': 18,   # Medium risk
        'M3': 26,   # High risk
        'M4': 10,   # Low risk
        'M5': 17,   # Medium risk
        'M6': 33,   # Critical risk
        'M7': 27,   # High risk
        'M8': 16,   # Medium risk
        'M9': 12,   # Low risk
        'M10': 13   # Low risk
    }
    
    # Generate logs for each machine
    for machine_id, incident_count in machine_incidents.items():
        machine_info = machines[machine_id]
        risk_profile = machine_info['risk_profile']
        
        for i in range(incident_count):
            # Date distribution - more recent for high risk
            if risk_profile in ['critical', 'high']:
                days_ago = random.randint(0, 60)  # More recent incidents
            else:
                days_ago = random.randint(0, 90)  # Spread across 90 days
            
            date = start_date + timedelta(days=days_ago, hours=random.randint(6, 22))
            
            # Issue type based on risk profile
            if risk_profile == 'critical':
                issue_type = random.choice(['vibration', 'overheating', 'hydraulic', 'mechanical'])
            elif risk_profile == 'high':
                issue_type = random.choice(['vibration', 'overheating', 'mechanical'])
            else:
                issue_type = random.choice(list(issue_templates.keys()))
            
            note = random.choice(issue_templates[issue_type])
            
            # Add "Issue again" for repeated problems (more common in high risk)
            if risk_profile in ['critical', 'high'] and random.random() > 0.5:
                note = note + " Issue again."
            elif random.random() > 0.7:
                note = note + " Issue again."
            
            # Calculate downtime cost in INR
            if risk_profile == 'critical':
                downtime_minutes = random.randint(30, 240) if random.random() > 0.2 else 0
            elif risk_profile == 'high':
                downtime_minutes = random.randint(20, 180) if random.random() > 0.3 else 0
            elif risk_profile == 'medium':
                downtime_minutes = random.randint(10, 120) if random.random() > 0.5 else 0
            else:
                downtime_minutes = random.randint(5, 60) if random.random() > 0.6 else 0
            
            downtime_cost = int((downtime_minutes / 60) * machine_info['cost_per_hour'])
            
            # Parts cost
            if risk_profile in ['critical', 'high']:
                part_replaced = random.choice([None, 'bearing', 'pump', 'motor', 'valve', 'seal'])
            else:
                part_replaced = random.choice([None, None, 'bearing', 'belt', 'seal', 'filter'])
            
            parts_cost = spare_parts.get(part_replaced, 0) if part_replaced else 0
            
            # Labor cost (Indian rates)
            labor_cost = random.randint(800, 2500)
            
            # Criticality based on risk profile
            if risk_profile == 'critical':
                crit = random.choice(['Critical', 'High', 'High'])
            elif risk_profile == 'high':
                crit = random.choice(['High', 'High', 'Medium'])
            elif risk_profile == 'medium':
                crit = random.choice(['Medium', 'Medium', 'Low'])
            else:
                crit = random.choice(['Low', 'Low', 'Medium'])
            
            logs.append({
                'machine_id': machine_id,
                'machine_type': machine_info['type'],
                'production_line': machine_info['line'],
                'date': date.strftime('%Y-%m-%d %H:%M'),
                'technician': random.choice(technicians),
                'technician_note': note,
                'issue_type': issue_type,
                'downtime_minutes': downtime_minutes,
                'downtime_cost_inr': downtime_cost,
                'action_taken': random.choice(action_types),
                'parts_replaced': part_replaced,
                'parts_cost_inr': parts_cost,
                'labor_cost_inr': labor_cost,
                'total_cost_inr': downtime_cost + parts_cost + labor_cost,
                'criticality': crit,
                'shift': 'Morning' if 6 <= date.hour < 14 else 'Afternoon' if 14 <= date.hour < 22 else 'Night'
            })
    
    df = pd.DataFrame(logs)
    df = df.sort_values('date').reset_index(drop=True)
    return df

if __name__ == '__main__':
    df = generate_maintenance_logs(200)
    df.to_csv('data/maintenance_logs.csv', index=False)
    print(f"Generated {len(df)} maintenance log records")
    print(f"\nMachines: {sorted(df['machine_id'].unique(), key=lambda x: int(x[1:]))}")
    print(f"Total Cost: ₹{df['total_cost_inr'].sum():,.0f}")
    print(f"Total Downtime: {df['downtime_minutes'].sum():,.0f} minutes")
    print("\nIncidents per machine:")
    for machine in sorted(df['machine_id'].unique(), key=lambda x: int(x[1:])):
        count = len(df[df['machine_id'] == machine])
        print(f"  {machine}: {count} incidents")
