# database/database_manager.py
"""
Database Manager for NEAR Partnership Analysis

Handles SQLite database operations including:
- Schema initialization and migrations
- Data storage and retrieval
- Export functionality
- Concurrent access management
"""

import sqlite3
import json
from datetime import datetime
from agents.config import DATABASE_NAME, DATABASE_PRAGMAS


class DatabaseManager:
    """
    Manages all database operations for the multi-agent analysis system.
    Handles schema creation, data persistence, and export functionality.
    """
    
    def __init__(self, db_path=None):
        """Initialize the database manager."""
        self.db_path = db_path or DATABASE_NAME
    
    def initialize_database(self):
        """
        Initialize enhanced database schema with full traceability and concurrent access support.
        
        Returns:
            tuple: (connection, cursor) for immediate use
        """
        # Enable WAL mode for better concurrent access
        conn = sqlite3.connect(self.db_path)
        
        # Apply database optimizations
        for pragma in DATABASE_PRAGMAS:
            conn.execute(pragma)
        
        cursor = conn.cursor()
        
        # Create schema
        self._create_tables(cursor)
        
        conn.commit()
        return conn, cursor
    
    def _create_tables(self, cursor):
        """Create all required database tables."""
        
        # General research table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_research (
                project_name TEXT PRIMARY KEY,
                slug TEXT,
                research_data TEXT,
                sources TEXT,
                success BOOLEAN,
                error TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        # Question-specific analyses table (with project-specific caching)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_analyses (
                cache_key TEXT PRIMARY KEY,
                project_name TEXT,
                question_id INTEGER,
                question_key TEXT,
                research_data TEXT,
                sources TEXT,
                analysis TEXT,
                score INTEGER,
                confidence TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (project_name) REFERENCES project_research (project_name)
            )
        ''')
        
        # Final summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS final_summaries (
                project_name TEXT PRIMARY KEY,
                slug TEXT,
                summary TEXT,
                total_score INTEGER,
                recommendation TEXT,
                success BOOLEAN,
                error TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_name) REFERENCES project_research (project_name)
            )
        ''')
    
    def export_comprehensive_data(self):
        """
        Export comprehensive analysis data with full traceability.
        
        Returns:
            tuple: (export_data, filename) containing all analysis results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Export with full traceability
            cursor.execute('''
                SELECT 
                    fs.project_name, fs.slug, fs.total_score, fs.recommendation,
                    pr.research_data, pr.sources as general_sources,
                    fs.summary, fs.created_at
                FROM final_summaries fs
                LEFT JOIN project_research pr ON fs.project_name = pr.project_name
                ORDER BY fs.total_score DESC, fs.updated_at DESC
            ''')
            
            summaries = cursor.fetchall()
            
            export_data = []
            for row in summaries:
                project_name = row[0]
                
                # Get question details
                cursor.execute('''
                    SELECT question_id, question_key, analysis, score, confidence, sources
                    FROM question_analyses 
                    WHERE project_name = ?
                    ORDER BY question_id
                ''', (project_name,))
                
                question_details = []
                for q_row in cursor.fetchall():
                    question_details.append({
                        "question_id": q_row[0],
                        "question_key": q_row[1],
                        "analysis": q_row[2],
                        "score": q_row[3],
                        "confidence": q_row[4],
                        "sources": json.loads(q_row[5]) if q_row[5] else []
                    })
                
                export_data.append({
                    "project_name": row[0],
                    "slug": row[1],
                    "total_score": row[2],
                    "recommendation": row[3],
                    "general_research": row[4],
                    "general_sources": json.loads(row[5]) if row[5] else [],
                    "question_analyses": question_details,
                    "final_summary": row[6],
                    "created_at": row[7]
                })
            
            export_filename = f"multi_agent_analyses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return export_data, export_filename
            
        finally:
            conn.close()
    
    def save_export_data(self, export_data, filename):
        """Save export data to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def get_analysis_statistics(self, export_data):
        """Generate summary statistics from export data."""
        if not export_data:
            return {}
        
        scores = [item["total_score"] for item in export_data]
        return {
            "total_projects": len(export_data),
            "min_score": min(scores),
            "max_score": max(scores),
            "avg_score": sum(scores) / len(scores)
        } 