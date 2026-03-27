"""Configuration settings for PlantPulse AI"""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')  # 'openai' or 'gemini'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

# Risk Scoring Thresholds
RISK_THRESHOLDS = {
    'critical': 70,
    'high': 50,
    'medium': 30,
    'low': 0
}

# Maintenance Scheduling
DEFAULT_SCHEDULE_DAYS = 14
MAINTENANCE_TIME_SLOTS = {
    'weekend': ['08:00', '14:00', '18:00'],
    'weekday': ['18:00']
}

# Data Settings
DATA_PATH = 'data/maintenance_logs.csv'
SAMPLE_DATA_SIZE = 200

# Agent Settings
AGENT_CONFIG = {
    'log_analyzer': {
        'min_repeated_issues': 2,
        'analysis_window_days': 90
    },
    'failure_predictor': {
        'recent_window_days': 30,
        'risk_factors': {
            'recent_incidents': 30,
            'repeated_issues': 25,
            'temporary_fixes': 20,
            'critical_incidents': 15,
            'downtime': 10
        }
    },
    'scheduler': {
        'max_daily_maintenance': 3,
        'estimated_duration_hours': 2
    }
}

def get_llm_config():
    """Get LLM configuration"""
    return {
        'provider': LLM_PROVIDER,
        'api_key': OPENAI_API_KEY if LLM_PROVIDER == 'openai' else GOOGLE_API_KEY,
        'model': 'gpt-3.5-turbo' if LLM_PROVIDER == 'openai' else 'gemini-pro'
    }

def validate_config():
    """Validate configuration"""
    issues = []
    
    if LLM_PROVIDER not in ['openai', 'gemini']:
        issues.append(f"Invalid LLM_PROVIDER: {LLM_PROVIDER}")
    
    if LLM_PROVIDER == 'openai' and not OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY not set")
    
    if LLM_PROVIDER == 'gemini' and not GOOGLE_API_KEY:
        issues.append("GOOGLE_API_KEY not set")
    
    return issues

if __name__ == '__main__':
    print("PlantPulse AI Configuration")
    print("=" * 50)
    print(f"LLM Provider: {LLM_PROVIDER}")
    print(f"Data Path: {DATA_PATH}")
    print(f"Risk Thresholds: {RISK_THRESHOLDS}")
    
    issues = validate_config()
    if issues:
        print("\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ Configuration valid")
