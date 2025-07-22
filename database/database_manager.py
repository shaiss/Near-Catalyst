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
from config.config import DATABASE_NAME, DATABASE_PRAGMAS


class DatabaseManager:
    """
    Manages all database operations for the multi-agent analysis system.
    Handles schema creation, data persistence, and export functionality.
    """
    
    def __init__(self, db_path=None):
        """Initialize the database manager."""
        self.db_path = db_path or DATABASE_NAME
    
    def initialize_database(self):
        """Initialize database with required tables and return connection."""
        conn = sqlite3.connect(self.db_path)
        conn.execute('PRAGMA journal_mode=WAL;')  # Enable WAL mode for concurrent access
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS project_research (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            slug TEXT,
            research_data TEXT,
            sources TEXT,
            success BOOLEAN,
            error TEXT,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(project_name)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS question_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            question_key TEXT NOT NULL,
            research_data TEXT,
            sources TEXT,
            analysis TEXT,
            score INTEGER,
            confidence TEXT,
            cache_key TEXT UNIQUE,
            created_at TEXT,
            updated_at TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS final_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL UNIQUE,
            slug TEXT,
            total_score INTEGER,
            recommendation TEXT,
            summary TEXT,
            success BOOLEAN,
            error TEXT,
            created_at TEXT,
            updated_at TEXT
        )''')

        # Add deep research table for enhanced AI analysis
        cursor.execute('''CREATE TABLE IF NOT EXISTS deep_research_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL UNIQUE,
            slug TEXT,
            research_data TEXT,
            sources TEXT,
            elapsed_time REAL,
            tool_calls_made INTEGER,
            estimated_cost REAL,
            success BOOLEAN,
            enabled BOOLEAN,
            enhanced_prompt TEXT,
            created_at TEXT,
            updated_at TEXT
        )''')

        # Add NEAR catalog cache table for storing full project details
        cursor.execute('''CREATE TABLE IF NOT EXISTS project_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            catalog_data TEXT NOT NULL,  -- JSON string of full catalog data
            name TEXT,
            description TEXT,
            category TEXT,
            stage TEXT,
            tech_stack TEXT,
            website TEXT,
            github TEXT,
            twitter TEXT,
            created_at TEXT,
            updated_at TEXT
        )''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_name ON project_research(project_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_question_cache ON question_analyses(cache_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_final_project ON final_summaries(project_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deep_research_project ON deep_research_data(project_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_catalog_slug ON project_catalog(slug)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_catalog_project ON project_catalog(project_name)')
        
        conn.commit()
        return conn, cursor

    def store_catalog_data(self, project_name, slug, catalog_data):
        """
        Store NEAR catalog data for a project.
        
        Args:
            project_name (str): Name of the project
            slug (str): Project slug
            catalog_data (dict): Full catalog data from NEAR API
        """
        if not catalog_data:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract key fields for easier querying
            name = catalog_data.get('name', project_name)
            description = catalog_data.get('description', '')
            category = catalog_data.get('category', '')
            stage = catalog_data.get('stage', '')
            tech_stack = catalog_data.get('tech_stack', '')
            website = catalog_data.get('website', '')
            github = catalog_data.get('github', '')
            twitter = catalog_data.get('twitter', '')
            
            now = datetime.now().isoformat()
            
            cursor.execute('''INSERT OR REPLACE INTO project_catalog 
                             (project_name, slug, catalog_data, name, description, category, 
                              stage, tech_stack, website, github, twitter, created_at, updated_at)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (project_name, slug, json.dumps(catalog_data), name, description, 
                           category, stage, tech_stack, website, github, twitter, now, now))
            
            conn.commit()
            conn.close()
            print(f"    ✓ Stored NEAR catalog data for {project_name}")
            
        except Exception as e:
            print(f"    ⚠️ Failed to store catalog data: {e}")
            if 'conn' in locals():
                conn.close()

    def get_catalog_data(self, project_name):
        """
        Retrieve cached NEAR catalog data for a project.
        
        Args:
            project_name (str): Name of the project
            
        Returns:
            dict: Catalog data if found, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT catalog_data FROM project_catalog WHERE project_name = ?', (project_name,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return json.loads(result[0])
            return None
            
        except Exception as e:
            print(f"    ⚠️ Failed to retrieve catalog data: {e}")
            return None
    
    def debug_project_data(self, project_name):
        """
        Debug function to analyze data quality issues for a specific project.
        
        Args:
            project_name (str): Name of the project to debug
            
        Returns:
            dict: Comprehensive debugging information
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            debug_info = {
                "project_name": project_name,
                "general_research": None,
                "deep_research": None,
                "question_analyses": [],
                "final_summary": None,
                "issues": []
            }
            
            # Check general research
            cursor.execute('SELECT * FROM project_research WHERE project_name = ?', (project_name,))
            general_research = cursor.fetchone()
            if general_research:
                debug_info["general_research"] = {
                    "success": general_research[4],
                    "data_length": len(general_research[2]) if general_research[2] else 0,
                    "sources_count": len(json.loads(general_research[3])) if general_research[3] else 0,
                    "error": general_research[5]
                }
            else:
                debug_info["issues"].append("No general research found")
            
            # Check deep research
            cursor.execute('SELECT * FROM deep_research_data WHERE project_name = ?', (project_name,))
            deep_research = cursor.fetchone()
            if deep_research:
                debug_info["deep_research"] = {
                    "success": deep_research[4],
                    "enabled": deep_research[5],
                    "data_length": len(deep_research[2]) if deep_research[2] else 0,
                    "sources_count": len(json.loads(deep_research[3])) if deep_research[3] else 0,
                    "tool_calls": deep_research[8],
                    "elapsed_time": deep_research[7],
                    "enhanced_prompt_length": len(deep_research[10]) if deep_research[10] else 0,
                    "error": deep_research[6]
                }
                
                # Check if enhanced_prompt appears truncated
                if deep_research[10] and len(deep_research[10]) > 0:
                    if deep_research[10].endswith("..."):
                        debug_info["issues"].append("Enhanced prompt appears truncated")
            
            # Check question analyses
            cursor.execute('''SELECT * FROM question_analyses WHERE project_name = ? ORDER BY question_id''', (project_name,))
            question_results = cursor.fetchall()
            
            for q_result in question_results:
                q_info = {
                    "question_id": q_result[2],
                    "question_key": q_result[3],
                    "research_data_length": len(q_result[4]) if q_result[4] else 0,
                    "analysis_length": len(q_result[6]) if q_result[6] else 0,
                    "score": q_result[7],
                    "confidence": q_result[8],
                    "has_analysis": bool(q_result[6] and q_result[6].strip()),
                    "analysis_preview": q_result[6][:100] if q_result[6] else None
                }
                
                # Check for issues
                if not q_info["has_analysis"]:
                    debug_info["issues"].append(f"Q{q_info['question_id']}: Empty analysis")
                if q_result[7] is None:
                    debug_info["issues"].append(f"Q{q_info['question_id']}: NULL score")
                if not q_result[4]:
                    debug_info["issues"].append(f"Q{q_info['question_id']}: Empty research data")
                
                debug_info["question_analyses"].append(q_info)
            
            # Check final summary
            cursor.execute('SELECT * FROM final_summaries WHERE project_name = ?', (project_name,))
            final_summary = cursor.fetchone()
            if final_summary:
                debug_info["final_summary"] = {
                    "success": final_summary[5],
                    "total_score": final_summary[3],
                    "recommendation": final_summary[4],
                    "summary_length": len(final_summary[2]) if final_summary[2] else 0,
                    "error": final_summary[6]
                }
                
                if not final_summary[5]:
                    debug_info["issues"].append(f"Final summary failed: {final_summary[6]}")
            else:
                debug_info["issues"].append("No final summary found")
            
            return debug_info
            
        finally:
            conn.close()
    
    def list_problematic_projects(self):
        """
        Identify projects with data quality issues.
        
        Returns:
            dict: Summary of projects with various issues
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            issues = {
                "empty_analyses": [],
                "failed_summaries": [],
                "missing_deep_research": [],
                "zero_scores": []
            }
            
            # Find projects with empty question analyses
            cursor.execute('''
                SELECT DISTINCT project_name 
                FROM question_analyses 
                WHERE analysis IS NULL OR analysis = '' OR TRIM(analysis) = ''
            ''')
            issues["empty_analyses"] = [row[0] for row in cursor.fetchall()]
            
            # Find projects with failed final summaries
            cursor.execute('''
                SELECT project_name, error 
                FROM final_summaries 
                WHERE success = 0 OR error IS NOT NULL
            ''')
            issues["failed_summaries"] = [(row[0], row[1]) for row in cursor.fetchall()]
            
            # Find projects that should have deep research but don't
            cursor.execute('''
                SELECT pr.project_name 
                FROM project_research pr
                LEFT JOIN deep_research_data dr ON pr.project_name = dr.project_name
                WHERE dr.project_name IS NULL
            ''')
            issues["missing_deep_research"] = [row[0] for row in cursor.fetchall()]
            
            # Find projects with all zero scores (might indicate parsing issues)
            cursor.execute('''
                SELECT project_name, COUNT(*) as question_count, SUM(score) as total_score
                FROM question_analyses 
                GROUP BY project_name
                HAVING total_score = 0 AND question_count >= 6
            ''')
            issues["zero_scores"] = [(row[0], row[1]) for row in cursor.fetchall()]
            
            return issues
            
        finally:
            conn.close()
    
    def export_comprehensive_data(self):
        """
        Export comprehensive analysis data with full traceability.
        
        Returns:
            tuple: (export_data, filename) containing all analysis results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Export with full traceability including deep research
            cursor.execute('''
                SELECT 
                    fs.project_name, fs.slug, fs.total_score, fs.recommendation,
                    pr.research_data, pr.sources as general_sources,
                    dr.research_data as deep_research_data, dr.sources as deep_research_sources,
                    dr.success as deep_research_success, dr.enabled as deep_research_enabled,
                    dr.elapsed_time as deep_research_time, dr.tool_calls_made as deep_research_tools,
                    dr.estimated_cost as deep_research_cost,
                    fs.summary, fs.created_at
                FROM final_summaries fs
                LEFT JOIN project_research pr ON fs.project_name = pr.project_name
                LEFT JOIN deep_research_data dr ON fs.project_name = dr.project_name
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
                
                # Build export record
                export_record = {
                    "project_name": row[0],
                    "slug": row[1],
                    "total_score": row[2],
                    "recommendation": row[3],
                    "general_research": row[4],
                    "general_sources": json.loads(row[5]) if row[5] else [],
                    "question_analyses": question_details,
                    "final_summary": row[13],
                    "created_at": row[14]
                }
                
                # Add deep research data if available
                if row[6]:  # deep_research_data exists
                    export_record["deep_research"] = {
                        "research_data": row[6],
                        "sources": json.loads(row[7]) if row[7] else [],
                        "success": row[8],
                        "enabled": row[9],
                        "elapsed_time": row[10],
                        "tool_calls_made": row[11],
                        "estimated_cost": row[12]
                    }
                else:
                    export_record["deep_research"] = None
                
                export_data.append(export_record)
            
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
    
    def clear_projects(self, project_identifiers=None):
        """
        Clear projects from the database.
        
        Args:
            project_identifiers (list or str): List of project names/slugs to clear, 
                                             or 'all' to clear everything
        
        Returns:
            dict: Summary of clearing operation
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if project_identifiers == 'all':
                return self._clear_all_projects(cursor, conn)
            elif isinstance(project_identifiers, (list, tuple)):
                return self._clear_specific_projects(cursor, conn, project_identifiers)
            else:
                raise ValueError("project_identifiers must be 'all' or a list of identifiers")
                
        finally:
            conn.close()
    
    def _clear_all_projects(self, cursor, conn):
        """Clear all projects from all tables."""
        # Get count before clearing
        cursor.execute('SELECT COUNT(*) FROM final_summaries')
        total_projects = cursor.fetchone()[0]
        
        if total_projects == 0:
            return {
                'cleared_projects': 0,
                'total_projects': 0,
                'message': 'Database is already empty'
            }
        
        # Clear all tables (order matters due to foreign keys)
        cursor.execute('DELETE FROM question_analyses')
        question_count = cursor.rowcount
        
        cursor.execute('DELETE FROM final_summaries')
        summary_count = cursor.rowcount
        
        cursor.execute('DELETE FROM project_research')
        research_count = cursor.rowcount
        
        cursor.execute('DELETE FROM deep_research_data')
        deep_research_count = cursor.rowcount
        
        conn.commit()
        
        return {
            'cleared_projects': total_projects,
            'total_projects': total_projects,
            'cleared_records': {
                'question_analyses': question_count,
                'final_summaries': summary_count,
                'project_research': research_count,
                'deep_research_data': deep_research_count
            },
            'message': f'Successfully cleared all {total_projects} projects from database'
        }
    
    def store_deep_research_data(self, project_name, slug, deep_research_result):
        """
        Store deep research results in the database.
        
        Args:
            project_name (str): Name of the project
            slug (str): Project slug
            deep_research_result (dict): Deep research results from DeepResearchAgent
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Store full enhanced_prompt without truncation for debugging
            enhanced_prompt = deep_research_result.get("enhanced_prompt", "")
            
            cursor.execute('''INSERT OR REPLACE INTO deep_research_data 
                             (project_name, slug, research_data, sources, success, enabled, error, 
                              elapsed_time, tool_calls_made, estimated_cost, enhanced_prompt, 
                              created_at, updated_at)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (project_name, slug, 
                           deep_research_result.get("content", ""),
                           json.dumps(deep_research_result.get("sources", [])),
                           deep_research_result.get("success", False),
                           deep_research_result.get("enabled", False),
                           deep_research_result.get("error", ""),
                           deep_research_result.get("elapsed_time", 0),
                           deep_research_result.get("tool_calls_made", 0),
                           deep_research_result.get("estimated_cost", 0),
                           enhanced_prompt,  # Store full prompt without truncation
                           datetime.now().isoformat(), 
                           datetime.now().isoformat()))
            conn.commit()
            
        finally:
            conn.close()
    
    def get_deep_research_data(self, project_name):
        """
        Retrieve deep research data for a project.
        
        Args:
            project_name (str): Name of the project
            
        Returns:
            dict or None: Deep research data if it exists
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM deep_research_data WHERE project_name = ?', (project_name,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "project_name": result[0],
                    "slug": result[1],
                    "research_data": result[2],
                    "sources": json.loads(result[3]) if result[3] else [],
                    "success": result[4],
                    "enabled": result[5],
                    "error": result[6],
                    "elapsed_time": result[7],
                    "tool_calls_made": result[8],
                    "estimated_cost": result[9],
                    "enhanced_prompt": result[10],
                    "created_at": result[11],
                    "updated_at": result[12]
                }
            return None
            
        finally:
            conn.close()
    
    def _clear_specific_projects(self, cursor, conn, project_identifiers):
        """Clear specific projects by name or slug."""
        cleared_projects = []
        not_found_projects = []
        
        for identifier in project_identifiers:
            # Check if project exists by name or slug
            cursor.execute('''
                SELECT project_name FROM project_research 
                WHERE project_name = ? OR slug = ?
            ''', (identifier, identifier))
            
            result = cursor.fetchone()
            if result:
                project_name = result[0]
                cleared_projects.append(project_name)
                
                # Clear from all tables (order matters due to foreign keys)
                cursor.execute('DELETE FROM question_analyses WHERE project_name = ?', (project_name,))
                cursor.execute('DELETE FROM final_summaries WHERE project_name = ?', (project_name,))
                cursor.execute('DELETE FROM project_research WHERE project_name = ?', (project_name,))
                cursor.execute('DELETE FROM deep_research_data WHERE project_name = ?', (project_name,))
            else:
                not_found_projects.append(identifier)
        
        conn.commit()
        
        result = {
            'cleared_projects': len(cleared_projects),
            'total_requested': len(project_identifiers),
            'cleared_names': cleared_projects,
            'message': f'Successfully cleared {len(cleared_projects)} project(s) from database'
        }
        
        if not_found_projects:
            result['not_found'] = not_found_projects
            result['message'] += f'. {len(not_found_projects)} project(s) not found: {not_found_projects}'
        
        return result
    
    def list_projects(self):
        """
        List all projects in the database.
        
        Returns:
            list: List of project information (name, slug, score, updated_at)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT pr.project_name, pr.slug, fs.total_score, fs.updated_at, dr.success as deep_research_success
                FROM project_research pr
                LEFT JOIN final_summaries fs ON pr.project_name = fs.project_name
                LEFT JOIN deep_research_data dr ON pr.project_name = dr.project_name
                ORDER BY pr.project_name
            ''')
            
            projects = []
            for row in cursor.fetchall():
                projects.append({
                    'name': row[0],
                    'slug': row[1],
                    'score': row[2],
                    'updated_at': row[3],
                    'deep_research_performed': row[4]
                })
            
            return projects
            
        finally:
            conn.close() 