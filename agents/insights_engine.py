"""Advanced Insights Engine - Unique Features for PlantPulse AI"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter

class InsightsEngine:
    """Generate unique, actionable insights from maintenance data"""
    
    def __init__(self, df):
        self.df = df.copy()
        self.df['date'] = pd.to_datetime(self.df['date'])
    
    def detect_anomalies(self):
        """Detect unusual patterns that deviate from normal behavior"""
        anomalies = []
        
        # Anomaly 1: Sudden spike in incidents
        recent_7_days = datetime.now() - timedelta(days=7)
        recent_incidents = len(self.df[self.df['date'] >= recent_7_days])
        avg_weekly = len(self.df) / 13  # 90 days / 7
        
        if recent_incidents > avg_weekly * 1.5:
            anomalies.append({
                'type': 'incident_spike',
                'severity': 'high',
                'title': '⚠️ Unusual Incident Spike Detected',
                'description': f'{recent_incidents} incidents in last 7 days (avg: {int(avg_weekly)})',
                'recommendation': 'Investigate environmental factors or recent process changes'
            })
        
        # Anomaly 2: Machine showing new issue type
        for machine in self.df['machine_id'].unique():
            machine_logs = self.df[self.df['machine_id'] == machine].sort_values('date')
            if len(machine_logs) > 3:
                recent_issues = set(machine_logs.tail(2)['issue_type'])
                historical_issues = set(machine_logs.head(len(machine_logs)-2)['issue_type'])
                new_issues = recent_issues - historical_issues
                
                if new_issues:
                    anomalies.append({
                        'type': 'new_issue_pattern',
                        'severity': 'medium',
                        'title': f'🔍 New Issue Pattern: {machine}',
                        'description': f'Machine showing {", ".join(new_issues)} for first time',
                        'recommendation': 'May indicate underlying problem or component degradation',
                        'machine_id': machine  # Added machine_id
                    })
        
        # Anomaly 3: Weekend incidents (unusual)
        self.df['day_of_week'] = self.df['date'].dt.dayofweek
        weekend_incidents = len(self.df[self.df['day_of_week'].isin([5, 6])])
        weekend_ratio = weekend_incidents / len(self.df)
        
        if weekend_ratio > 0.2:
            anomalies.append({
                'type': 'weekend_pattern',
                'severity': 'medium',
                'title': '📅 High Weekend Incident Rate',
                'description': f'{int(weekend_ratio*100)}% of incidents occur on weekends',
                'recommendation': 'Review weekend operations and staffing levels'
            })
        
        # Anomaly 4: Rapid deterioration (multiple issues in short time)
        for machine in self.df['machine_id'].unique():
            machine_logs = self.df[self.df['machine_id'] == machine].sort_values('date')
            if len(machine_logs) >= 3:
                last_3 = machine_logs.tail(3)
                time_span = (last_3['date'].max() - last_3['date'].min()).days
                
                if time_span <= 7 and len(last_3) >= 3:
                    anomalies.append({
                        'type': 'rapid_deterioration',
                        'severity': 'critical',
                        'title': f'🚨 Rapid Deterioration: {machine}',
                        'description': f'3 incidents in {time_span} days',
                        'recommendation': 'Immediate inspection required - possible cascading failure',
                        'machine_id': machine  # Added machine_id
                    })
        
        return anomalies[:5]  # Top 5 anomalies
    
    def predict_failure_cascade(self, machine_id):
        """Predict which machines might fail if this one fails"""
        machine_logs = self.df[self.df['machine_id'] == machine_id]
        
        if len(machine_logs) == 0:
            return []
        
        # Get production line
        prod_line = machine_logs.iloc[0]['production_line']
        
        # Find machines on same line
        line_machines = self.df[self.df['production_line'] == prod_line]['machine_id'].unique()
        line_machines = [m for m in line_machines if m != machine_id]
        
        # Calculate cascade risk
        cascade_risks = []
        for dependent_machine in line_machines[:3]:  # Top 3 dependent machines
            dependent_logs = self.df[self.df['machine_id'] == dependent_machine]
            
            # Risk factors
            same_line_risk = 40  # Base risk for same production line
            issue_correlation = 20 if len(set(machine_logs['issue_type']) & set(dependent_logs['issue_type'])) > 0 else 0
            recent_issues = 15 if len(dependent_logs[dependent_logs['date'] >= datetime.now() - timedelta(days=30)]) > 2 else 0
            
            total_risk = same_line_risk + issue_correlation + recent_issues
            
            cascade_risks.append({
                'machine_id': dependent_machine,
                'cascade_probability': min(total_risk, 85),
                'reason': f'Same production line ({prod_line})',
                'estimated_impact': f'{np.random.randint(2, 8)} hours downtime',
                'mitigation': 'Pre-emptive inspection recommended'
            })
        
        return sorted(cascade_risks, key=lambda x: x['cascade_probability'], reverse=True)
    
    def calculate_cost_impact(self, machine_id=None):
        """Calculate real-time cost impact in INR (Indian Rupees)"""
        if machine_id:
            logs = self.df[self.df['machine_id'] == machine_id]
        else:
            logs = self.df
        
        # Calculate costs from actual data if available
        if 'total_cost_inr' in logs.columns:
            total_cost = logs['total_cost_inr'].sum()
            downtime_cost = logs['downtime_cost_inr'].sum() if 'downtime_cost_inr' in logs.columns else 0
            parts_cost = logs['parts_cost_inr'].sum() if 'parts_cost_inr' in logs.columns else 0
            labor_cost = logs['labor_cost_inr'].sum() if 'labor_cost_inr' in logs.columns else 0
        else:
            # Fallback calculation for old data format
            total_downtime_hours = logs['downtime_minutes'].sum() / 60
            cost_per_hour = 42000  # Average INR cost per hour for Indian manufacturing
            labor_cost_per_incident = 1500  # Average labor cost in INR
            parts_cost_avg = 5000  # Average parts cost in INR
            
            downtime_cost = total_downtime_hours * cost_per_hour
            labor_cost = len(logs) * labor_cost_per_incident
            parts_cost = logs['parts_replaced'].notna().sum() * parts_cost_avg
            total_cost = downtime_cost + labor_cost + parts_cost
        
        total_downtime_hours = logs['downtime_minutes'].sum() / 60
        
        # Calculate prevented cost (if maintenance was predictive)
        prevented_failures = len(logs[logs['action_taken'] == 'temporary_fix']) * 0.7
        prevented_cost = prevented_failures * 42000 * 4  # 4 hours avg per failure
        
        # Calculate ROI
        roi_percentage = int((prevented_cost / total_cost) * 100) if total_cost > 0 else 0
        
        return {
            'total_downtime_hours': round(total_downtime_hours, 1),
            'downtime_cost': int(downtime_cost) if 'downtime_cost' in locals() else int(total_cost * 0.7),
            'parts_cost': int(parts_cost) if 'parts_cost' in locals() else int(total_cost * 0.2),
            'labor_cost': int(labor_cost) if 'labor_cost' in locals() else int(total_cost * 0.1),
            'total_cost': int(total_cost),
            'cost_per_incident': int(total_cost / len(logs)) if len(logs) > 0 else 0,
            'prevented_cost_potential': int(prevented_cost),
            'roi_opportunity': f"{roi_percentage}%",
            'currency': 'INR'
        }
    
    def calculate_maintenance_efficiency_score(self):
        """Gamification: Score maintenance team performance"""
        total_incidents = len(self.df)
        
        # Positive factors
        permanent_fixes = len(self.df[self.df['action_taken'] == 'part_replacement'])
        inspections = len(self.df[self.df['action_taken'] == 'inspection'])
        
        # Negative factors
        temporary_fixes = len(self.df[self.df['action_taken'] == 'temporary_fix'])
        repeated_issues = len(self.df[self.df['technician_note'].str.contains('again', case=False, na=False)])
        critical_incidents = len(self.df[self.df['criticality'] == 'Critical'])
        
        # Calculate score (0-100)
        score = 50  # Base score
        score += (permanent_fixes / total_incidents) * 20 if total_incidents > 0 else 0
        score += (inspections / total_incidents) * 15 if total_incidents > 0 else 0
        score -= (temporary_fixes / total_incidents) * 15 if total_incidents > 0 else 0
        score -= (repeated_issues / total_incidents) * 10 if total_incidents > 0 else 0
        score -= (critical_incidents / total_incidents) * 10 if total_incidents > 0 else 0
        
        score = max(0, min(100, score))
        
        # Determine grade
        if score >= 85:
            grade = 'A+'
            message = 'Excellent! Proactive maintenance culture'
        elif score >= 75:
            grade = 'A'
            message = 'Very good maintenance practices'
        elif score >= 65:
            grade = 'B'
            message = 'Good, but room for improvement'
        elif score >= 50:
            grade = 'C'
            message = 'Needs improvement - too many temporary fixes'
        else:
            grade = 'D'
            message = 'Critical - reactive maintenance mode'
        
        return {
            'score': int(score),
            'grade': grade,
            'message': message,
            'permanent_fixes': permanent_fixes,
            'temporary_fixes': temporary_fixes,
            'repeated_issues': repeated_issues,
            'improvement_tip': 'Focus on root cause analysis instead of temporary fixes' if temporary_fixes > permanent_fixes else 'Keep up the proactive approach!'
        }
    
    def predict_parts_inventory(self):
        """Predict which parts will be needed soon"""
        # Analyze parts replacement patterns
        parts_used = self.df[self.df['parts_replaced'].notna()]['parts_replaced'].value_counts()
        
        # Get machines with high risk
        high_risk_machines = self.df.groupby('machine_id').size().sort_values(ascending=False).head(5).index
        
        # Predict parts needed
        predictions = []
        
        for part in parts_used.head(5).index:
            # Find machines that used this part
            machines_using_part = self.df[self.df['parts_replaced'] == part]['machine_id'].unique()
            
            # Calculate probability
            usage_frequency = parts_used[part]
            days_span = (self.df['date'].max() - self.df['date'].min()).days
            monthly_usage = (usage_frequency / days_span) * 30 if days_span > 0 else 0
            
            # Check if high-risk machines need this part
            high_risk_overlap = len(set(machines_using_part) & set(high_risk_machines))
            
            probability = min(95, int((monthly_usage * 20) + (high_risk_overlap * 15)))
            
            predictions.append({
                'part': part.title(),
                'probability': probability,
                'estimated_quantity': max(1, int(monthly_usage * 1.5)),
                'lead_time': '3-5 days',
                'machines_affected': list(machines_using_part)[:3],
                'urgency': 'High' if probability > 70 else 'Medium' if probability > 40 else 'Low'
            })
        
        return sorted(predictions, key=lambda x: x['probability'], reverse=True)
    
    def generate_smart_insights(self):
        """AI-generated insights - unique observations"""
        insights = []
        
        # Insight 1: Most problematic time of day
        self.df['hour'] = self.df['date'].dt.hour
        hour_counts = self.df['hour'].value_counts()
        if len(hour_counts) > 0:
            peak_hour = hour_counts.index[0]
            insights.append({
                'icon': '🕐',
                'title': 'Peak Failure Time',
                'insight': f'Most incidents occur around {peak_hour}:00',
                'action': 'Schedule preventive checks before peak hours'
            })
        
        # Insight 2: Issue correlation
        issue_pairs = []
        for machine in self.df['machine_id'].unique():
            machine_logs = self.df[self.df['machine_id'] == machine]
            issues = machine_logs['issue_type'].tolist()
            for i in range(len(issues)-1):
                issue_pairs.append((issues[i], issues[i+1]))
        
        if issue_pairs:
            most_common_pair = Counter(issue_pairs).most_common(1)[0]
            insights.append({
                'icon': '🔗',
                'title': 'Issue Correlation Detected',
                'insight': f'{most_common_pair[0][0]} often followed by {most_common_pair[0][1]}',
                'action': 'When fixing first issue, inspect for second'
            })
        
        # Insight 3: Maintenance response time
        avg_downtime = self.df['downtime_minutes'].mean()
        if avg_downtime > 60:
            insights.append({
                'icon': '⏱️',
                'title': 'Response Time Opportunity',
                'insight': f'Average downtime is {int(avg_downtime)} minutes',
                'action': 'Reduce response time to save costs'
            })
        
        # Insight 4: Production line comparison
        line_incidents = self.df.groupby('production_line').size()
        if len(line_incidents) > 1:
            worst_line = line_incidents.idxmax()
            best_line = line_incidents.idxmin()
            insights.append({
                'icon': '📊',
                'title': 'Production Line Variance',
                'insight': f'{worst_line} has {line_incidents[worst_line]} incidents vs {best_line} with {line_incidents[best_line]}',
                'action': f'Apply best practices from {best_line} to {worst_line}'
            })
        
        # Insight 5: Seasonal pattern
        self.df['month'] = self.df['date'].dt.month
        month_counts = self.df['month'].value_counts()
        if len(month_counts) > 0:
            worst_month = month_counts.index[0]
            month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            insights.append({
                'icon': '📅',
                'title': 'Seasonal Pattern',
                'insight': f'{month_names[worst_month]} shows highest incident rate',
                'action': 'Increase preventive maintenance before this period'
            })
        
        return insights[:4]  # Top 4 insights
    
    def compare_machines(self, machine_ids):
        """Compare multiple machines across key metrics"""
        comparison = []
        
        for machine_id in machine_ids:
            machine_logs = self.df[self.df['machine_id'] == machine_id]
            
            if len(machine_logs) == 0:
                continue
            
            comparison.append({
                'machine_id': machine_id,
                'total_incidents': len(machine_logs),
                'total_downtime': machine_logs['downtime_minutes'].sum(),
                'avg_downtime_per_incident': machine_logs['downtime_minutes'].mean(),
                'temporary_fix_ratio': len(machine_logs[machine_logs['action_taken'] == 'temporary_fix']) / len(machine_logs),
                'most_common_issue': machine_logs['issue_type'].mode()[0] if len(machine_logs) > 0 else 'N/A',
                'days_since_last_incident': (datetime.now() - machine_logs['date'].max()).days
            })
        
        return comparison
    
    def get_risk_heatmap_data(self):
        """Generate data for 3D risk heatmap visualization"""
        heatmap_data = []
        
        for machine in self.df['machine_id'].unique():
            machine_logs = self.df[self.df['machine_id'] == machine]
            
            # Calculate risk dimensions
            frequency_risk = min(100, len(machine_logs) * 5)
            severity_risk = len(machine_logs[machine_logs['criticality'].isin(['High', 'Critical'])]) / len(machine_logs) * 100 if len(machine_logs) > 0 else 0
            recency_risk = 100 - min(100, (datetime.now() - machine_logs['date'].max()).days * 3) if len(machine_logs) > 0 else 0
            
            heatmap_data.append({
                'machine_id': machine,
                'frequency_risk': int(frequency_risk),
                'severity_risk': int(severity_risk),
                'recency_risk': int(recency_risk),
                'overall_risk': int((frequency_risk + severity_risk + recency_risk) / 3),
                'production_line': machine_logs.iloc[0]['production_line']
            })
        
        return sorted(heatmap_data, key=lambda x: x['overall_risk'], reverse=True)
