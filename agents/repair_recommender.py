"""Component-Level Repair Recommender with YouTube Video Links"""

class RepairRecommender:
    """Recommend specific components to repair/replace with video tutorials"""
    
    def __init__(self):
        # Component repair database with YouTube links
        self.repair_database = {
            'vibration': {
                'components': ['Bearing', 'Motor Mount', 'Coupling', 'Belt'],
                'primary_component': 'Bearing',
                'temporary_fix': 'Tighten mounting bolts, check alignment',
                'permanent_fix': 'Replace worn bearings',
                'estimated_cost_inr': 8500,
                'estimated_time_hours': 2,
                'youtube_videos': [
                    {
                        'title': 'Machine Bearing Replacement Tutorial',
                        'url': 'https://www.youtube.com/watch?v=ptYcRcRO_h4',
                        'duration': '12:35',
                        'views': 'Professional Guide'
                    },
                    {
                        'title': 'Motor Vibration Troubleshooting',
                        'url': 'https://www.youtube.com/watch?v=30KNFHhahag',
                        'duration': '15:20',
                        'views': 'Expert Tutorial'
                    }
                ],
                'tools_required': ['Bearing puller', 'Torque wrench', 'Dial indicator'],
                'safety_precautions': ['Lockout/tagout', 'Wear safety glasses', 'Use proper lifting']
            },
            'overheating': {
                'components': ['Cooling Fan', 'Thermal Sensor', 'Motor Windings', 'Ventilation System'],
                'primary_component': 'Cooling Fan',
                'temporary_fix': 'Clean ventilation, reduce load',
                'permanent_fix': 'Replace cooling fan and clean motor',
                'estimated_cost_inr': 12000,
                'estimated_time_hours': 3,
                'youtube_videos': [
                    {
                        'title': 'Motor Overheating - Causes & Solutions',
                        'url': 'https://www.youtube.com/watch?v=7SyeodSfUug',
                        'duration': '18:45',
                        'views': 'Comprehensive Guide'
                    },
                    {
                        'title': 'How to Replace Industrial Cooling Fan',
                        'url': 'https://www.youtube.com/watch?v=k0ovUHEOtyE',
                        'duration': '14:20',
                        'views': 'Step-by-Step'
                    }
                ],
                'tools_required': ['Multimeter', 'Screwdriver set', 'Thermal camera'],
                'safety_precautions': ['Allow cooling time', 'Check electrical connections', 'Verify voltage']
            },
            'lubrication': {
                'components': ['Oil Seal', 'Lubrication Pump', 'Oil Filter', 'Bearing'],
                'primary_component': 'Oil Seal',
                'temporary_fix': 'Add lubricant, check oil level',
                'permanent_fix': 'Replace seals and change oil',
                'estimated_cost_inr': 6500,
                'estimated_time_hours': 1.5,
                'youtube_videos': [
                    {
                        'title': 'Machine Lubrication Best Practices',
                        'url': 'https://www.youtube.com/watch?v=evpaTW2WJ5Y',
                        'duration': '16:30',
                        'views': 'Maintenance Guide'
                    },
                    {
                        'title': 'How to Replace Oil Seals',
                        'url': 'https://www.youtube.com/watch?v=ptYcRcRO_h4',
                        'duration': '12:35',
                        'views': 'Professional Tutorial'
                    }
                ],
                'tools_required': ['Oil pump', 'Seal puller', 'Cleaning solvent'],
                'safety_precautions': ['Dispose oil properly', 'Avoid skin contact', 'Use gloves']
            },
            'electrical': {
                'components': ['Contactor', 'Relay', 'Wiring', 'Circuit Breaker'],
                'primary_component': 'Contactor',
                'temporary_fix': 'Tighten connections, reset breaker',
                'permanent_fix': 'Replace faulty contactor',
                'estimated_cost_inr': 4500,
                'estimated_time_hours': 1,
                'youtube_videos': [
                    {
                        'title': 'Electrical Troubleshooting for Industrial Machines',
                        'url': 'https://www.youtube.com/watch?v=qkd1vEyEit8',
                        'duration': '22:15',
                        'views': 'Expert Guide'
                    },
                    {
                        'title': 'How to Replace a Contactor',
                        'url': 'https://www.youtube.com/watch?v=Hr0H85WaACQ',
                        'duration': '10:45',
                        'views': 'Step-by-Step'
                    }
                ],
                'tools_required': ['Multimeter', 'Insulated tools', 'Wire stripper'],
                'safety_precautions': ['Lockout/tagout CRITICAL', 'Verify zero voltage', 'Use insulated tools']
            },
            'mechanical': {
                'components': ['Belt', 'Coupling', 'Gear', 'Shaft'],
                'primary_component': 'Belt',
                'temporary_fix': 'Adjust belt tension',
                'permanent_fix': 'Replace worn belt',
                'estimated_cost_inr': 3200,
                'estimated_time_hours': 0.5,
                'youtube_videos': [
                    {
                        'title': 'Belt Replacement and Tensioning',
                        'url': 'https://www.youtube.com/watch?v=fc3jmp4ske4',
                        'duration': '13:40',
                        'views': 'Professional Guide'
                    },
                    {
                        'title': 'Mechanical Drive Maintenance',
                        'url': 'https://www.youtube.com/watch?v=MrBI1hRTgx4',
                        'duration': '19:25',
                        'views': 'Complete Tutorial'
                    }
                ],
                'tools_required': ['Belt tension gauge', 'Alignment tool', 'Wrench set'],
                'safety_precautions': ['Stop machine completely', 'Check for pinch points', 'Wear gloves']
            },
            'hydraulic': {
                'components': ['Hydraulic Pump', 'Pressure Valve', 'Hydraulic Hose', 'Cylinder Seal'],
                'primary_component': 'Hydraulic Pump',
                'temporary_fix': 'Check fluid level, bleed air',
                'permanent_fix': 'Replace pump or seals',
                'estimated_cost_inr': 28000,
                'estimated_time_hours': 4,
                'youtube_videos': [
                    {
                        'title': 'Hydraulic System Troubleshooting',
                        'url': 'https://www.youtube.com/watch?v=JT6Q-CMnzFs',
                        'duration': '25:30',
                        'views': 'Expert Guide'
                    },
                    {
                        'title': 'How to Replace Hydraulic Pump',
                        'url': 'https://www.youtube.com/watch?v=8msF1eDDeJM',
                        'duration': '18:50',
                        'views': 'Professional Tutorial'
                    }
                ],
                'tools_required': ['Hydraulic pressure gauge', 'Wrench set', 'Seal kit'],
                'safety_precautions': ['Release pressure first', 'Wear face shield', 'Check for leaks']
            }
        }
    
    def get_repair_recommendation(self, issue_type, action_taken='temporary_fix'):
        """Get detailed repair recommendation for an issue"""
        issue_type = issue_type.lower()
        
        if issue_type not in self.repair_database:
            return self._get_generic_recommendation()
        
        repair_info = self.repair_database[issue_type]
        
        return {
            'issue_type': issue_type.title(),
            'primary_component': repair_info['primary_component'],
            'all_components': repair_info['components'],
            'recommended_action': repair_info['permanent_fix'] if action_taken == 'temporary_fix' else repair_info['temporary_fix'],
            'temporary_fix': repair_info['temporary_fix'],
            'permanent_fix': repair_info['permanent_fix'],
            'estimated_cost_inr': repair_info['estimated_cost_inr'],
            'estimated_time_hours': repair_info['estimated_time_hours'],
            'youtube_videos': repair_info['youtube_videos'],
            'tools_required': repair_info['tools_required'],
            'safety_precautions': repair_info['safety_precautions'],
            'urgency': 'HIGH' if action_taken == 'temporary_fix' else 'MEDIUM'
        }
    
    def get_component_details(self, component_name):
        """Get details about a specific component"""
        component_db = {
            'Bearing': {
                'description': 'Reduces friction between moving parts',
                'lifespan_hours': 10000,
                'cost_range_inr': '5000-15000',
                'failure_signs': ['Vibration', 'Noise', 'Heat', 'Wear debris']
            },
            'Cooling Fan': {
                'description': 'Dissipates heat from motor',
                'lifespan_hours': 15000,
                'cost_range_inr': '8000-20000',
                'failure_signs': ['Overheating', 'No airflow', 'Noise', 'Blade damage']
            },
            'Belt': {
                'description': 'Transmits power between pulleys',
                'lifespan_hours': 5000,
                'cost_range_inr': '2000-5000',
                'failure_signs': ['Slipping', 'Cracking', 'Glazing', 'Misalignment']
            },
            'Oil Seal': {
                'description': 'Prevents lubricant leakage',
                'lifespan_hours': 8000,
                'cost_range_inr': '3000-8000',
                'failure_signs': ['Oil leaks', 'Contamination', 'Wear', 'Hardening']
            },
            'Contactor': {
                'description': 'Electrical switching device',
                'lifespan_hours': 20000,
                'cost_range_inr': '3000-6000',
                'failure_signs': ['Arcing', 'Burning smell', 'Failure to close', 'Overheating']
            },
            'Hydraulic Pump': {
                'description': 'Generates hydraulic pressure',
                'lifespan_hours': 12000,
                'cost_range_inr': '20000-40000',
                'failure_signs': ['Pressure drop', 'Noise', 'Leaks', 'Overheating']
            }
        }
        
        return component_db.get(component_name, {
            'description': 'Component information not available',
            'lifespan_hours': 'Unknown',
            'cost_range_inr': 'Contact supplier',
            'failure_signs': ['Consult manual']
        })
    
    def _get_generic_recommendation(self):
        """Generic recommendation for unknown issues"""
        return {
            'issue_type': 'General',
            'primary_component': 'Multiple Components',
            'all_components': ['Consult manual'],
            'recommended_action': 'Comprehensive inspection required',
            'temporary_fix': 'Monitor closely',
            'permanent_fix': 'Detailed diagnosis needed',
            'estimated_cost_inr': 10000,
            'estimated_time_hours': 2,
            'youtube_videos': [
                {
                    'title': 'General Machine Troubleshooting',
                    'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'duration': '15:00',
                    'views': '1.5M'
                }
            ],
            'tools_required': ['Basic tool kit', 'Multimeter'],
            'safety_precautions': ['Follow lockout/tagout', 'Wear PPE'],
            'urgency': 'MEDIUM'
        }
    
    def get_repair_history_analysis(self, machine_logs):
        """Analyze repair history to predict next failure"""
        if len(machine_logs) == 0:
            return None
        
        # Count issue types
        issue_counts = machine_logs['issue_type'].value_counts()
        
        # Find most common issue
        most_common_issue = issue_counts.index[0] if len(issue_counts) > 0 else 'unknown'
        
        # Count temporary fixes
        temp_fixes = len(machine_logs[machine_logs['action_taken'] == 'temporary_fix'])
        
        # Get recommendation
        recommendation = self.get_repair_recommendation(most_common_issue)
        
        return {
            'most_common_issue': most_common_issue,
            'occurrence_count': int(issue_counts[most_common_issue]) if most_common_issue in issue_counts else 0,
            'temporary_fixes_count': temp_fixes,
            'recommendation': recommendation,
            'next_likely_failure': recommendation['primary_component'],
            'preventive_action': recommendation['permanent_fix']
        }
