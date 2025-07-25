#!/usr/bin/env python3
"""
NEAR Catalyst Framework Dashboard Server

A Flask-based web dashboard for visualizing hackathon catalyst discovery results
from the NEAR Catalyst Framework multi-agent system.
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
import argparse
import socket
import random

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'project_analyses_multi_agent.db')
FRONTEND_DIR = 'frontend'

def is_port_available(host, port):
    """Check if a port is available on the given host"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0  # Port is available if connection fails
    except Exception:
        return False

def find_available_port(host, preferred_port=None, port_range=(8000, 8999)):
    """
    Find an available port, preferring the specified port if available,
    otherwise choosing a random port in the specified range.
    """
    # First try the preferred port if specified
    if preferred_port and is_port_available(host, preferred_port):
        return preferred_port
    
    # If preferred port is not available or not specified, try random ports in range
    start_port, end_port = port_range
    attempts = 0
    max_attempts = 50
    
    while attempts < max_attempts:
        # Choose a random port in the range
        random_port = random.randint(start_port, end_port)
        
        if is_port_available(host, random_port):
            return random_port
        
        attempts += 1
    
    # If we can't find an available port in the range, raise an exception
    raise RuntimeError(f"Could not find an available port in range {start_port}-{end_port} after {max_attempts} attempts")

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def clean_and_structure_text(text):
    """Clean and structure text content for better display"""
    if not text:
        return None
    
    # Remove excessive markdown formatting that causes issues
    cleaned = text.replace('**', '').replace('***', '').replace('####', '###')
    
    # Split into paragraphs and clean up
    paragraphs = [p.strip() for p in cleaned.split('\n\n') if p.strip()]
    
    # Try to extract structured information
    structured = {
        'full_text': cleaned,
        'summary': paragraphs[0] if paragraphs else cleaned[:500],
        'key_points': [],
        'analysis_sections': []
    }
    
    # Extract key points (lines starting with numbers, bullets, or capital letters)
    for para in paragraphs:
        lines = para.split('\n')
        for line in lines:
            line = line.strip()
            if (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '-', '*', '•')) or 
                (line.isupper() and len(line) < 100)):
                structured['key_points'].append(line)
            elif line.startswith(('SCORE:', 'ANALYSIS:', 'CONFIDENCE:')):
                structured['analysis_sections'].append(line)
    
    return structured

