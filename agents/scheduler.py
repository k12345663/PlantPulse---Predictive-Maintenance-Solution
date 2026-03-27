from datetime import datetime, timedelta

class MaintenanceSchedulerAgent:
    """Agent for generating optimized maintenance schedules"""
    
    def __init__(self, risk_data, df):
        self.risk_data = risk_data
        self.df = df
    
    def generate_schedule(self, days_ahead=7):
        """Generate maintenance schedule for next N days"""
        schedule = []
        
        # Sort machines by risk score
        high_priority = [m for m in self.risk_data if m['risk_score'] >= 50]
        medium_priority = [m for m in self.risk_data if 30 <= m['risk_score'] < 50]
        
        current_date = datetime.now()
        time_slots = self._generate_time_slots(current_date, days_ahead)
        
        slot_index = 0
        
        # Schedule high priority first
        for machine in high_priority:
            if slot_index >= len(time_slots):
                break
            
            machine_info = self._get_machine_details(machine['machine_id'])
            
            schedule.append({
                'machine_id': machine['machine_id'],
                'risk_score': machine['risk_score'],
                'priority': 'High',
                'scheduled_time': time_slots[slot_index],
                'estimated_duration': '2-3 hours',
                'production_line': machine_info['production_line'],
                'reason': self._generate_reason(machine),
                'recommended_actions': self._recommend_actions(machine['machine_id'])
            })
            slot_index += 1
        
        # Schedule medium priority
        for machine in medium_priority[:5]:  # Limit to top 5 medium priority
            if slot_index >= len(time_slots):
                break
            
            machine_info = self._get_machine_details(machine['machine_id'])
            
            schedule.append({
                'machine_id': machine['machine_id'],
                'risk_score': machine['risk_score'],
                'priority': 'Medium',
                'scheduled_time': time_slots[slot_index],
                'estimated_duration': '1-2 hours',
                'production_line': machine_info['production_line'],
                'reason': self._generate_reason(machine),
                'recommended_actions': self._recommend_actions(machine['machine_id'])
            })
            slot_index += 1
        
        return schedule
    
    def _generate_time_slots(self, start_date, days):
        """Generate maintenance time slots (weekends and off-hours)"""
        slots = []
        
        for day in range(days):
            current = start_date + timedelta(days=day)
            
            # Weekend slots (more available)
            if current.weekday() >= 5:  # Saturday or Sunday
                slots.append(current.replace(hour=8, minute=0).strftime('%Y-%m-%d %H:%M'))
                slots.append(current.replace(hour=14, minute=0).strftime('%Y-%m-%d %H:%M'))
                slots.append(current.replace(hour=18, minute=0).strftime('%Y-%m-%d %H:%M'))
            else:
                # Weekday off-hours
                slots.append(current.replace(hour=18, minute=0).strftime('%Y-%m-%d %H:%M'))
        
        return slots
    
    def _get_machine_details(self, machine_id):
        """Get machine details from logs"""
        machine_logs = self.df[self.df['machine_id'] == machine_id]
        
        if len(machine_logs) > 0:
            return {
                'production_line': machine_logs.iloc[0]['production_line'],
                'last_issue': machine_logs.iloc[-1]['issue_type']
            }
        return {'production_line': 'Unknown', 'last_issue': 'Unknown'}
    
    def _generate_reason(self, machine):
        """Generate human-readable reason for scheduling"""
        factors = machine.get('factors', [])
        
        if not factors:
            return f"Preventive maintenance recommended"
        
        reason = f"Risk Score: {machine['risk_score']}/100. "
        reason += " ".join(factors[:2])  # Top 2 factors
        
        return reason
    
    def _recommend_actions(self, machine_id):
        """Recommend specific maintenance actions"""
        machine_logs = self.df[self.df['machine_id'] == machine_id]
        issue_types = machine_logs['issue_type'].value_counts()
        
        actions = []
        
        if 'vibration' in issue_types.index:
            actions.append("Inspect and replace bearings")
            actions.append("Check alignment and balance")
        
        if 'overheating' in issue_types.index:
            actions.append("Clean cooling system")
            actions.append("Check motor windings")
        
        if 'lubrication' in issue_types.index:
            actions.append("Full lubrication system service")
            actions.append("Replace seals if needed")
        
        if 'electrical' in issue_types.index:
            actions.append("Inspect electrical connections")
            actions.append("Test voltage and current")
        
        if 'mechanical' in issue_types.index:
            actions.append("Check belts and couplings")
            actions.append("Inspect for wear and tear")
        
        return actions[:3] if actions else ["General inspection and preventive maintenance"]
    
    def optimize_by_production_line(self, schedule):
        """Group maintenance by production line to minimize disruption"""
        from collections import defaultdict
        
        by_line = defaultdict(list)
        for item in schedule:
            by_line[item['production_line']].append(item)
        
        return dict(by_line)
