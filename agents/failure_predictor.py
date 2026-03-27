import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import Counter

class FailurePredictorAgent:
    """Agent for predicting machine failure risk based on historical patterns with ML"""
    
    def __init__(self, df):
        self.df = df.copy()
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.risk_scores = {}
        self.ml_model = None
        self.scaler = StandardScaler()
        self._train_anomaly_detector()
    
    def calculate_risk_score(self, machine_id):
        """Calculate failure risk score (0-100) for a machine"""
        machine_logs = self.df[self.df['machine_id'] == machine_id]
        
        if len(machine_logs) == 0:
            return {'risk_score': 0, 'risk_level': 'Unknown', 'factors': []}
        
        score = 0
        factors = []
        
        # Factor 1: Recent incident frequency (0-30 points)
        recent_30_days = datetime.now() - timedelta(days=30)
        recent_incidents = len(machine_logs[machine_logs['date'] >= recent_30_days])
        incident_score = min(recent_incidents * 5, 30)
        score += incident_score
        if recent_incidents > 3:
            factors.append(f"{recent_incidents} incidents in last 30 days")
        
        # Factor 2: Repeated issues (0-25 points)
        issue_counts = machine_logs['issue_type'].value_counts()
        repeated_issues = issue_counts[issue_counts >= 2]
        repeated_score = min(len(repeated_issues) * 8, 25)
        score += repeated_score
        if len(repeated_issues) > 0:
            factors.append(f"Repeated issues: {', '.join(repeated_issues.index.tolist())}")
        
        # Factor 3: Temporary fixes (0-20 points)
        temp_fixes = len(machine_logs[machine_logs['action_taken'] == 'temporary_fix'])
        temp_fix_score = min(temp_fixes * 7, 20)
        score += temp_fix_score
        if temp_fixes > 1:
            factors.append(f"{temp_fixes} temporary fixes applied")
        
        # Factor 4: Critical incidents (0-15 points)
        critical_count = len(machine_logs[machine_logs['criticality'].isin(['High', 'Critical'])])
        critical_score = min(critical_count * 5, 15)
        score += critical_score
        if critical_count > 0:
            factors.append(f"{critical_count} high/critical severity incidents")
        
        # Factor 5: Total downtime (0-10 points)
        total_downtime = machine_logs['downtime_minutes'].sum()
        downtime_score = min(total_downtime / 60, 10)  # 1 point per hour
        score += downtime_score
        if total_downtime > 120:
            factors.append(f"{int(total_downtime)} minutes total downtime")
        
        # Determine risk level
        if score >= 70:
            risk_level = 'Critical'
        elif score >= 50:
            risk_level = 'High'
        elif score >= 30:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        return {
            'machine_id': machine_id,
            'risk_score': min(int(score), 100),
            'risk_level': risk_level,
            'factors': factors,
            'total_incidents': len(machine_logs),
            'recent_incidents': recent_incidents
        }
    
    def get_all_risk_scores(self):
        """Calculate risk scores for all machines"""
        machines = self.df['machine_id'].unique()
        risk_data = []
        
        for machine in machines:
            risk_info = self.calculate_risk_score(machine)
            risk_data.append(risk_info)
        
        # Sort by risk score descending
        risk_data.sort(key=lambda x: x['risk_score'], reverse=True)
        return risk_data
    
    def get_high_risk_machines(self, threshold=50):
        """Get machines with risk score above threshold"""
        all_risks = self.get_all_risk_scores()
        return [r for r in all_risks if r['risk_score'] >= threshold]
    
    def predict_failure_window(self, machine_id):
        """Estimate time window for potential failure"""
        risk_info = self.calculate_risk_score(machine_id)
        risk_score = risk_info['risk_score']
        
        if risk_score >= 70:
            window = "1-7 days"
            urgency = "Immediate"
        elif risk_score >= 50:
            window = "1-2 weeks"
            urgency = "High"
        elif risk_score >= 30:
            window = "2-4 weeks"
            urgency = "Medium"
        else:
            window = "4+ weeks"
            urgency = "Low"
        
        return {
            'machine_id': machine_id,
            'predicted_window': window,
            'urgency': urgency,
            'risk_score': risk_score
        }