def format_project_data(row):
    """Format database row into project dictionary"""
    return {
        'project_name': row['project_name'],
        'slug': row['slug'],
        'total_score': row['total_score'],
        'recommendation': row['recommendation'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
        'final_summary': clean_and_structure_text(row['summary'])
    }

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return send_file(os.path.join(FRONTEND_DIR, 'index.html'))

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static frontend files"""
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/api/projects')
def get_projects():
    """Get all projects with summary data"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT project_name, slug, total_score, recommendation, 
                   summary, created_at, updated_at, success
            FROM final_summaries 
            ORDER BY total_score DESC, updated_at DESC
        ''')
        
        projects = []
        for row in cursor.fetchall():
            projects.append(format_project_data(row))
        
        conn.close()
        return jsonify(projects)
        
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/project/<project_name>')
def get_project_details(project_name):
    """Get detailed analysis for a specific project"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get project summary
        cursor.execute('''
            SELECT fs.*, pr.research_data, pr.sources as general_sources
            FROM final_summaries fs
            LEFT JOIN project_research pr ON fs.project_name = pr.project_name
            WHERE fs.project_name = ?
        ''', (project_name,))
        
        project_row = cursor.fetchone()
        if not project_row:
            conn.close()
            return jsonify({'error': 'Project not found'}), 404
        
        # Get question analyses from cache tables (FIXED: reconstruct cache keys properly)
        import hashlib
        
        # Define the diagnostic questions to reconstruct cache keys
        diagnostic_questions = [
            {"id": 1, "question": "Gap-Filler?"},
            {"id": 2, "question": "New Proof-Points?"},
            {"id": 3, "question": "Clear Story?"},
            {"id": 4, "question": "Shared Audience, Different Function?"},
            {"id": 5, "question": "Low-Friction Integration?"},
            {"id": 6, "question": "Hands-On Support?"}
        ]
        
        question_analyses = []
        for q_config in diagnostic_questions:
            # Reconstruct cache key exactly as done in QuestionAgent
            cache_input = f"analysis_q{q_config['id']}:{project_name}:{q_config['question']}"
            cache_key = hashlib.md5(cache_input.encode()).hexdigest()
            
            cursor.execute('SELECT result_data FROM question_analysis WHERE cache_key = ?', (cache_key,))
            cache_row = cursor.fetchone()
            
            if cache_row:
                try:
                    # Parse cached question analysis data
                    analysis_data = json.loads(cache_row['result_data'])
                    question_analyses.append({
                        'question_id': analysis_data.get('question_id'),
                        'question_key': analysis_data.get('question', ''),
                        'analysis': analysis_data.get('analysis', ''),
                        'score': analysis_data.get('score'),
                        'confidence': analysis_data.get('confidence', ''),
                        'sources': [],  # Sources are in research cache
                        'research_data': None  # Will get from research cache if needed
                    })
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing question analysis cache for Q{q_config['id']}: {e}")
                    continue

        # Get deep research data
        cursor.execute('''
            SELECT research_data, sources, elapsed_time, tool_calls_made, estimated_cost,
                   success, enabled, enhanced_prompt
            FROM deep_research_data 
            WHERE project_name = ?
        ''', (project_name,))

        deep_research_row = cursor.fetchone()
        deep_research_data = None
        if deep_research_row:
            deep_research_data = {
                'research_data': deep_research_row['research_data'],
                'sources': json.loads(deep_research_row['sources']) if deep_research_row['sources'] else [],
                'elapsed_time': deep_research_row['elapsed_time'],
                'tool_calls_made': deep_research_row['tool_calls_made'],
                'estimated_cost': deep_research_row['estimated_cost'],
                'success': deep_research_row['success'],
                'enabled': deep_research_row['enabled'],
                'enhanced_prompt': deep_research_row['enhanced_prompt']
            }

        # Get cached NEAR catalog data (NEW)
        cursor.execute('''
            SELECT catalog_data, name, description, category, stage, tech_stack, 
                   website, github, twitter
            FROM project_catalog 
            WHERE project_name = ?
        ''', (project_name,))

        catalog_row = cursor.fetchone()
        catalog_data = None
        if catalog_row:
            catalog_data = {
                'full_data': json.loads(catalog_row['catalog_data']) if catalog_row['catalog_data'] else None,
                'name': catalog_row['name'],
                'description': catalog_row['description'],
                'category': catalog_row['category'],
                'stage': catalog_row['stage'],
                'tech_stack': catalog_row['tech_stack'],
                'website': catalog_row['website'],
                'github': catalog_row['github'],
                'twitter': catalog_row['twitter'],
                'cached': True  # Flag to indicate this is cached data
            }

        # Get real API usage data for cost and time calculations
        try:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(total_tokens) as total_tokens,
                    SUM(estimated_cost) as total_cost,
                    SUM(response_time) as total_time,
                    COUNT(DISTINCT session_id) as total_sessions,
                    AVG(estimated_cost) as avg_cost_per_call,
                    MAX(created_at) as last_analysis_time,
                    COUNT(CASE WHEN reasoning_tokens > 0 THEN 1 END) as reasoning_calls,
                    SUM(reasoning_tokens) as total_reasoning_tokens
                FROM api_usage_tracking 
                WHERE project_name = ?
            ''', (project_name,))

            usage_row = cursor.fetchone()
            usage_data = None
            if usage_row and usage_row['total_calls'] > 0:
                usage_data = {
                    'total_calls': usage_row['total_calls'],
                    'total_tokens': usage_row['total_tokens'],
                    'total_cost': round(usage_row['total_cost'] or 0, 4),
                    'total_time': round(usage_row['total_time'] or 0, 1),
                    'total_sessions': usage_row['total_sessions'],
                    'avg_cost_per_call': round(usage_row['avg_cost_per_call'] or 0, 4),
                    'last_analysis_time': usage_row['last_analysis_time'],
                    'reasoning_calls': usage_row['reasoning_calls'],
                    'total_reasoning_tokens': usage_row['total_reasoning_tokens'],
                    'has_real_data': True
                }

                # Get breakdown by agent type
                cursor.execute('''
                    SELECT 
                        agent_type,
                        COUNT(*) as calls,
                        SUM(total_tokens) as tokens,
                        SUM(estimated_cost) as cost,
                        AVG(response_time) as avg_time
                    FROM api_usage_tracking 
                    WHERE project_name = ?
                    GROUP BY agent_type
                    ORDER BY cost DESC
                ''', (project_name,))

                agent_breakdown = []
                for agent_row in cursor.fetchall():
                    agent_breakdown.append({
                        'agent_type': agent_row['agent_type'],
                        'calls': agent_row['calls'],
                        'tokens': agent_row['tokens'],
                        'cost': round(agent_row['cost'] or 0, 4),
                        'avg_time': round(agent_row['avg_time'] or 0, 2)
                    })

                usage_data['agent_breakdown'] = agent_breakdown
        
        except Exception as e:
            print(f"ERROR: Failed to fetch usage data for {project_name}: {e}")
            usage_data = None
        
        # Prepare response
        result = format_project_data(project_row)
        result.update({
            'general_research': clean_and_structure_text(project_row['research_data']),
            'general_sources': json.loads(project_row['general_sources']) if project_row['general_sources'] else [],
            'question_analyses': question_analyses,
            'deep_research': deep_research_data,
            'catalog_data': catalog_data,  # Include cached catalog data
            'usage_data': usage_data  # Include real API usage and cost data
        })
        
        conn.close()
        return jsonify(result)
        
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500
    except json.JSONDecodeError as e:
        conn.close()
        return jsonify({'error': f'JSON parsing failed: {str(e)}'}), 500
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get project counts by score range
        cursor.execute('''
            SELECT 
                COUNT(*) as total_projects,
                AVG(total_score) as avg_score,
                COUNT(CASE WHEN total_score >= 4 THEN 1 END) as green_light,
                COUNT(CASE WHEN total_score >= 0 AND total_score < 4 THEN 1 END) as mid_tier,
                COUNT(CASE WHEN total_score < 0 THEN 1 END) as misaligned,
                MAX(updated_at) as last_updated
            FROM final_summaries
        ''')
        
        stats_row = cursor.fetchone()
        
        stats = {
            'total_projects': stats_row['total_projects'],
            'avg_score': round(stats_row['avg_score'] or 0, 1),
            'green_light': stats_row['green_light'],
            'mid_tier': stats_row['mid_tier'],
            'misaligned': stats_row['misaligned'],
            'last_updated': stats_row['last_updated']
        }
        
        conn.close()
        return jsonify(stats)
        
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': f'Database query failed: {str(e)}'}), 500
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/export')
def export_data():
    """Export all data as JSON"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get all data
        cursor.execute('''
            SELECT 
                fs.project_name, fs.slug, fs.total_score, fs.recommendation,
                fs.summary, fs.created_at, fs.updated_at,
                pr.research_data, pr.sources as general_sources
            FROM final_summaries fs
            LEFT JOIN project_research pr ON fs.project_name = pr.project_name
            ORDER BY fs.total_score DESC, fs.updated_at DESC
        ''')
        
        export_data = []
        for row in cursor.fetchall():
            project_name = row['project_name']
            
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
                    'question_id': q_row['question_id'],
                    'question_key': q_row['question_key'],
                    'analysis': q_row['analysis'],
                    'score': q_row['score'],
                    'confidence': q_row['confidence'],
                    'sources': json.loads(q_row['sources']) if q_row['sources'] else []
                })
            
            project_data = format_project_data(row)
            project_data.update({
                'general_research': row['research_data'],
                'general_sources': json.loads(row['general_sources']) if row['general_sources'] else [],
                'question_analyses': question_details
            })
            
            export_data.append(project_data)
        
        conn.close()
        
        # Create timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        response = jsonify({
            'exported_at': datetime.now().isoformat(),
            'total_projects': len(export_data),
            'data': export_data
        })
        
        response.headers['Content-Disposition'] = f'attachment; filename=near_partnership_export_{timestamp}.json'
        return response
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database unavailable'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM final_summaries')
        count = cursor.fetchone()['count']
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'projects_count': count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        conn.close()
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

def check_database():
    """Check if database exists and has data"""
    if not os.path.exists(DATABASE_PATH):
        print(f"⚠️  Database not found: {DATABASE_PATH}")
        print("   Run the multi-agent analysis script first to generate data.")
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM final_summaries')
        count = cursor.fetchone()['count']
        conn.close()
        
        if count == 0:
            print(f"⚠️  Database is empty. Run the analysis script to populate data.")
            return False
        
        print(f"✓ Database found with {count} projects analyzed")
        return True
        
    except sqlite3.Error as e:
        print(f"⚠️  Database error: {e}")
        conn.close()
        return False

def main():
    parser = argparse.ArgumentParser(description='NEAR Catalyst Framework Dashboard Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host address (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port number (default: 5000, auto-detects if occupied)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--check-db', action='store_true', help='Check database and exit')
    parser.add_argument('--force-port', action='store_true', help='Force the specified port without auto-detection')
    
    args = parser.parse_args()
    
    if args.check_db:
        check_database()
        return
    
    print("🚀 NEAR Catalyst Framework Dashboard")
    print("=" * 50)
    
    # Check database
    if not check_database():
        print("\n❌ Cannot start server without valid database.")
        print("   Run: python analyze_projects_multi_agent.py --limit 5")
        return
    
    # Check frontend files
    if not os.path.exists(FRONTEND_DIR):
        print(f"⚠️  Frontend directory not found: {FRONTEND_DIR}")
        print("   Make sure frontend files are in the correct location.")
        return
    
    # Smart port detection
    try:
        if args.force_port:
            # Force the specified port without checking
            actual_port = args.port
            print(f"🔧 Forcing port {actual_port} (--force-port specified)")
        else:
            # Try to find an available port
            if args.port == 5000:
                # Default port - try 8080 first, then random in 8000 range
                print(f"🔍 Checking port availability...")
                if is_port_available(args.host, 8080):
                    actual_port = 8080
                    print(f"✓ Using port {actual_port} (8080 available)")
                elif is_port_available(args.host, args.port):
                    actual_port = args.port
                    print(f"✓ Using port {actual_port} (original port available)")
                else:
                    actual_port = find_available_port(args.host, port_range=(8000, 8999))
                    print(f"🎲 Auto-selected port {actual_port} (original port occupied)")
            else:
                # Custom port specified - try it first, then fall back to 8000 range
                actual_port = find_available_port(args.host, preferred_port=args.port, port_range=(8000, 8999))
                if actual_port != args.port:
                    print(f"⚠️  Port {args.port} occupied, auto-selected port {actual_port}")
                else:
                    print(f"✓ Using requested port {actual_port}")
    
    except RuntimeError as e:
        print(f"\n❌ Port detection failed: {e}")
        print("   Try using --force-port to bypass auto-detection")
        return
    
    print(f"\n🌐 Server starting on http://{args.host}:{actual_port}")
    print(f"📊 Dashboard: http://{args.host}:{actual_port}")
    print(f"🔗 API endpoints:")
    print(f"   • GET /api/projects - List all projects")
    print(f"   • GET /api/project/<name> - Project details")
    print(f"   • GET /api/stats - Dashboard statistics")
    print(f"   • GET /api/export - Export all data")
    print(f"   • GET /api/health - Health check")
    print(f"\n💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(
            host=args.host,
            port=actual_port,
            debug=args.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == '__main__':
    main() 