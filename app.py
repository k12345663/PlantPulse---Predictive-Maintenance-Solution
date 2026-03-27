import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Import agents
from agents.log_analyzer import LogAnalyzerAgent
from agents.failure_predictor_ml import FailurePredictorMLAgent
from agents.scheduler_urgent import UrgentMaintenanceScheduler
from agents.assistant import AIAssistantAgent
from agents.insights_engine import InsightsEngine
from database import MaintenanceDatabase

# Page config
st.set_page_config(
    page_title="PlantPulse AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .risk-high {
        color: #d62728;
        font-weight: bold;
    }
    .risk-medium {
        color: #ff7f0e;
        font-weight: bold;
    }
    .risk-low {
        color: #2ca02c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database():
    """Get database instance"""
    db = MaintenanceDatabase()
    
    # Check if database is empty
    stats = db.get_stats()
    if stats['total_logs'] == 0:
        # Load CSV data if available
        if os.path.exists('data/maintenance_logs.csv'):
            db.load_csv_to_db()
        else:
            # Generate sample data
            from utils.data_generator import generate_maintenance_logs
            df = generate_maintenance_logs(200)
            os.makedirs('data', exist_ok=True)
            df.to_csv('data/maintenance_logs.csv', index=False)
            db.load_csv_to_db()
    
    return db

def load_data(db):
    """Load maintenance logs from database"""
    df = db.get_all_logs()
    # Rename columns to match agent expectations
    df = df.rename(columns={
        'log_date': 'date',
        'issue_category': 'issue_type'
    })
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    return df

def initialize_agents(df):
    """Initialize all AI agents"""
    log_analyzer = LogAnalyzerAgent(df)
    failure_predictor = FailurePredictorMLAgent(df)
    risk_data = failure_predictor.get_all_risk_scores()

    # Enrich each risk entry with predicted_window
    for r in risk_data:
        pw = failure_predictor.predict_failure_window(r['machine_id'])
        r['predicted_window'] = pw['predicted_window']

    scheduler = UrgentMaintenanceScheduler(risk_data, df)
    assistant = AIAssistantAgent(log_analyzer, failure_predictor, scheduler)
    insights_engine = InsightsEngine(df)

    return log_analyzer, failure_predictor, scheduler, assistant, risk_data, insights_engine

def main():
    # Header
    st.markdown('<p class="main-header">🏭 PlantPulse AI</p>', unsafe_allow_html=True)
    st.markdown("**Predictive Maintenance Intelligence System**")
    
    # Initialize database
    db = get_database()
    
    # Load data and initialize agents
    df = load_data(db)
    log_analyzer, failure_predictor, scheduler, assistant, risk_data, insights_engine = initialize_agents(df)
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["🏭 Visual Overview", "🎯 Insights Dashboard", "🔬 ML Comparison", "🧠 LLM Comparison", "📊 Dashboard", "📋 Logs", "➕ Add New Log", "⚠️ Risk Analysis", "📅 Schedule", "🤖 AI Assistant", "📞 Voice Agent"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**PlantPulse AI** uses multi-agent architecture to predict failures "
        "and optimize maintenance schedules."
    )
    
    # Page routing
    if page == "🏭 Visual Overview":
        show_visual_overview(df, risk_data, failure_predictor, db)
    elif page == "🎯 Insights Dashboard":
        show_insights_dashboard(insights_engine, df, risk_data, db)
    elif page == "🔬 ML Comparison":
        show_ml_comparison(df, failure_predictor)
    elif page == "🧠 LLM Comparison":
        show_llm_comparison(df, risk_data, failure_predictor)
    elif page == "📊 Dashboard":
        show_dashboard(df, risk_data, log_analyzer, db)
    elif page == "📋 Logs":
        show_logs(df, db)
    elif page == "➕ Add New Log":
        show_add_log(db)
    elif page == "⚠️ Risk Analysis":
        show_risk_analysis(risk_data, failure_predictor, df)
    elif page == "📅 Schedule":
        show_schedule(scheduler, risk_data)
    elif page == "🤖 AI Assistant":
        show_assistant(assistant)
    elif page == "📞 Voice Agent":
        show_voice_agent(df, risk_data, scheduler)

def show_visual_overview(df, risk_data, failure_predictor, db):
    """🏭 Visual Overview - Machine Status & Problems"""
    st.header("🏭 Visual Machine Overview")
    st.markdown("**Real-time machine health monitoring and issue tracking**")
    
    # Add explanation
    with st.expander("ℹ️ Understanding the Indicators", expanded=False):
        st.markdown("""
        **Risk Level (🔴🟠🟡🟢):**
        - Based on 7 factors: frequency, repeated issues, temporary fixes, critical incidents, downtime, acceleration, and ML
        - Critical (70-100): Failure likely in 1-7 days
        - High (50-69): Failure likely in 1-2 weeks
        - Medium (30-49): Failure likely in 2-4 weeks
        - Low (0-29): Failure likely in 4+ weeks
        
        **ML Status (🤖 Anomaly / ✓ Normal):**
        - ML analyzes 6 behavior patterns: incident count, downtime, temp fix ratio, critical ratio, recent incidents, issue diversity
        - 🤖 Anomaly: Machine behavior is unusual compared to others (even if risk is low)
        - ✓ Normal: Machine behavior follows expected patterns (even if risk is high)
        
        **Example:** A machine can be Critical (many incidents) but ML Normal (incidents follow expected patterns)
        """)
    
    # Summary metrics at top
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        critical_count = len([r for r in risk_data if r['risk_level'] == 'Critical'])
        st.metric("Critical Machines", critical_count, delta=None if critical_count == 0 else f"{critical_count} need attention")
    with col2:
        high_count = len([r for r in risk_data if r['risk_level'] == 'High'])
        st.metric("High Risk Machines", high_count)
    with col3:
        last_7_days = df[df['date'] >= datetime.now() - timedelta(days=7)]
        st.metric("Incidents (7 days)", len(last_7_days))
    with col4:
        total_downtime = last_7_days['downtime_minutes'].sum()
        st.metric("Downtime (7 days)", f"{total_downtime} min")
    
    st.markdown("---")
    
    # Get stats for each machine
    machine_stats = []
    for risk in risk_data:
        machine_id = risk['machine_id']
        machine_logs = df[df['machine_id'] == machine_id]
        recent_7_days = machine_logs[machine_logs['date'] >= datetime.now() - timedelta(days=7)]
        
        # Get top issues
        top_issues = machine_logs['issue_type'].value_counts().head(2).to_dict()

        # Predicted failure window (once, stored here)
        fail_pred = failure_predictor.predict_failure_window(machine_id)
        predicted_window = fail_pred.get('predicted_window', 'N/A')
        
        machine_stats.append({
            'machine_id': machine_id,
            'risk_score': risk['risk_score'],
            'risk_level': risk['risk_level'],
            'total_incidents': len(machine_logs),
            'recent_incidents': len(recent_7_days),
            'ml_anomaly': risk.get('ml_anomaly', False),
            'production_line': machine_logs.iloc[0]['production_line'] if len(machine_logs) > 0 else 'Unknown',
            'top_issues': top_issues,
            'predicted_window': predicted_window,
        })
    
    # Machine Status Grid
    st.subheader("Machine Health Status")
    
    # Row 1: M1-M5
    cols = st.columns(5)
    for idx, machine in enumerate(machine_stats[:5]):
        with cols[idx]:
            color = {'Critical': '#d62728', 'High': '#ff7f0e', 'Medium': '#ffbb78', 'Low': '#2ca02c'}[machine['risk_level']]
            emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}[machine['risk_level']]
            
            st.markdown(f"""
            <div style='text-align: center; padding: 12px; background-color: {color}15; 
                        border-radius: 8px; border: 2px solid {color}; margin-bottom: 8px;'>
                <h3 style='margin: 0; font-size: 1.3em;'>{emoji} {machine['machine_id']}</h3>
                <h4 style='color: {color}; margin: 3px 0;'>{machine['risk_score']}/100</h4>
                <p style='margin: 2px 0; font-size: 0.85em;'>{machine['risk_level']}</p>
                <p style='margin: 2px 0; font-size: 0.75em; color: #666;'>{machine['total_incidents']} total | {machine['recent_incidents']} recent</p>
                <p style='margin: 2px 0; font-size: 0.75em; color: #444;'>⏰ {machine['predicted_window']}</p>
                {f"<p style='margin: 2px 0; font-size: 0.75em; color: #d62728;'>🤖 Anomaly</p>" if machine['ml_anomaly'] else ""}
            </div>
            """, unsafe_allow_html=True)
    
    # Row 2: M6-M10
    cols = st.columns(5)
    for idx, machine in enumerate(machine_stats[5:10]):
        with cols[idx]:
            color = {'Critical': '#d62728', 'High': '#ff7f0e', 'Medium': '#ffbb78', 'Low': '#2ca02c'}[machine['risk_level']]
            emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}[machine['risk_level']]
            
            st.markdown(f"""
            <div style='text-align: center; padding: 12px; background-color: {color}15; 
                        border-radius: 8px; border: 2px solid {color}; margin-bottom: 8px;'>
                <h3 style='margin: 0; font-size: 1.3em;'>{emoji} {machine['machine_id']}</h3>
                <h4 style='color: {color}; margin: 3px 0;'>{machine['risk_score']}/100</h4>
                <p style='margin: 2px 0; font-size: 0.85em;'>{machine['risk_level']}</p>
                <p style='margin: 2px 0; font-size: 0.75em; color: #666;'>{machine['total_incidents']} total | {machine['recent_incidents']} recent</p>
                <p style='margin: 2px 0; font-size: 0.75em; color: #444;'>⏰ {machine['predicted_window']}</p>
                {f"<p style='margin: 2px 0; font-size: 0.75em; color: #d62728;'>🤖 Anomaly</p>" if machine['ml_anomaly'] else ""}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Problem Machines - Detailed View
    st.subheader("⚠️ Machines Requiring Attention")
    
    problem_machines = sorted([m for m in machine_stats if m['risk_level'] in ['Critical', 'High']], 
                             key=lambda x: x['risk_score'], reverse=True)
    
    if problem_machines:
        # Import repair recommender
        from agents.repair_recommender import RepairRecommender
        repair_recommender = RepairRecommender()
        
        for machine in problem_machines:
            machine_id = machine['machine_id']
            machine_logs = df[df['machine_id'] == machine_id]
            risk_info = failure_predictor.calculate_risk_score(machine_id)
            
            # Get most common issue for repair recommendation
            most_common_issue = machine_logs['issue_type'].mode()[0] if len(machine_logs['issue_type'].mode()) > 0 else 'vibration'
            repair_recommendation = repair_recommender.get_repair_recommendation(most_common_issue)
            
            # Color coding
            border_color = '#d62728' if machine['risk_level'] == 'Critical' else '#ff7f0e'
            
            with st.expander(f"{'🔴' if machine['risk_level'] == 'Critical' else '🟠'} {machine_id} - {machine['risk_level']} ({machine['risk_score']}/100)", expanded=False):
                
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Incidents", machine['total_incidents'])
                with col2:
                    st.metric("Recent (7d)", machine['recent_incidents'])
                with col3:
                    st.metric("Predicted Failure", machine['predicted_window'])
                with col4:
                    if machine['ml_anomaly']:
                        st.metric("ML Status", "🤖 Anomaly")
                        st.caption("ML detected unusual behavior pattern")
                    else:
                        st.metric("ML Status", "✓ Normal")
                        st.caption("Behavior within normal range")
                
                # Issue breakdown
                st.markdown("**Issue Breakdown:**")
                if machine['top_issues']:
                    issue_cols = st.columns(len(machine['top_issues']))
                    for idx, (issue, count) in enumerate(machine['top_issues'].items()):
                        with issue_cols[idx]:
                            st.info(f"**{issue.title()}**: {count} times")
                
                # Repair Recommendation with YouTube Videos
                st.markdown("---")
                st.markdown("### 🔧 Recommended Solution")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"**Primary Issue:** {repair_recommendation['issue_type']}")
                    st.markdown(f"**Component to Replace:** {repair_recommendation['primary_component']}")
                    st.markdown(f"**Estimated Cost:** ₹{repair_recommendation['estimated_cost_inr']:,}")
                    st.markdown(f"**Estimated Time:** {repair_recommendation['estimated_time_hours']} hours")
                
                with col2:
                    st.markdown(f"**Temporary Fix:** {repair_recommendation['temporary_fix']}")
                    st.markdown(f"**Permanent Fix:** {repair_recommendation['permanent_fix']}")
                    st.markdown(f"**Urgency:** {repair_recommendation['urgency']}")
                
                # YouTube Video Links
                st.markdown("**📹 Repair Tutorial Videos:**")
                video_cols = st.columns(2)
                for idx, video in enumerate(repair_recommendation['youtube_videos']):
                    with video_cols[idx]:
                        st.markdown(f"""
                        <div style='padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin: 5px 0;'>
                            <strong>🎥 {video['title']}</strong><br>
                            <small>⏱️ {video['duration']} | 👁️ {video['views']}</small><br>
                            <a href="{video['url']}" target="_blank" style='color: #1f77b4;'>▶️ Watch Tutorial</a>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Risk factors
                st.markdown("---")
                st.markdown("**Key Risk Factors:**")
                factors_to_show = risk_info['factors'][:4]  # Show top 4 factors
                for factor in factors_to_show:
                    st.markdown(f"• {factor}")
                
                # Recent maintenance logs
                st.markdown("**Recent Maintenance History:**")
                recent_logs = machine_logs.sort_values('date', ascending=False).head(5)
                
                for idx, (_, log) in enumerate(recent_logs.iterrows()):
                    log_date = pd.to_datetime(log['date']).strftime('%b %d, %H:%M')
                    criticality_emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(log.get('criticality', 'Medium'), '⚪')
                    
                    st.markdown(f"""
                    <div style='padding: 8px; background-color: #f8f9fa; border-left: 3px solid {border_color}; 
                                border-radius: 4px; margin: 4px 0; font-size: 0.9em;'>
                        <div style='display: flex; justify-content: space-between; margin-bottom: 4px;'>
                            <strong>{criticality_emoji} {log_date}</strong>
                            <span style='color: #666;'>{log['issue_type'].replace('_', ' ').title()}</span>
                        </div>
                        <div style='color: #555; font-style: italic; margin-bottom: 4px;'>
                            "{log['technician_note'][:80]}{'...' if len(log['technician_note']) > 80 else ''}"
                        </div>
                        <div style='font-size: 0.85em; color: #888;'>
                            Action: {log['action_taken'].replace('_', ' ').title()} • 
                            Downtime: {log['downtime_minutes']} min
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Quick LLM Recommendation button
                st.markdown("---")
                st.markdown("### 🧠 AI Recommendation")
                
                btn_key = f"llm_btn_{machine_id}"
                result_key = f"llm_result_{machine_id}"
                
                if st.button(f"Get AI Recommendation for {machine_id}", key=btn_key):
                    from agents.llm_comparison import LLMComparisonEngine
                    recent_7d_count = len(machine_logs[machine_logs['date'] >= datetime.now() - timedelta(days=7)])
                    temp_fix_count = len(machine_logs[machine_logs['action_taken'] == 'temporary_fix'])
                    
                    with st.spinner("Querying all AI models... (may take 15-40s for Ollama models)"):
                        engine = LLMComparisonEngine()
                        result = engine.compare(
                            machine_id, most_common_issue,
                            risk_info['risk_score'], risk_info['risk_level'],
                            recent_7d_count, int(machine_logs['downtime_minutes'].sum()),
                            temp_fix_count, risk_info['factors'][:3]
                        )
                    st.session_state[result_key] = result
                
                if result_key in st.session_state:
                    res = st.session_state[result_key]
                    successful_llms = [r for r in res['results'] if r['success']]
                    
                    if successful_llms:
                        # Collective summary banner
                        collective = res.get('collective')
                        if collective:
                            agreement_color = {"High Agreement": "#2ca02c", "Moderate Agreement": "#ff7f0e", "Mixed Opinions": "#d62728"}.get(collective["agreement_level"], "#888")
                            st.markdown(f"""
                            <div style='padding: 12px; background: {agreement_color}18; border-left: 4px solid {agreement_color}; border-radius: 6px; margin-bottom: 10px;'>
                                <strong style='color:{agreement_color};'>{collective["agreement_level"]} — {collective["models_agreed"]} models</strong><br>
                                Priority: <strong>{collective["agreed_priority"]}</strong> ({collective["priority_agreement"]}% agreement) &nbsp;|&nbsp;
                                Avg Confidence: <strong>{collective["avg_confidence"]}%</strong> &nbsp;|&nbsp;
                                Best: <strong>{collective["best_response_from"]}</strong>
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown(f"**🏆 Best recommendation from: {res['best_llm'] or 'N/A'}**")
                        
                        # Show all successful LLM responses in tabs
                        tab_names = [r['llm_name'] for r in successful_llms]
                        tabs = st.tabs(tab_names)
                        
                        for tab, r in zip(tabs, successful_llms):
                            with tab:
                                demo_badge = " 🟡 DEMO" if r.get('is_demo') else ""
                                st.caption(f"⏱️ {r['latency_ms']:.0f}ms | 📝 {r['word_count']} words | ⭐ {r['quality_score']}/100{demo_badge}")
                                st.markdown(r['response'])
                    else:
                        st.warning("All LLMs failed. Check API keys or Ollama connection.")
    else:
        st.success("✅ All machines operating within normal parameters")
    
    st.markdown("---")
    
    # Timeline and Analytics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Incident Trend (Last 30 Days)")
        last_30_days = df[df['date'] >= datetime.now() - timedelta(days=30)].copy()
        last_30_days['date_only'] = pd.to_datetime(last_30_days['date']).dt.date
        daily_incidents = last_30_days.groupby('date_only').size().reset_index(name='count')
        
        fig = px.area(daily_incidents, x='date_only', y='count',
                     labels={'date_only': 'Date', 'count': 'Incidents'},
                     color_discrete_sequence=['#d62728'])
        fig.update_layout(height=250, showlegend=False, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🔧 Issue Distribution")
        issue_counts = last_30_days['issue_type'].value_counts().head(5)
        
        for issue, count in issue_counts.items():
            percentage = (count / len(last_30_days)) * 100
            st.markdown(f"""
            <div style='margin: 8px 0;'>
                <div style='display: flex; justify-content: space-between; font-size: 0.9em;'>
                    <span>{issue.title()}</span>
                    <span><strong>{count}</strong> ({percentage:.0f}%)</span>
                </div>
                <div style='background-color: #e0e0e0; border-radius: 10px; height: 8px; margin-top: 4px;'>
                    <div style='background-color: #d62728; width: {percentage}%; height: 100%; border-radius: 10px;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Production Line Status
    st.subheader("🏭 Production Line Overview")
    
    line_stats = []
    for line in sorted(df['production_line'].unique()):
        line_machines = df[df['production_line'] == line]['machine_id'].unique()
        line_incidents = len(df[df['production_line'] == line])
        line_downtime = df[df['production_line'] == line]['downtime_minutes'].sum()
        line_risks = [m for m in machine_stats if m['machine_id'] in line_machines]
        
        line_stats.append({
            'line': line,
            'machines': len(line_machines),
            'incidents': line_incidents,
            'downtime': line_downtime,
            'critical': len([m for m in line_risks if m['risk_level'] == 'Critical']),
            'high': len([m for m in line_risks if m['risk_level'] == 'High'])
        })
    
    cols = st.columns(len(line_stats))
    for idx, line in enumerate(line_stats):
        with cols[idx]:
            status_color = '#d62728' if line['critical'] > 0 else '#ff7f0e' if line['high'] > 0 else '#2ca02c'
            status_emoji = '🔴' if line['critical'] > 0 else '🟠' if line['high'] > 0 else '🟢'
            
            # Build warning messages
            warnings = ""
            if line['critical'] > 0:
                warnings += f"<p style='margin: 3px 0; font-size: 0.85em; color: #d62728;'>⚠️ {line['critical']} Critical</p>"
            if line['high'] > 0:
                warnings += f"<p style='margin: 3px 0; font-size: 0.85em; color: #ff7f0e;'>⚠️ {line['high']} High Risk</p>"
            
            st.markdown(f"""
            <div style='padding: 12px; background-color: {status_color}10; 
                        border-radius: 8px; border: 2px solid {status_color};'>
                <h4 style='margin: 0 0 8px 0;'>{status_emoji} {line['line']}</h4>
                <p style='margin: 3px 0; font-size: 0.9em;'>Machines: {line['machines']}</p>
                <p style='margin: 3px 0; font-size: 0.9em;'>Incidents: {line['incidents']}</p>
                <p style='margin: 3px 0; font-size: 0.9em;'>Downtime: {line['downtime']} min</p>
                {warnings}
            </div>
            """, unsafe_allow_html=True)

def show_insights_dashboard(insights_engine, df, risk_data, db):
    """🎯 Advanced Insights Dashboard - Unique Features"""
    st.header("🎯 Advanced Insights Dashboard")
    st.markdown("**AI-Powered Intelligence Beyond Basic Analytics**")
    
    # Smart Insights Panel
    st.subheader("💡 Smart Insights")
    insights = insights_engine.generate_smart_insights()
    
    cols = st.columns(len(insights))
    for idx, insight in enumerate(insights):
        with cols[idx]:
            st.markdown(f"### {insight['icon']}")
            st.markdown(f"**{insight['title']}**")
            st.info(insight['insight'])
            st.caption(f"💡 {insight['action']}")
    
    st.markdown("---")
    
    # Anomaly Detection
    st.subheader("🔍 Anomaly Detection")
    anomalies = insights_engine.detect_anomalies()
    
    if anomalies:
        # Import repair recommender
        from agents.repair_recommender import RepairRecommender
        repair_recommender = RepairRecommender()
        
        for anomaly in anomalies:
            severity_color = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }
            
            with st.expander(f"{severity_color.get(anomaly['severity'], '🔵')} {anomaly['title']}", expanded=True):
                st.markdown(f"**Description:** {anomaly['description']}")
                st.markdown(f"**Recommendation:** {anomaly['recommendation']}")
                
                # If anomaly has a machine_id, show repair recommendation with YouTube videos
                if 'machine_id' in anomaly:
                    machine_logs = df[df['machine_id'] == anomaly['machine_id']]
                    if len(machine_logs) > 0:
                        most_common_issue = machine_logs['issue_type'].mode()[0] if len(machine_logs['issue_type'].mode()) > 0 else 'vibration'
                        repair_rec = repair_recommender.get_repair_recommendation(most_common_issue)
                        
                        st.markdown("---")
                        st.markdown("**🔧 Repair Solution:**")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Component:** {repair_rec['primary_component']}")
                            st.markdown(f"**Cost:** ₹{repair_rec['estimated_cost_inr']:,}")
                        with col2:
                            st.markdown(f"**Time:** {repair_rec['estimated_time_hours']} hours")
                            st.markdown(f"**Fix:** {repair_rec['permanent_fix']}")
                        
                        # YouTube Videos
                        st.markdown("**📹 How to Fix (Video Tutorials):**")
                        for video in repair_rec['youtube_videos']:
                            st.markdown(f"• [{video['title']}]({video['url']}) - {video['duration']} ({video['views']} views)")
    else:
        st.success("✅ No anomalies detected - system operating normally")
    
    st.markdown("---")
    
    # Cost Impact Calculator
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Cost Impact Analysis")
        cost_data = insights_engine.calculate_cost_impact()
        
        st.metric("Total Downtime Cost", f"₹{cost_data['total_cost']:,.0f}")
        st.metric("Cost Per Incident", f"₹{cost_data['cost_per_incident']:,.0f}")
        st.metric("Potential Savings", f"₹{cost_data['prevented_cost_potential']:,.0f}", 
                 delta=f"{cost_data['roi_opportunity']} ROI Opportunity", delta_color="normal")
        
        st.info(f"💡 With predictive maintenance, you could save **₹{cost_data['prevented_cost_potential']:,.0f}** annually")
    
    with col2:
        st.subheader("🏆 Maintenance Efficiency Score")
        efficiency = insights_engine.calculate_maintenance_efficiency_score()
        
        # Create a gauge-like display
        score_color = '#2ecc71' if efficiency['score'] >= 75 else '#f39c12' if efficiency['score'] >= 50 else '#e74c3c'
        
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; background-color: {score_color}20; border-radius: 10px; border: 3px solid {score_color};'>
            <h1 style='color: {score_color}; margin: 0;'>{efficiency['score']}/100</h1>
            <h2 style='margin: 10px 0;'>Grade: {efficiency['grade']}</h2>
            <p style='margin: 0;'>{efficiency['message']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Performance Breakdown:**")
        st.markdown(f"- ✅ Permanent Fixes: {efficiency['permanent_fixes']}")
        st.markdown(f"- ⚠️ Temporary Fixes: {efficiency['temporary_fixes']}")
        st.markdown(f"- 🔄 Repeated Issues: {efficiency['repeated_issues']}")
        
        st.caption(f"💡 {efficiency['improvement_tip']}")
    
    st.markdown("---")
    
    # Failure Cascade Prediction
    st.subheader("⛓️ Failure Cascade Prediction")
    st.markdown("**What happens if a high-risk machine fails?**")
    
    high_risk_machines = [r['machine_id'] for r in risk_data if r['risk_score'] >= 50]
    if high_risk_machines:
        selected_machine = st.selectbox("Select high-risk machine:", high_risk_machines)
        
        cascade = insights_engine.predict_failure_cascade(selected_machine)
        
        if cascade:
            st.warning(f"⚠️ If **{selected_machine}** fails, these machines are at risk:")
            
            for item in cascade:
                with st.expander(f"🔗 {item['machine_id']} - {item['cascade_probability']}% cascade probability"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Reason:** {item['reason']}")
                        st.markdown(f"**Impact:** {item['estimated_impact']}")
                    with col2:
                        st.markdown(f"**Mitigation:** {item['mitigation']}")
                        
                        # Progress bar for probability
                        st.progress(item['cascade_probability'] / 100)
        else:
            st.info("No significant cascade risk detected")
    else:
        st.info("No high-risk machines currently")
    
    st.markdown("---")
    
    # Predictive Parts Inventory
    st.subheader("🔧 Predictive Parts Inventory")
    st.markdown("**Parts you'll likely need in the next 30 days**")
    
    parts_predictions = insights_engine.predict_parts_inventory()
    
    if parts_predictions:
        for part in parts_predictions:
            urgency_color = '🔴' if part['urgency'] == 'High' else '🟡' if part['urgency'] == 'Medium' else '🟢'
            
            with st.expander(f"{urgency_color} {part['part']} - {part['probability']}% probability"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Estimated Quantity", part['estimated_quantity'])
                
                with col2:
                    st.metric("Lead Time", part['lead_time'])
                
                with col3:
                    st.metric("Urgency", part['urgency'])
                
                st.markdown(f"**Machines affected:** {', '.join(part['machines_affected'])}")
                st.progress(part['probability'] / 100)
    else:
        st.info("No parts predictions available yet")
    
    st.markdown("---")
    
    # 3D Risk Heatmap
    st.subheader("🗺️ Multi-Dimensional Risk Heatmap")
    heatmap_data = insights_engine.get_risk_heatmap_data()
    
    if heatmap_data:
        heatmap_df = pd.DataFrame(heatmap_data)
        
        # Create bubble chart
        fig = px.scatter(
            heatmap_df,
            x='frequency_risk',
            y='severity_risk',
            size='recency_risk',
            color='overall_risk',
            hover_data=['machine_id', 'production_line'],
            labels={
                'frequency_risk': 'Frequency Risk',
                'severity_risk': 'Severity Risk',
                'overall_risk': 'Overall Risk'
            },
            title='Risk Distribution: Frequency vs Severity (bubble size = recency)',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption("💡 Machines in the top-right corner with large bubbles need immediate attention")
    
    st.markdown("---")
    
    # Machine Comparison
    st.subheader("⚖️ Machine Comparison")
    
    all_machines = df['machine_id'].unique().tolist()
    selected_machines = st.multiselect(
        "Select machines to compare (2-4 recommended):",
        all_machines,
        default=all_machines[:3] if len(all_machines) >= 3 else all_machines
    )
    
    if len(selected_machines) >= 2:
        comparison = insights_engine.compare_machines(selected_machines)
        comparison_df = pd.DataFrame(comparison)
        
        # Display comparison table
        st.dataframe(comparison_df.style.background_gradient(cmap='RdYlGn_r', subset=['total_incidents', 'total_downtime']), 
                    use_container_width=True)
        
        # Comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(comparison_df, x='machine_id', y='total_incidents', 
                        title='Total Incidents Comparison',
                        color='total_incidents', color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(comparison_df, x='machine_id', y='total_downtime',
                        title='Total Downtime Comparison',
                        color='total_downtime', color_continuous_scale='Oranges')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select at least 2 machines to compare")

def show_dashboard(df, risk_data, log_analyzer, db):
    """Main dashboard view"""
    st.header("📊 System Overview")
    
    # Get stats from database
    stats = db.get_stats()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Machines", stats['total_machines'])
    
    with col2:
        high_risk_count = stats['high_risk_machines']
        st.metric("High Risk Machines", high_risk_count, delta=None, delta_color="inverse")
    
    with col3:
        total_downtime = df['downtime_minutes'].sum()
        st.metric("Total Downtime", f"{int(total_downtime)} min")
    
    with col4:
        total_incidents = stats['total_logs']
        st.metric("Total Incidents", total_incidents)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Distribution")
        risk_levels = [r['risk_level'] for r in risk_data]
        risk_counts = pd.Series(risk_levels).value_counts()
        
        fig = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            color=risk_counts.index,
            color_discrete_map={
                'Critical': '#d62728',
                'High': '#ff7f0e',
                'Medium': '#ffbb78',
                'Low': '#2ca02c'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Issue Type Distribution")
        issue_counts = df['issue_type'].value_counts()
        
        fig = px.bar(
            x=issue_counts.index,
            y=issue_counts.values,
            labels={'x': 'Issue Type', 'y': 'Count'},
            color=issue_counts.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top risk machines
    st.subheader("🚨 Top Risk Machines")
    top_risks = risk_data[:5]
    
    for machine in top_risks:
        risk_color = "risk-high" if machine['risk_score'] >= 70 else "risk-medium" if machine['risk_score'] >= 50 else "risk-low"
        
        with st.expander(f"**{machine['machine_id']}** - Risk Score: {machine['risk_score']}/100"):
            st.markdown(f"**Risk Level:** <span class='{risk_color}'>{machine['risk_level']}</span>", unsafe_allow_html=True)
            st.markdown("**Risk Factors:**")
            for factor in machine['factors']:
                st.markdown(f"- {factor}")

    # ── Machine PDF Export ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📥 Export Machine Report")

    all_machine_ids = sorted(df['machine_id'].unique().tolist())
    selected = st.selectbox("Select machine to export full PDF report", all_machine_ids, key="dashboard_pdf_machine")

    if st.button("📑 Generate PDF Report", type="primary", use_container_width=False, key="dashboard_pdf_btn"):
        with st.spinner(f"Generating full report for {selected}..."):
            try:
                from utils.pdf_exporter import generate_machine_pdf
                from agents.failure_predictor_ml import FailurePredictorMLAgent
                from agents.repair_recommender import RepairRecommender

                predictor   = FailurePredictorMLAgent(df)
                risk_info   = predictor.calculate_risk_score(selected)
                fail_window = predictor.predict_failure_window(selected)

                machine_logs = df[df['machine_id'] == selected]
                most_common  = machine_logs['issue_type'].mode()[0] if len(machine_logs) > 0 else 'vibration'

                recommender = RepairRecommender()
                repair_rec  = recommender.get_repair_recommendation(most_common)

                pdf_bytes = generate_machine_pdf(
                    machine_id            = selected,
                    machine_logs_df       = machine_logs,
                    risk_info             = risk_info,
                    repair_recommendation = repair_rec,
                    failure_window        = fail_window,
                )
                st.session_state[f'dash_pdf_{selected}'] = pdf_bytes
                st.success(f"✅ Report ready for {selected}!")
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

    pdf_key = f'dash_pdf_{selected}'
    if pdf_key in st.session_state:
        st.download_button(
            label=f"⬇️ Download {selected} Full Report (PDF)",
            data=st.session_state[pdf_key],
            file_name=f"PlantPulse_{selected}_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
        )

def show_logs(df, db):
    """Logs view with search and filter"""
    st.header("📋 Maintenance Logs")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        machines = ['All'] + sorted(df['machine_id'].unique().tolist())
        selected_machine = st.selectbox("Filter by Machine", machines)
    
    with col2:
        issues = ['All'] + sorted(df['issue_type'].unique().tolist())
        selected_issue = st.selectbox("Filter by Issue Type", issues)
    
    with col3:
        search_term = st.text_input("Search in notes", "")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_machine != 'All':
        filtered_df = filtered_df[filtered_df['machine_id'] == selected_machine]
    
    if selected_issue != 'All':
        filtered_df = filtered_df[filtered_df['issue_type'] == selected_issue]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['technician_note'].str.contains(search_term, case=False, na=False)
        ]
    
    # Display stats
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} logs**")
    
    # Display logs table
    display_df = filtered_df[[
        'machine_id', 'date', 'technician_note', 'issue_type',
        'action_taken', 'downtime_minutes', 'criticality'
    ]].copy()
    
    display_df = display_df.sort_values('date', ascending=False)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400
    )
    
    # ── Export options ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📥 Export Options")

    col_csv, col_pdf = st.columns(2)

    with col_csv:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📄 Export to CSV",
            data=csv,
            file_name=f"maintenance_logs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_pdf:
        # PDF export only makes sense for a single machine
        if selected_machine != 'All':
            if st.button("📑 Export Machine PDF Report", use_container_width=True, type="primary"):
                with st.spinner(f"Generating PDF report for {selected_machine}..."):
                    try:
                        from utils.pdf_exporter import generate_machine_pdf
                        from agents.failure_predictor_ml import FailurePredictorMLAgent
                        from agents.repair_recommender import RepairRecommender

                        # Build required data
                        predictor   = FailurePredictorMLAgent(df)
                        risk_info   = predictor.calculate_risk_score(selected_machine)
                        fail_window = predictor.predict_failure_window(selected_machine)

                        machine_logs = df[df['machine_id'] == selected_machine]
                        most_common_issue = (
                            machine_logs['issue_type'].mode()[0]
                            if len(machine_logs) > 0 else 'vibration'
                        )

                        recommender = RepairRecommender()
                        repair_rec  = recommender.get_repair_recommendation(most_common_issue)

                        pdf_bytes = generate_machine_pdf(
                            machine_id           = selected_machine,
                            machine_logs_df      = machine_logs,
                            risk_info            = risk_info,
                            repair_recommendation= repair_rec,
                            failure_window       = fail_window,
                        )

                        st.session_state[f'pdf_{selected_machine}'] = pdf_bytes
                        st.success(f"✅ PDF ready for {selected_machine}!")

                    except Exception as e:
                        st.error(f"PDF generation failed: {e}")

            # Show download button if PDF is ready
            pdf_key = f'pdf_{selected_machine}'
            if pdf_key in st.session_state:
                st.download_button(
                    label=f"⬇️ Download {selected_machine} Report PDF",
                    data=st.session_state[pdf_key],
                    file_name=f"PlantPulse_{selected_machine}_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.info("Select a specific machine above to export a full PDF report with recommendations.")

def show_add_log(db):
    """Add new maintenance log"""
    st.header("➕ Add New Maintenance Log")
    
    st.markdown("""
    Enter a new maintenance or repair log. The system will automatically:
    - Analyze the technician note
    - Update machine risk scores
    - Regenerate maintenance schedule
    """)
    
    with st.form("new_log_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            machine_id = st.text_input(
                "Machine ID *",
                placeholder="e.g., M12",
                help="Enter the machine identifier"
            )
            
            production_line = st.selectbox(
                "Production Line",
                ["Line-A", "Line-B", "Line-C"]
            )
            
            log_date = st.date_input(
                "Date *",
                value=datetime.now()
            )
            
            log_time = st.time_input(
                "Time *",
                value=datetime.now().time()
            )
            
            issue_category = st.selectbox(
                "Issue Category *",
                ["vibration", "overheating", "lubrication", "electrical", "mechanical", "other"]
            )
        
        with col2:
            action_taken = st.selectbox(
                "Action Taken *",
                ["temporary_fix", "adjustment", "part_replacement", "inspection", "monitoring"]
            )
            
            downtime_minutes = st.number_input(
                "Downtime (minutes)",
                min_value=0,
                value=0,
                step=5
            )
            
            parts_replaced = st.text_input(
                "Parts Replaced",
                placeholder="e.g., bearing, belt, seal"
            )
            
            criticality = st.selectbox(
                "Criticality *",
                ["Low", "Medium", "High", "Critical"]
            )
            
            severity = st.selectbox(
                "Severity *",
                ["Low", "Medium", "High", "Critical"]
            )
        
        technician_note = st.text_area(
            "Technician Note *",
            placeholder="Describe the issue, symptoms, and actions taken...",
            help="Be specific about symptoms, sounds, temperatures, vibrations, etc.",
            height=100
        )
        
        submitted = st.form_submit_button("✅ Submit Log", use_container_width=True)
        
        if submitted:
            # Validate required fields
            if not machine_id or not technician_note:
                st.error("Please fill in all required fields (*)")
            else:
                # Combine date and time
                log_datetime = datetime.combine(log_date, log_time)
                
                # Prepare log data
                log_data = {
                    'machine_id': machine_id.upper(),
                    'production_line': production_line,
                    'log_date': log_datetime.strftime('%Y-%m-%d %H:%M'),
                    'technician_note': technician_note,
                    'issue_category': issue_category,
                    'severity': severity,
                    'action_taken': action_taken,
                    'downtime_minutes': downtime_minutes,
                    'parts_replaced': parts_replaced if parts_replaced else None,
                    'criticality': criticality,
                    'maintenance_type': 'corrective',
                    'incident_flag': 1 if criticality in ['High', 'Critical'] else 0
                }
                
                # Add to database
                log_id = db.add_log(log_data)
                
                st.success(f"✅ Log #{log_id} added successfully!")
                
                # Reload data and recalculate everything
                with st.spinner("🔄 Analyzing patterns and updating system..."):
                    # Force cache clear
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    
                    # Reload data
                    df_updated = load_data(db)
                    
                    # Reinitialize agents with updated data
                    from agents.failure_predictor_ml import FailurePredictorMLAgent
                    from agents.scheduler_urgent import UrgentMaintenanceScheduler
                    
                    predictor_updated = FailurePredictorMLAgent(df_updated)
                    risk_data_updated = predictor_updated.get_all_risk_scores()
                    scheduler_updated = UrgentMaintenanceScheduler(risk_data_updated, df_updated)
                    
                    # Get updated risk for this machine
                    machine_risk = next((r for r in risk_data_updated if r['machine_id'] == machine_id.upper()), None)
                    
                    # Detect patterns
                    machine_logs = df_updated[df_updated['machine_id'] == machine_id.upper()].sort_values('date')
                    recent_issues = machine_logs.tail(5)['issue_type'].tolist()
                    
                    # Check for issue sequences
                    pattern_detected = False
                    pattern_msg = ""
                    if len(recent_issues) >= 2:
                        if 'overheating' in recent_issues and 'vibration' in recent_issues:
                            pattern_detected = True
                            pattern_msg = "⚠️ **Pattern Detected:** Overheating → Vibration sequence indicates potential motor bearing failure"
                        elif 'vibration' in recent_issues and 'overheating' in recent_issues:
                            pattern_detected = True
                            pattern_msg = "⚠️ **Pattern Detected:** Vibration → Overheating sequence indicates cooling system degradation"
                        elif recent_issues.count(issue_category) >= 2:
                            pattern_detected = True
                            pattern_msg = f"⚠️ **Pattern Detected:** Repeated {issue_category} issues indicate unresolved root cause"
                
                st.success("✅ System updated with real-time learning!")
                
                # Show analysis results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 Updated Risk Analysis")
                    if machine_risk:
                        st.metric("Risk Score", f"{machine_risk['risk_score']}/100", 
                                 delta=f"{machine_risk['risk_level']}")
                        if machine_risk['ml_anomaly']:
                            st.warning(f"🤖 ML Anomaly Detected ({machine_risk['ml_confidence']}% confidence)")
                        
                        st.markdown("**Risk Factors:**")
                        for factor in machine_risk['factors'][:3]:
                            st.markdown(f"- {factor}")
                
                with col2:
                    st.markdown("### 📅 Schedule Updated")
                    schedule_updated = scheduler_updated.generate_schedule(7)
                    machine_schedule = next((s for s in schedule_updated if s['machine_id'] == machine_id.upper()), None)
                    
                    if machine_schedule:
                        st.info(f"**Priority:** {machine_schedule['priority']}")
                        st.info(f"**Scheduled:** {machine_schedule['scheduled_time']}")
                        st.markdown(f"**Reason:** {machine_schedule['reason'][:100]}...")
                    else:
                        st.success("Machine risk is low - no immediate maintenance needed")
                
                # Show pattern detection
                if pattern_detected:
                    st.warning(pattern_msg)
                    st.markdown("**Recommended Action:** Schedule comprehensive inspection to address root cause")
                
                # Show what was added
                with st.expander("📄 View Added Log"):
                    st.json(log_data)
                
                st.markdown("---")
                st.markdown("**✅ Real-Time Learning Complete:**")
                st.markdown("- Risk scores recalculated with ML")
                st.markdown("- Maintenance schedule regenerated")
                st.markdown("- Issue patterns analyzed")
                st.markdown("- System learned from new data")

def show_risk_analysis(risk_data, failure_predictor, df):
    """Risk analysis view"""
    st.header("⚠️ Failure Risk Analysis")
    
    # Risk table
    st.subheader("Machine Risk Scores")
    
    risk_df = pd.DataFrame(risk_data)
    risk_df = risk_df[['machine_id', 'risk_score', 'risk_level', 'total_incidents', 'recent_incidents']]
    
    # Color code risk levels
    def color_risk(val):
        if val == 'Critical':
            return 'background-color: #ffcccc'
        elif val == 'High':
            return 'background-color: #ffe6cc'
        elif val == 'Medium':
            return 'background-color: #ffffcc'
        else:
            return 'background-color: #ccffcc'
    
    styled_df = risk_df.style.applymap(color_risk, subset=['risk_level'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Risk score chart
    st.subheader("Risk Score Comparison")
    fig = px.bar(
        risk_df,
        x='machine_id',
        y='risk_score',
        color='risk_level',
        color_discrete_map={
            'Critical': '#d62728',
            'High': '#ff7f0e',
            'Medium': '#ffbb78',
            'Low': '#2ca02c'
        },
        labels={'risk_score': 'Risk Score', 'machine_id': 'Machine ID'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed analysis
    st.subheader("Detailed Risk Analysis")
    selected_machine = st.selectbox("Select Machine", risk_df['machine_id'].tolist())
    
    if selected_machine:
        risk_info = failure_predictor.calculate_risk_score(selected_machine)
        prediction = failure_predictor.predict_failure_window(selected_machine)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Risk Score", f"{risk_info['risk_score']}/100")
        
        with col2:
            st.metric("Risk Level", risk_info['risk_level'])
        
        with col3:
            st.metric("Predicted Failure Window", prediction['predicted_window'])
        
        st.markdown("**Risk Factors:**")
        for factor in risk_info['factors']:
            st.markdown(f"- {factor}")

def show_schedule(scheduler, risk_data):
    """Maintenance schedule view"""
    st.header("📅 Maintenance Schedule")
    
    # Tabs for auto and manual scheduling
    tab1, tab2 = st.tabs(["🤖 Auto-Generated Schedule", "✏️ Manual Scheduling"])
    
    with tab1:
        # Generate schedule
        days_ahead = st.slider("Schedule for next N days", 7, 30, 14)
        schedule = scheduler.generate_schedule(days_ahead)
        
        if not schedule:
            st.info("No maintenance currently scheduled.")
        else:
            st.subheader(f"Upcoming Maintenance ({len(schedule)} machines)")
            
            # Schedule table
            for idx, item in enumerate(schedule, 1):
                with st.expander(f"#{idx} - {item['machine_id']} - {item['scheduled_time']} ({item['priority']} Priority)"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Machine:** {item['machine_id']}")
                        st.markdown(f"**Risk Score:** {item['risk_score']}/100")
                        st.markdown(f"**Priority:** {item['priority']}")
                        st.markdown(f"**Production Line:** {item['production_line']}")
                    
                    with col2:
                        st.markdown(f"**Scheduled Time:** {item['scheduled_time']}")
                        st.markdown(f"**Estimated Duration:** {item['estimated_duration']}")
                    
                    st.markdown("**Reason:**")
                    st.info(item['reason'])
                    
                    st.markdown("**Recommended Actions:**")
                    for action in item['recommended_actions']:
                        st.markdown(f"- {action}")
            
            # Group by production line
            st.subheader("Schedule by Production Line")
            by_line = scheduler.optimize_by_production_line(schedule)
            
            for line, items in by_line.items():
                st.markdown(f"**{line}:** {len(items)} machines")
    
    with tab2:
        st.subheader("📝 Schedule Maintenance Manually")
        st.markdown("Schedule maintenance for a specific machine at your preferred time.")
        
        # Get all machines
        all_machines = [r['machine_id'] for r in risk_data]
        
        with st.form("manual_schedule_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_machine = st.selectbox("Select Machine", all_machines)
                
                # Get machine info
                machine_risk = next((r for r in risk_data if r['machine_id'] == selected_machine), None)
                if machine_risk:
                    st.info(f"Risk Score: {machine_risk['risk_score']}/100 - {machine_risk['risk_level']}")
                
                maintenance_type = st.selectbox(
                    "Maintenance Type",
                    ["Preventive", "Corrective", "Predictive", "Emergency", "Inspection"]
                )
                
                priority = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"])
            
            with col2:
                schedule_date = st.date_input("Schedule Date", datetime.now() + timedelta(days=1))
                schedule_time = st.time_input("Schedule Time", datetime.now().replace(hour=8, minute=0))
                
                duration_hours = st.number_input("Estimated Duration (hours)", min_value=0.5, max_value=8.0, value=2.0, step=0.5)
                
                technician = st.text_input("Assigned Technician", "")
            
            reason = st.text_area(
                "Reason for Maintenance",
                placeholder="e.g., Routine inspection, Replace worn parts, Address vibration issue..."
            )
            
            actions = st.text_area(
                "Planned Actions (one per line)",
                placeholder="e.g.,\nInspect motor bearings\nCheck hydraulic pressure\nReplace filters"
            )
            
            submit = st.form_submit_button("📅 Schedule Maintenance", use_container_width=True)
            
            if submit:
                if not reason:
                    st.error("Please provide a reason for maintenance")
                elif not actions:
                    st.error("Please specify planned actions")
                else:
                    # Create schedule entry
                    scheduled_datetime = datetime.combine(schedule_date, schedule_time)
                    action_list = [a.strip() for a in actions.split('\n') if a.strip()]
                    
                    schedule_entry = {
                        'machine_id': selected_machine,
                        'maintenance_type': maintenance_type,
                        'priority': priority,
                        'scheduled_date': schedule_date.strftime('%Y-%m-%d'),
                        'scheduled_time': schedule_time.strftime('%H:%M'),
                        'scheduled_datetime': scheduled_datetime.strftime('%Y-%m-%d %H:%M'),
                        'estimated_duration': f"{duration_hours} hours",
                        'technician': technician if technician else "To be assigned",
                        'reason': reason,
                        'actions': action_list,
                        'status': 'Scheduled',
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Save to database
                    db = get_database()
                    schedule_id = db.add_manual_schedule(schedule_entry)
                    
                    st.success(f"✅ Maintenance scheduled for {selected_machine} on {scheduled_datetime.strftime('%Y-%m-%d at %H:%M')}")
                    st.balloons()
                    
                    # Display confirmation
                    with st.expander("📋 Schedule Details", expanded=True):
                        st.markdown(f"**Schedule ID:** #{schedule_id}")
                        st.markdown(f"**Machine:** {selected_machine}")
                        st.markdown(f"**Type:** {maintenance_type}")
                        st.markdown(f"**Priority:** {priority}")
                        st.markdown(f"**Date & Time:** {scheduled_datetime.strftime('%Y-%m-%d at %H:%M')}")
                        st.markdown(f"**Duration:** {duration_hours} hours")
                        st.markdown(f"**Technician:** {schedule_entry['technician']}")
                        st.markdown(f"**Reason:** {reason}")
                        st.markdown("**Planned Actions:**")
                        for action in action_list:
                            st.markdown(f"- {action}")
        
        # Show recently scheduled items
        st.markdown("---")
        st.subheader("📋 Manual Schedule History")
        
        # Get manual schedules from database
        db = get_database()
        all_schedules = db.get_schedule()
        
        if len(all_schedules) > 0:
            # Filter manual schedules
            manual_schedules = all_schedules[all_schedules['schedule_source'] == 'manual'] if 'schedule_source' in all_schedules.columns else pd.DataFrame()
            
            if len(manual_schedules) > 0:
                st.dataframe(
                    manual_schedules[['schedule_id', 'machine_id', 'maintenance_type', 'priority', 'suggested_date', 'suggested_time', 'status']],
                    use_container_width=True
                )
            else:
                st.info("No manual schedules yet. Create one above!")
        else:
            st.info("No manual schedules yet. Create one above!")

def show_assistant(assistant):
    """AI assistant chat interface"""
    st.header("🤖 AI Maintenance Assistant")
    
    st.markdown("Ask questions about maintenance history, risk analysis, or schedules.")
    
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about maintenance..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response = assistant.answer_query(prompt)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Example questions
    st.sidebar.markdown("### Example Questions")
    example_questions = [
        "Which machines are at high risk?",
        "Why is M12 high priority?",
        "Show me the maintenance schedule",
        "What are the most common issues?",
        "Which production line has the most problems?"
    ]
    
    for question in example_questions:
        if st.sidebar.button(question, key=question):
            st.session_state.messages.append({"role": "user", "content": question})
            response = assistant.answer_query(question)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

def show_machine_history(log_analyzer, failure_predictor, df):
    """Machine history view"""
    st.header("🔍 Machine History")
    
    machines = df['machine_id'].unique()
    selected_machine = st.selectbox("Select Machine", machines)
    
    if selected_machine:
        history = log_analyzer.get_machine_history(selected_machine)
        risk_info = failure_predictor.calculate_risk_score(selected_machine)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Incidents", history['total_incidents'])
        
        with col2:
            st.metric("Total Downtime", f"{int(history['total_downtime'])} min")
        
        with col3:
            st.metric("Risk Score", f"{risk_info['risk_score']}/100")
        
        with col4:
            st.metric("Temporary Fixes", history['temporary_fix_count'])
        
        # Issue breakdown
        st.subheader("Issue Type Breakdown")
        issue_df = pd.DataFrame(list(history['issue_types'].items()), columns=['Issue Type', 'Count'])
        fig = px.bar(issue_df, x='Issue Type', y='Count', color='Count', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent logs
        st.subheader("Recent Maintenance Logs")
        recent_df = pd.DataFrame(history['recent_logs'])
        st.dataframe(recent_df, use_container_width=True)

def show_ml_comparison(df, failure_predictor):
    """🔬 ML Algorithm Comparison - Compare 6 Different Algorithms"""
    st.header("🔬 ML Algorithm Comparison")
    st.markdown("**Compare 6 different machine learning algorithms for anomaly detection**")
    
    st.info("💡 This feature compares 6 ML algorithms to show which performs best for our data!")
    
    # Import ML comparison engine
    from agents.ml_comparison import MLComparisonEngine
    from agents.repair_recommender import RepairRecommender
    
    # Initialize engines
    ml_engine = MLComparisonEngine(df)
    repair_recommender = RepairRecommender()
    
    # Run comparison
    with st.spinner("🔄 Running 6 ML algorithms... This may take a few seconds..."):
        comparison_results = ml_engine.compare_all_algorithms()
    
    if not comparison_results:
        st.warning("Not enough data to compare algorithms. Need at least 3 machines.")
        return
    
    st.success(f"✅ Analyzed {comparison_results['machines_analyzed']} machines using {comparison_results['total_algorithms']} algorithms!")
    
    # Show algorithm performance comparison
    st.subheader("📊 Algorithm Performance Comparison")
    
    algo_data = []
    for algo in comparison_results['algorithms']:
        algo_data.append({
            'Algorithm': algo['name'],
            'Accuracy': f"{algo['accuracy_estimate']}%",
            'Training Time': f"{algo['training_time_ms']:.1f}ms",
            'Description': algo['description']
        })
    
    algo_df = pd.DataFrame(algo_data)
    st.dataframe(algo_df, use_container_width=True)
    
    # Best algorithm
    best = ml_engine.get_best_algorithm(comparison_results)
    if best:
        st.success(f"🏆 **Best Algorithm:** {best['best_algorithm']} - {best['reason']}")
    
    st.markdown("---")
    
    # Consensus Results
    st.subheader("🎯 Consensus Results (Majority Vote)")
    st.markdown("**When 3+ algorithms agree, we have high confidence!**")
    
    consensus_data = []
    for item in comparison_results['consensus']:
        consensus_data.append({
            'Machine': item['machine_id'],
            'Anomaly?': '🔴 YES' if item['is_anomaly'] else '🟢 NO',
            'Votes Anomaly': f"{item['votes_anomaly']}/6",
            'Votes Normal': f"{item['votes_normal']}/6",
            'Avg Confidence': f"{item['avg_confidence']}%",
            'Agreement': f"{item['agreement_percentage']}%"
        })
    
    consensus_df = pd.DataFrame(consensus_data)
    st.dataframe(consensus_df, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed algorithm results
    st.subheader("🔍 Detailed Results by Algorithm")
    
    selected_algo = st.selectbox(
        "Select algorithm to view details:",
        [algo['name'] for algo in comparison_results['algorithms']]
    )
    
    for algo in comparison_results['algorithms']:
        if algo['name'] == selected_algo:
            st.markdown(f"### {algo['name']}")
            st.markdown(f"**Description:** {algo['description']}")
            st.markdown(f"**Accuracy:** {algo['accuracy_estimate']}% | **Training Time:** {algo['training_time_ms']:.1f}ms")
            
            # Show results
            results_data = []
            for result in algo['results']:
                results_data.append({
                    'Machine': result['machine_id'],
                    'Anomaly': '🔴 YES' if result['is_anomaly'] else '🟢 NO',
                    'Confidence': f"{result['confidence']}%",
                    'Score': f"{result['score']:.3f}"
                })
            
            results_df = pd.DataFrame(results_data)
            st.dataframe(results_df, use_container_width=True)
            
            # Visualization
            import plotly.express as px
            fig = px.bar(
                results_df,
                x='Machine',
                y='Confidence',
                color='Anomaly',
                title=f'{selected_algo} - Confidence Scores',
                color_discrete_map={'🔴 YES': 'red', '🟢 NO': 'green'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Component Repair Recommendations
    st.subheader("🔧 Component Repair Recommendations")
    st.markdown("**Get specific component recommendations for detected anomalies**")
    
    anomalous_machines = [item['machine_id'] for item in comparison_results['consensus'] if item['is_anomaly']]
    
    if anomalous_machines:
        selected_machine = st.selectbox("Select anomalous machine:", anomalous_machines)
        
        # Get machine's most common issue
        machine_logs = df[df['machine_id'] == selected_machine]
        if len(machine_logs) > 0:
            most_common_issue = machine_logs['issue_type'].mode()[0] if len(machine_logs['issue_type'].mode()) > 0 else 'vibration'
            
            # Get repair recommendation
            recommendation = repair_recommender.get_repair_recommendation(most_common_issue)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Issue Type:** {recommendation['issue_type']}")
                st.markdown(f"**Primary Component:** {recommendation['primary_component']}")
                st.markdown(f"**Estimated Cost:** ₹{recommendation['estimated_cost_inr']:,}")
                st.markdown(f"**Estimated Time:** {recommendation['estimated_time_hours']} hours")
                st.markdown(f"**Urgency:** {recommendation['urgency']}")
            
            with col2:
                st.markdown(f"**Temporary Fix:** {recommendation['temporary_fix']}")
                st.markdown(f"**Permanent Fix:** {recommendation['permanent_fix']}")
                st.markdown(f"**All Components:** {', '.join(recommendation['all_components'])}")
            
            # YouTube Videos
            st.markdown("### 📹 Repair Tutorial Videos")
            for i, video in enumerate(recommendation['youtube_videos'], 1):
                with st.expander(f"Video {i}: {video['title']} ({video['duration']})"):
                    st.markdown(f"**Duration:** {video['duration']}")
                    st.markdown(f"**Views:** {video['views']}")
                    st.markdown(f"**[Watch on YouTube]({video['url']})**")
            
            # Tools and Safety
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🛠️ Tools Required")
                for tool in recommendation['tools_required']:
                    st.markdown(f"- {tool}")
            
            with col2:
                st.markdown("### ⚠️ Safety Precautions")
                for precaution in recommendation['safety_precautions']:
                    st.markdown(f"- {precaution}")
    else:
        st.info("No anomalous machines detected. All machines operating normally!")


def show_llm_comparison(df, risk_data, failure_predictor):
    """🧠 LLM Comparison - Compare 6 LLMs: Ollama, MiniMax, Kimi, GLM, Gemini, OpenAI"""
    st.header("🧠 LLM Recommendation Comparison")
    st.markdown("**Same prompt → 7 different AI models → Compare quality, speed, and depth**")

    from agents.llm_comparison import LLMComparisonEngine

    # Pick a machine to analyze
    st.subheader("⚙️ Select Machine to Analyze")

    col1, col2 = st.columns(2)
    with col1:
        all_machines = sorted(df['machine_id'].unique().tolist())
        # Default to highest risk machine
        top_machine = risk_data[0]['machine_id'] if risk_data else all_machines[0]
        selected_machine = st.selectbox("Machine ID", all_machines,
                                        index=all_machines.index(top_machine) if top_machine in all_machines else 0)
    with col2:
        machine_logs = df[df['machine_id'] == selected_machine]
        most_common_issue = machine_logs['issue_type'].mode()[0] if len(machine_logs) > 0 else 'vibration'
        st.info(f"Most common issue: **{most_common_issue.title()}** ({len(machine_logs)} total logs)")

    # Build context for selected machine
    risk_info = failure_predictor.calculate_risk_score(selected_machine)
    recent_7d = machine_logs[machine_logs['date'] >= (
        __import__('datetime').datetime.now() - __import__('datetime').timedelta(days=7)
    )]
    temp_fixes = len(machine_logs[machine_logs['action_taken'] == 'temporary_fix'])

    # Show what will be sent to all LLMs
    with st.expander("📋 View Prompt Sent to All LLMs (same for fair comparison)", expanded=False):
        from agents.llm_comparison import build_maintenance_prompt
        preview_prompt = build_maintenance_prompt(
            selected_machine, most_common_issue,
            risk_info['risk_score'], risk_info['risk_level'],
            len(recent_7d), int(machine_logs['downtime_minutes'].sum()),
            temp_fixes, risk_info['factors'][:3]
        )
        st.code(preview_prompt, language="text")

    st.markdown("---")

    # Run comparison — two modes
    col_instant, col_live = st.columns(2)
    with col_instant:
        instant_clicked = st.button(
            "⚡ Instant Demo — All 7 Models (< 1 sec)",
            use_container_width=True, type="primary"
        )
    with col_live:
        live_clicked = st.button(
            "🌐 Live APIs — Real Responses (15–40 sec)",
            use_container_width=True
        )

    if instant_clicked:
        engine = LLMComparisonEngine()
        comparison = engine.compare_instant(
            selected_machine, most_common_issue,
            risk_info['risk_score'], risk_info['risk_level'],
            len(recent_7d), int(machine_logs['downtime_minutes'].sum()),
            temp_fixes, risk_info['factors'][:3]
        )
        st.session_state['llm_comparison_result'] = comparison
        st.success(f"⚡ Instant results loaded! Best: **{comparison['best_llm'] or 'N/A'}**")
        st.info("ℹ️ Showing pre-computed demo responses. Click 'Live APIs' to query models in real time.")

    if live_clicked:
        engine = LLMComparisonEngine()
        with st.spinner("🌐 Querying all 7 LLMs in parallel... (up to 20s per model, demo fallback on timeout)"):
            comparison = engine.compare(
                selected_machine, most_common_issue,
                risk_info['risk_score'], risk_info['risk_level'],
                len(recent_7d), int(machine_logs['downtime_minutes'].sum()),
                temp_fixes, risk_info['factors'][:3]
            )
        st.session_state['llm_comparison_result'] = comparison
        live_count = sum(1 for r in comparison['results'] if not r.get('is_demo'))
        demo_count = sum(1 for r in comparison['results'] if r.get('is_demo'))
        st.success(f"✅ Done! {live_count} live · {demo_count} demo fallback · Best: **{comparison['best_llm'] or 'N/A'}**")
        if comparison.get('any_demo'):
            st.info("ℹ️ Some models timed out or hit quota — demo responses shown for those.")

    # Display results if available
    if 'llm_comparison_result' in st.session_state:
        comparison = st.session_state['llm_comparison_result']
        results = comparison['results']
        mode_badge = "⚡ Instant Demo" if comparison.get('mode') == 'instant' else "🌐 Live APIs"

        st.markdown("---")
        st.caption(f"Showing: {mode_badge} · {comparison.get('timestamp', '')}")

        # ── Summary comparison table ──────────────────────────────────────────
        st.subheader("📊 Comparison Summary")

        import pandas as pd
        summary_rows = []
        for r in results:
            summary_rows.append({
                "LLM": r['llm_name'],
                "Model": r['model_name'],
                "Status": "✅ Success" if r['success'] else "❌ Failed",
                "Latency": f"{r['latency_ms']:.0f} ms",
                "Words": r['word_count'],
                "Quality Score": f"{r['quality_score']}/100",
                "Error": r['error'] or "—"
            })

        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # Best LLM callout
        if comparison['best_llm']:
            st.success(f"🏆 Best Overall: **{comparison['best_llm']}** (70% quality + 30% speed score)")

        st.markdown("---")

        # ── Visual comparison charts ──────────────────────────────────────────
        st.subheader("📈 Visual Comparison")

        import plotly.graph_objects as go
        import plotly.express as px

        col1, col2, col3 = st.columns(3)

        successful = [r for r in results if r['success']]

        _chart_colors = ['#E91E63', '#FF5722', '#9C27B0', '#00BCD4', '#FF9800', '#4CAF50']

        with col1:
            if successful:
                fig = px.bar(
                    x=[r['llm_name'] for r in successful],
                    y=[r['quality_score'] for r in successful],
                    color=[r['llm_name'] for r in successful],
                    title="Quality Score (0-100)",
                    labels={'x': 'LLM', 'y': 'Score'},
                    color_discrete_sequence=_chart_colors
                )
                fig.update_layout(height=300, showlegend=False, margin=dict(t=40, b=0))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if successful:
                fig = px.bar(
                    x=[r['llm_name'] for r in successful],
                    y=[r['latency_ms'] for r in successful],
                    color=[r['llm_name'] for r in successful],
                    title="Response Latency (ms) — Lower is Better",
                    labels={'x': 'LLM', 'y': 'ms'},
                    color_discrete_sequence=_chart_colors
                )
                fig.update_layout(height=300, showlegend=False, margin=dict(t=40, b=0))
                st.plotly_chart(fig, use_container_width=True)

        with col3:
            if successful:
                fig = px.bar(
                    x=[r['llm_name'] for r in successful],
                    y=[r['word_count'] for r in successful],
                    color=[r['llm_name'] for r in successful],
                    title="Response Length (words)",
                    labels={'x': 'LLM', 'y': 'Words'},
                    color_discrete_sequence=_chart_colors
                )
                fig.update_layout(height=300, showlegend=False, margin=dict(t=40, b=0))
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ── Radar chart for multi-dimension comparison ────────────────────────
        st.subheader("🕸️ Multi-Dimension Comparison")

        if len(successful) >= 2:
            max_latency = max(r['latency_ms'] for r in successful) or 1
            categories = ['Quality', 'Speed', 'Detail', 'Actionability', 'Conciseness']

            fig = go.Figure()
            colors = ['#E91E63', '#FF5722', '#9C27B0', '#00BCD4', '#FF9800', '#4CAF50']

            for i, r in enumerate(successful):
                speed_score = (1 - r['latency_ms'] / max_latency) * 100
                detail_score = min(100, r['word_count'] / 2)
                text_lower = r['response'].lower()
                action_score = sum(20 for w in ['replace', 'inspect', 'schedule', 'check', 'monitor']
                                   if w in text_lower)
                concise_score = max(0, 100 - max(0, r['word_count'] - 150) / 2)

                values = [r['quality_score'], speed_score, detail_score,
                          min(100, action_score), concise_score]
                values += [values[0]]  # close the polygon

                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories + [categories[0]],
                    fill='toself',
                    name=r['llm_name'],
                    line_color=colors[i % len(colors)],
                    opacity=0.6
                ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                height=420,
                title="LLM Performance Radar"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ── Side-by-side recommendations ─────────────────────────────────────
        st.subheader("💬 Full Recommendations — Side by Side")

        llm_colors = {
            'MiniMax-M2 (Ollama)':      '#E91E63',
            'DeepSeek-V3 (Ollama)':     '#FF5722',
            'GLM-5 (Ollama)':           '#9C27B0',
            'Kimi-K2 (Ollama)':         '#00BCD4',
            'Qwen3-Next-80B (Ollama)':  '#00796B',
            'Gemini (Google)':          '#FF9800',
            'GPT-3.5 (OpenAI)':         '#4CAF50',
        }

        # Render in a 2-column grid so each card is readable
        for row_start in range(0, len(results), 2):
            row_items = results[row_start:row_start + 2]
            cols = st.columns(2)
            for col, r in zip(cols, row_items):
                color = llm_colors.get(r['llm_name'], '#888')
                with col:
                    demo_badge = " <small style='background:#ff9800;color:white;padding:2px 6px;border-radius:4px;'>DEMO</small>" if r.get('is_demo') else ""
                    st.markdown(f"""
                    <div style='border: 2px solid {color}; border-radius: 8px; padding: 10px;
                                background: {color}10; margin-bottom: 8px;'>
                        <h4 style='color: {color}; margin: 0;'>{r['llm_name']}{demo_badge}</h4>
                        <small style='color: #666;'>{r['model_name']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    if r['success']:
                        st.markdown(f"⏱️ `{r['latency_ms']:.0f}ms` | 📝 `{r['word_count']} words` | ⭐ `{r['quality_score']}/100`")
                        st.markdown("---")
                        st.markdown(r['response'])
                    else:
                        st.error(f"❌ Failed: {r['error']}")

        st.markdown("---")

        # ── Collective Recommendation ─────────────────────────────────────────
        st.subheader("🤝 Collective Recommendation")
        st.markdown("**Synthesized from all 7 AI models — what they collectively agree on**")

        collective = comparison.get("collective")
        if collective:
            # Summary banner
            agreement_color = {"High Agreement": "#2ca02c", "Moderate Agreement": "#ff7f0e", "Mixed Opinions": "#d62728"}.get(collective["agreement_level"], "#888")
            st.markdown(f"""
            <div style='padding: 16px; background: {agreement_color}18; border-left: 5px solid {agreement_color};
                        border-radius: 6px; margin-bottom: 12px;'>
                <h4 style='margin:0; color:{agreement_color};'>{collective["agreement_level"]} across {collective["models_agreed"]} models</h4>
                <p style='margin: 6px 0 0 0;'>{collective["summary"]}</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Agreed Priority", collective["agreed_priority"])
            with col2:
                st.metric("Priority Agreement", f"{collective['priority_agreement']}%")
            with col3:
                st.metric("Avg Confidence", f"{collective['avg_confidence']}%")
            with col4:
                st.metric("Avg Quality Score", f"{collective['avg_quality_score']}/100")

            if collective["top_actions"]:
                st.markdown("**Most mentioned actions across all models:**")
                for action, count in collective["top_actions"]:
                    bar = "█" * min(count, 10)
                    st.markdown(f"- `{bar}` **{action.title()}** — mentioned {count}x")

            st.markdown(f"**Best individual response from:** {collective['best_response_from']}")
            with st.expander("View best response text"):
                st.markdown(collective["best_response_text"])
        else:
            st.info("Run the comparison above to see collective recommendation.")

        st.markdown("---")

        # ── Scoring breakdown ─────────────────────────────────────────────────
        st.subheader("🔍 Quality Scoring Breakdown")
        st.markdown("""
        Each response is scored on **5 criteria (20 pts each)**:

        | Criterion | What We Check |
        |-----------|--------------|
        | Root Cause | Contains "cause", "reason", "due to" |
        | Immediate Action | Contains "immediate", "24 hour", "urgent" |
        | Long-term Fix | Contains "permanent", "replace", "overhaul" |
        | Priority/Confidence | Contains "priority", "critical", "%" |
        | Response Length | ≥80 words = 20pts, ≥40 words = 10pts |
        """)


def show_voice_agent(df, risk_data, scheduler=None):
    """📞 Omi Dimension AI — Voice Agent Management"""
    st.header("📞 Voice Agent — Omi Dimension AI")
    st.markdown("**Live voice assistant that answers calls about machine faults, risks, and maintenance**")

    from agents.omi_voice_agent import create_voice_agent, update_voice_agent, OMI_API_KEY

    AGENT_ID   = "131316"
    CALL_TO    = "+18668740093"
    API_KEY    = os.getenv("OMI_API_KEY", "")

    # Generate live schedule to pass into agent context
    live_schedule = None
    if scheduler is not None:
        try:
            live_schedule = scheduler.generate_schedule(days_ahead=7)
        except Exception:
            live_schedule = None

    # ── CALL SECTION ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style='padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-radius: 12px; border: 2px solid #00BCD4; text-align: center; margin-bottom: 20px;'>
        <h2 style='color: #00BCD4; margin: 0 0 8px 0;'>🎙️ PlantPulse Voice Assistant</h2>
        <p style='color: #aaa; margin: 0 0 4px 0; font-size: 0.95em;'>
            Agent ID: #131254 &nbsp;|&nbsp; Powered by Omi Dimension AI
        </p>
        <p style='color: #ccc; margin: 0; font-size: 0.9em;'>
            Ask about machine faults, risk levels, maintenance schedules, cascade risks, and costs
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if st.button("📞 Call Me — Connect to Voice Agent", use_container_width=True, type="primary"):
            with st.spinner("Calling +91 8999163408 ..."):
                try:
                    from omnidimension import Client
                    client = Client(API_KEY)
                    call_response = client.call.dispatch_call(
                        agent_id=int(AGENT_ID),
                        to_number="+918999163408",
                    )
                    st.session_state['omi_call_response'] = call_response
                    st.success("✅ Call initiated! +91 8999163408 will ring in a few seconds.")
                    st.json(call_response)
                except ImportError:
                    st.error("Run: pip install omnidimension")
                except Exception as e:
                    st.error(f"❌ Call failed: {e}")

        st.markdown("""
        <div style='text-align: center; margin-top: 6px;'>
            <p style='color: #888; font-size: 0.82em;'>
                The agent will call <strong>+91 8999163408</strong> and speak in English, Hindi, or Marathi
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── WHAT YOU CAN ASK ─────────────────────────────────────────────────────
    st.subheader("💬 What You Can Ask the Voice Agent")
    q_col1, q_col2 = st.columns(2)
    with q_col1:
        st.info('🔴 "Which machines are critical right now?"')
        st.info('🔧 "What is the status of M5?"')
        st.info('⛓️ "What happens if M3 fails?"')
        st.info('📅 "What is the maintenance schedule?"')
    with q_col2:
        st.info('💰 "What is the downtime cost?"')
        st.info('🤖 "Which machines have ML anomalies?"')
        st.info('🔩 "What repairs are needed for vibration issues?"')
        st.info('📊 "What does this platform do?"')

    st.markdown("---")

    # ── LIVE DATA PREVIEW ─────────────────────────────────────────────────────
    st.subheader("📊 Live Data in Agent Context")
    critical = [r for r in risk_data if r['risk_level'] == 'Critical']
    high     = [r for r in risk_data if r['risk_level'] == 'High']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Critical Machines", len(critical))
    with col2:
        st.metric("High Risk Machines", len(high))
    with col3:
        st.metric("Total Machines", len(risk_data))

    with st.expander("👁️ Preview machine data the agent knows"):
        from datetime import datetime, timedelta
        rows = []
        for r in risk_data:
            machine_logs = df[df['machine_id'] == r['machine_id']]
            recent = len(machine_logs[machine_logs['date'] >= datetime.now() - timedelta(days=7)])
            top_issue = machine_logs['issue_type'].mode()[0] if len(machine_logs) > 0 else "unknown"
            rows.append({
                "Machine": r['machine_id'],
                "Risk Level": r['risk_level'],
                "Score": r['risk_score'],
                "Main Issue": top_issue.title(),
                "Recent (7d)": recent,
                "ML Anomaly": "🤖 Yes" if r.get('ml_anomaly') else "✓ No",
                "Failure Window": r.get('predicted_window', 'N/A'),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── UPDATE AGENT ──────────────────────────────────────────────────────────
    st.subheader("🔄 Update Agent with Latest Data")
    if st.button("Push Live Machine Data to Agent", use_container_width=True):
        with st.spinner("Updating agent context with current machine data..."):
            result = update_voice_agent(AGENT_ID, risk_data, df, live_schedule)
        if result["success"]:
            st.success("✅ Agent updated with latest machine data!")
        else:
            st.error(f"❌ {result['error']}")

    st.markdown("---")

    # ── CONFIG SUMMARY ────────────────────────────────────────────────────────
    st.subheader("⚙️ Agent Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        Agent ID: #131254
        Model: gpt-4.1-mini (temperature 0.7)
        Voice: Google en-IN Chirp3-HD-Despina
        Languages: English, Hindi, Marathi
        """)
    with col2:
        st.markdown("""
        Transcriber: Azure (silence timeout 400ms)
        Interruption: Enabled (min 2 words)
        Noise reduction: On
        Max call duration: 10 minutes
        """)

    st.markdown("---")
    st.subheader("📋 Install Dependency")
    st.code("pip install omnidimension", language="bash")


if __name__ == "__main__":
    main()
