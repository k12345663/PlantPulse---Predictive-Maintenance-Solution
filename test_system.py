"""
Quick system test to verify all components work
Run this before your demo to ensure everything is functioning
"""

import sys
import os

def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    try:
        import pandas
        import streamlit
        import plotly
        from dotenv import load_dotenv
        print("✅ All required packages installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def test_data():
    """Test that data file exists and is valid"""
    print("\nTesting data...")
    try:
        import pandas as pd
        
        if not os.path.exists('data/maintenance_logs.csv'):
            print("⚠️  Data file not found. Generating...")
            from utils.data_generator import generate_maintenance_logs
            os.makedirs('data', exist_ok=True)
            df = generate_maintenance_logs(200)
            df.to_csv('data/maintenance_logs.csv', index=False)
            print("✅ Data generated successfully")
        else:
            df = pd.read_csv('data/maintenance_logs.csv')
            print(f"✅ Data loaded: {len(df)} records, {len(df['machine_id'].unique())} machines")
        
        return True
    except Exception as e:
        print(f"❌ Data error: {e}")
        return False

def test_agents():
    """Test that all agents can be initialized"""
    print("\nTesting agents...")
    try:
        import pandas as pd
        from agents.log_analyzer import LogAnalyzerAgent
        from agents.failure_predictor import FailurePredictorAgent
        from agents.scheduler import MaintenanceSchedulerAgent
        from agents.assistant import AIAssistantAgent
        
        # Load data
        df = pd.read_csv('data/maintenance_logs.csv')
        
        # Initialize agents
        log_analyzer = LogAnalyzerAgent(df)
        print("  ✅ Log Analyzer Agent initialized")
        
        failure_predictor = FailurePredictorAgent(df)
        print("  ✅ Failure Predictor Agent initialized")
        
        risk_data = failure_predictor.get_all_risk_scores()
        print(f"  ✅ Risk scores calculated for {len(risk_data)} machines")
        
        scheduler = MaintenanceSchedulerAgent(risk_data, df)
        print("  ✅ Scheduler Agent initialized")
        
        assistant = AIAssistantAgent(log_analyzer, failure_predictor, scheduler)
        print("  ✅ AI Assistant Agent initialized")
        
        return True
    except Exception as e:
        print(f"❌ Agent error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_functionality():
    """Test core functionality"""
    print("\nTesting core functionality...")
    try:
        import pandas as pd
        from agents.log_analyzer import LogAnalyzerAgent
        from agents.failure_predictor import FailurePredictorAgent
        from agents.scheduler import MaintenanceSchedulerAgent
        
        df = pd.read_csv('data/maintenance_logs.csv')
        
        # Test log analysis
        log_analyzer = LogAnalyzerAgent(df)
        patterns = log_analyzer.extract_patterns()
        print(f"  ✅ Pattern extraction: {patterns['total_incidents']} incidents analyzed")
        
        # Test risk prediction
        failure_predictor = FailurePredictorAgent(df)
        risk_data = failure_predictor.get_all_risk_scores()
        high_risk = [r for r in risk_data if r['risk_score'] >= 50]
        print(f"  ✅ Risk prediction: {len(high_risk)} high-risk machines identified")
        
        # Test scheduling
        scheduler = MaintenanceSchedulerAgent(risk_data, df)
        schedule = scheduler.generate_schedule(7)
        print(f"  ✅ Schedule generation: {len(schedule)} maintenance tasks scheduled")
        
        # Test machine history
        machines = df['machine_id'].unique()
        if len(machines) > 0:
            history = log_analyzer.get_machine_history(machines[0])
            print(f"  ✅ Machine history: {history['total_incidents']} incidents for {machines[0]}")
        
        return True
    except Exception as e:
        print(f"❌ Functionality error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        llm_provider = os.getenv('LLM_PROVIDER', 'openai')
        print(f"  ℹ️  LLM Provider: {llm_provider}")
        
        if llm_provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY', '')
            if api_key:
                print("  ✅ OpenAI API key configured")
            else:
                print("  ⚠️  OpenAI API key not set (AI Assistant will use fallback)")
        elif llm_provider == 'gemini':
            api_key = os.getenv('GOOGLE_API_KEY', '')
            if api_key:
                print("  ✅ Google API key configured")
            else:
                print("  ⚠️  Google API key not set (AI Assistant will use fallback)")
        
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("PlantPulse AI - System Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Data", test_data()))
    results.append(("Agents", test_agents()))
    results.append(("Functionality", test_functionality()))
    results.append(("Configuration", test_config()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready for demo.")
        print("\nTo run the application:")
        print("  streamlit run app.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
