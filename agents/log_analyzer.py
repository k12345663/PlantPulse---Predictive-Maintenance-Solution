import pandas as pd
import re
from collections import Counter

class LogAnalyzerAgent:
    """Agent for analyzing maintenance logs and extracting structured insights"""
    
    def __init__(self, df):
        self.df = df
        self.analysis_cache = {}
    
    def extract_patterns(self, machine_id=None):
        """Extract recurring patterns from logs"""
        df = self.df if machine_id is None else self.df[self.df['machine_id'] == machine_id]
        
        patterns = {
            'total_incidents': len(df),
            'issue_distribution': df['issue_type'].value_counts().to_dict(),
            'repeated_issues': self._find_repeated_issues(df),
            'downtime_total': df['downtime_minutes'].sum(),
            'avg_downtime': df['downtime_minutes'].mean(),
            'temporary_fixes': len(df[df['action_taken'] == 'temporary_fix']),
            'critical_incidents': len(df[df['criticality'].isin(['High', 'Critical'])])
        }
        
        return patterns
    
    def _find_repeated_issues(self, df):
        """Identify machines with repeated similar issues"""
        repeated = {}
        
        for machine in df['machine_id'].unique():
            machine_logs = df[df['machine_id'] == machine]
            issue_counts = machine_logs['issue_type'].value_counts()
            
            # Issues appearing 2+ times are considered repeated
            repeated_issues = issue_counts[issue_counts >= 2].to_dict()
            if repeated_issues:
                repeated[machine] = repeated_issues
        
        return repeated
    
    def get_machine_history(self, machine_id):
        """Get detailed history for a specific machine"""
        machine_logs = self.df[self.df['machine_id'] == machine_id].copy()
        machine_logs = machine_logs.sort_values('date', ascending=False)
        
        return {
            'recent_logs': machine_logs.head(10).to_dict('records'),
            'total_incidents': len(machine_logs),
            'issue_types': machine_logs['issue_type'].value_counts().to_dict(),
            'total_downtime': machine_logs['downtime_minutes'].sum(),
            'last_incident': machine_logs.iloc[0]['date'] if len(machine_logs) > 0 else None,
            'temporary_fix_count': len(machine_logs[machine_logs['action_taken'] == 'temporary_fix'])
        }
    
    def search_logs(self, query):
        """Search logs using keyword matching"""
        query_lower = query.lower()
        
        # Search in technician notes
        matches = self.df[
            self.df['technician_note'].str.lower().str.contains(query_lower, na=False) |
            self.df['issue_type'].str.lower().str.contains(query_lower, na=False)
        ]
        
        return matches.to_dict('records')
    
    def get_timeline_analysis(self, machine_id, days=30):
        """Analyze incident timeline for a machine"""
        from datetime import datetime, timedelta
        
        machine_logs = self.df[self.df['machine_id'] == machine_id].copy()
        machine_logs['date'] = pd.to_datetime(machine_logs['date'])
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_logs = machine_logs[machine_logs['date'] >= cutoff_date]
        
        return {
            'incident_count': len(recent_logs),
            'incidents': recent_logs.sort_values('date').to_dict('records'),
            'trend': 'increasing' if len(recent_logs) > 3 else 'stable'
        }
