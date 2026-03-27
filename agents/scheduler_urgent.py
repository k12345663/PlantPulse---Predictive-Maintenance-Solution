"""Enhanced Scheduler with Urgent Priority Algorithm"""

from datetime import datetime, timedelta
import numpy as np

class UrgentMaintenanceScheduler:
    """Scheduler with urgent priority for today's faults"""
    
    def __init__(self, risk_data, df):
        self.risk_data = risk_data
        self.df = df
    
    def generate_schedule(self, days_ahead=7):
        """Generate maintenance schedule with URGENT priority for today's faults"""
        schedule = []
        
        # STEP 1: Identify TODAY'S FAULTS (URGENT)
        today = datetime.now().date()
        today_faults = self.df[pd.to_datetime(self.df['date']).dt.date == today]
        urgent_machines = today_faults['machine_id'].unique().tolist()
        
        # STEP 2: Sort machines by priority algorithm
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for machine in self.risk_data:
            machine_id = machine['machine_id']
            risk_score = machine['risk_score']
            
            # URGENT: Today's faults get IMMEDIATE priority
            if machine_id in urgent_machines:
                priority_score = risk_score + 50  # Boost by 50 points
                machine['priority_boost'] = 'URGENT - Fault today'
                machine['boosted_score'] = priority_score
                high_priority.append(machine)
            elif risk_score >= 50:
                machine['boosted_score'] = risk_score
                high_priority.append(machine)
            elif risk_score >= 30:
                machine['boosted_score'] = risk_score
                medium_priority.append(machine)
            else:
                machine['boosted_score'] = risk_score
                low_priority.append(machine)
        
        # Sort by boosted score
        high_priority.sort(key=lambda x: x['boosted_score'], reverse=True)
        medium_priority.sort(key=lambda x: x['boosted_score'], reverse=True)
        
        # STEP 3: Generate time slots with URGENT slots first
        current_date = datetime.now()
        time_slots = self._generate_urgent_time_slots(current_date, days_ahead, len(urgent_machines))
        
        slot_index = 0
        
        # STEP 4: Schedule URGENT machines FIRST (today's faults)
        for machine in high_priority:
            if slot_index >= len(time_slots):
                break
            
            machine_info = self._get_machine_details(machine['machine_id'])
            is_urgent = machine['machine_id'] in urgent_machines
            
            schedule.append({
                'machine_id': machine['machine_id'],
                'risk_score': machine['risk_score'],
                'priority': 'URGENT' if is_urgent else 'High',
                'scheduled_time': time_slots[slot_index],
                'estimated_duration': '2-3 hours' if is_urgent else '1.5-2 hours',
                'production_line': machine_info['production_line'],
                'reason': self._generate_reason(machine, is_urgent),
                'recommended_actions': self._recommend_actions(machine['machine_id']),
                'urgency_flag': '🚨 IMMEDIATE' if is_urgent else '⚠️ High Priority',
                'ml_enhanced': machine.get('ml_anomaly', False)
            })
            slot_index += 1
        
        # STEP 5: Schedule medium priority
        for machine in medium_priority[:5]:
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
                'reason': self._generate_reason(machine, False),
                'recommended_actions': self._recommend_actions(machine['machine_id']),
                'urgency_flag': '🟡 Scheduled',
                'ml_enhanced': machine.get('ml_anomaly', False)
            })
            slot_index += 1
        
        return schedule
    
    def _generate_urgent_time_slots(self, start_date, days, urgent_count):
        """Generate time slots with URGENT slots first"""
        slots = []
        
        # URGENT SLOTS: Today, ASAP
        current_hour = start_date.hour
        
        # If before 6 PM, schedule urgent maintenance today
        if current_hour < 18:
            # Next available slot today
            next_slot = start_date.replace(minute=0, second=0) + timedelta(hours=1)
            for i in range(urgent_count):
                slots.append(next_slot.strftime('%Y-%m-%d %H:%M'))
                next_slot += timedelta(hours=2)  # 2-hour intervals
        else:
            # After hours, schedule for tomorrow morning
            tomorrow = start_date + timedelta(days=1)
            next_slot = tomorrow.replace(hour=6, minute=0, second=0)
            for i in range(urgent_count):
                slots.append(next_slot.strftime('%Y-%m-%d %H:%M'))
                next_slot += timedelta(hours=2)
        
        # REGULAR SLOTS: Weekends and off-hours
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
    
    def _generate_reason(self, machine, is_urgent):
        """Generate human-readable reason for scheduling"""
        factors = machine.get('factors', [])
        
        if is_urgent:
            reason = f"🚨 URGENT: Fault reported today. Risk Score: {machine['risk_score']}/100. "
        else:
            reason = f"Risk Score: {machine['risk_score']}/100. "
        
        if factors:
            reason += " ".join(factors[:2])  # Top 2 factors
        else:
            reason += "Preventive maintenance recommended"
        
        if machine.get('ml_anomaly'):
            reason += f" 🤖 ML detected anomalous behavior."
        
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
        
        if 'hydraulic' in issue_types.index:
            actions.append("Check hydraulic pressure")
            actions.append("Inspect seals and hoses")
        
        return actions[:3] if actions else ["General inspection and preventive maintenance"]
    
    def optimize_by_production_line(self, schedule):
        """Group maintenance by production line to minimize disruption"""
        from collections import defaultdict
        
        by_line = defaultdict(list)
        for item in schedule:
            by_line[item['production_line']].append(item)
        
        return dict(by_line)
    
    def get_urgent_machines_today(self):
        """Get list of machines with faults reported today"""
        today = datetime.now().date()
        today_faults = self.df[pd.to_datetime(self.df['date']).dt.date == today]
        
        urgent_list = []
        for machine_id in today_faults['machine_id'].unique():
            machine_faults = today_faults[today_faults['machine_id'] == machine_id]
            urgent_list.append({
                'machine_id': machine_id,
                'fault_count_today': len(machine_faults),
                'latest_issue': machine_faults.iloc[-1]['issue_type'],
                'latest_time': machine_faults.iloc[-1]['date'],
                'criticality': machine_faults.iloc[-1]['criticality']
            })
        
        return urgent_list

# Import pandas for date operations
import pandas as pd
