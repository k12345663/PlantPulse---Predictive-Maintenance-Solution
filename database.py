"""Database management for PlantPulse AI"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

class MaintenanceDatabase:
    """SQLite database for maintenance logs and risk data"""
    
    def __init__(self, db_path='data/plantpulse.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table 1: maintenance_logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT NOT NULL,
                machine_type TEXT,
                production_line TEXT,
                log_date TEXT NOT NULL,
                technician TEXT,
                technician_note TEXT NOT NULL,
                issue_category TEXT,
                severity TEXT,
                action_taken TEXT,
                downtime_minutes INTEGER DEFAULT 0,
                downtime_cost_inr REAL DEFAULT 0,
                parts_replaced TEXT,
                parts_cost_inr REAL DEFAULT 0,
                labor_cost_inr REAL DEFAULT 0,
                total_cost_inr REAL DEFAULT 0,
                maintenance_type TEXT,
                criticality TEXT,
                shift TEXT,
                incident_flag INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table 2: machine_risk
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS machine_risk (
                machine_id TEXT PRIMARY KEY,
                risk_score REAL,
                risk_level TEXT,
                last_updated TEXT,
                explanation TEXT
            )
        ''')
        
        # Table 3: maintenance_schedule
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_schedule (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT,
                maintenance_type TEXT,
                priority TEXT,
                priority_rank INTEGER,
                suggested_date TEXT,
                suggested_time TEXT,
                suggested_time_slot TEXT,
                estimated_duration TEXT,
                estimated_duration_minutes INTEGER,
                technician TEXT,
                reason TEXT,
                actions TEXT,
                status TEXT DEFAULT 'Scheduled',
                schedule_source TEXT DEFAULT 'auto',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_csv_to_db(self, csv_path='data/maintenance_logs.csv'):
        """Load CSV data into database"""
        if not os.path.exists(csv_path):
            return False
        
        df = pd.read_csv(csv_path)
        conn = sqlite3.connect(self.db_path)
        
        # Map CSV columns to database columns
        df_mapped = df.rename(columns={
            'date': 'log_date',
            'issue_type': 'issue_category'
        })
        
        # Add missing columns with defaults
        if 'maintenance_type' not in df_mapped.columns:
            df_mapped['maintenance_type'] = 'corrective'
        if 'incident_flag' not in df_mapped.columns:
            df_mapped['incident_flag'] = 0
        if 'severity' not in df_mapped.columns:
            df_mapped['severity'] = df_mapped['criticality']
        
        # Select only columns that exist in the database
        db_columns = [
            'machine_id', 'machine_type', 'production_line', 'log_date',
            'technician', 'technician_note', 'issue_category', 'severity',
            'action_taken', 'downtime_minutes', 'downtime_cost_inr',
            'parts_replaced', 'parts_cost_inr', 'labor_cost_inr',
            'total_cost_inr', 'maintenance_type', 'criticality',
            'shift', 'incident_flag'
        ]
        
        df_to_insert = df_mapped[[col for col in db_columns if col in df_mapped.columns]]
        
        # Insert into database
        df_to_insert.to_sql('maintenance_logs', conn, if_exists='append', index=False)
        
        conn.close()
        return True
    
    def add_log(self, log_data):
        """Add a new maintenance log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO maintenance_logs (
                machine_id, machine_type, production_line, log_date,
                technician_note, issue_category, severity, action_taken,
                downtime_minutes, parts_replaced, maintenance_type,
                criticality, incident_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_data.get('machine_id'),
            log_data.get('machine_type', 'Motor'),
            log_data.get('production_line', 'Line-A'),
            log_data.get('log_date', datetime.now().strftime('%Y-%m-%d %H:%M')),
            log_data.get('technician_note'),
            log_data.get('issue_category'),
            log_data.get('severity', 'Medium'),
            log_data.get('action_taken'),
            log_data.get('downtime_minutes', 0),
            log_data.get('parts_replaced'),
            log_data.get('maintenance_type', 'corrective'),
            log_data.get('criticality', 'Medium'),
            log_data.get('incident_flag', 0)
        ))
        
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        
        return log_id
    
    def get_all_logs(self):
        """Get all maintenance logs as DataFrame"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM maintenance_logs ORDER BY log_date DESC', conn)
        conn.close()
        return df
    
    def get_logs_for_machine(self, machine_id):
        """Get logs for specific machine"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            'SELECT * FROM maintenance_logs WHERE machine_id = ? ORDER BY log_date DESC',
            conn,
            params=(machine_id,)
        )
        conn.close()
        return df
    
    def update_risk(self, machine_id, risk_score, risk_level, explanation):
        """Update machine risk data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO machine_risk (
                machine_id, risk_score, risk_level, last_updated, explanation
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            machine_id,
            risk_score,
            risk_level,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            explanation
        ))
        
        conn.commit()
        conn.close()
    
    def get_all_risks(self):
        """Get all machine risks"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM machine_risk ORDER BY risk_score DESC', conn)
        conn.close()
        return df
    
    def clear_schedule(self):
        """Clear existing schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM maintenance_schedule')
        conn.commit()
        conn.close()
    
    def add_schedule_item(self, schedule_data):
        """Add maintenance schedule item"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO maintenance_schedule (
                machine_id, priority_rank, suggested_date,
                suggested_time_slot, estimated_duration_minutes, reason
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            schedule_data['machine_id'],
            schedule_data['priority_rank'],
            schedule_data['suggested_date'],
            schedule_data['suggested_time_slot'],
            schedule_data['estimated_duration_minutes'],
            schedule_data['reason']
        ))
        
        conn.commit()
        conn.close()
    
    def add_manual_schedule(self, schedule_data):
        """Add manual maintenance schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert actions list to string
        actions_str = '\n'.join(schedule_data.get('actions', []))
        
        cursor.execute('''
            INSERT INTO maintenance_schedule (
                machine_id, maintenance_type, priority, suggested_date,
                suggested_time, estimated_duration, technician, reason,
                actions, status, schedule_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            schedule_data['machine_id'],
            schedule_data.get('maintenance_type', 'Preventive'),
            schedule_data.get('priority', 'Medium'),
            schedule_data['scheduled_date'],
            schedule_data['scheduled_time'],
            schedule_data['estimated_duration'],
            schedule_data.get('technician', 'To be assigned'),
            schedule_data['reason'],
            actions_str,
            schedule_data.get('status', 'Scheduled'),
            'manual'
        ))
        
        conn.commit()
        schedule_id = cursor.lastrowid
        conn.close()
        
        return schedule_id
    
    def get_schedule(self):
        """Get maintenance schedule"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            'SELECT * FROM maintenance_schedule ORDER BY priority_rank',
            conn
        )
        conn.close()
        return df
    
    def get_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM maintenance_logs')
        total_logs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT machine_id) FROM maintenance_logs')
        total_machines = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM machine_risk WHERE risk_score >= 50')
        high_risk_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_logs': total_logs,
            'total_machines': total_machines,
            'high_risk_machines': high_risk_count
        }
