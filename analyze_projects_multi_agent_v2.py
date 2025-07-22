#!/usr/bin/env python3
"""
NEAR Partnership Analysis - Multi-Agent System (Modular Version)

Entry Point: analyze_projects_multi_agent_v2.py

This is the main orchestrator for the NEAR Protocol partnership analysis system.
It coordinates multiple specialized AI agents to evaluate potential technical partners
using a comprehensive framework that creates "1 + 1 = 3" value propositions.

SYSTEM ARCHITECTURE:
===================

File Structure Overview:
------------------------
- analyze_projects_multi_agent_v2.py (THIS FILE) - Main orchestrator and CLI
- agents/                            - AI agent modules
  ├── __init__.py                   - Agent package exports
  ├── config.py                     - Configuration constants
  ├── research_agent.py             - Agent 1: General project research
  ├── question_agent.py             - Agents 2-7: Question-specific analysis
  └── summary_agent.py              - Agent 8: Final synthesis
- database/                         - Database management
  ├── __init__.py                   - Database package exports
  └── database_manager.py           - SQLite operations and exports
- frontend/                         - Web dashboard (Glass UI)
  ├── index.html                    - Dashboard structure
  ├── styles.css                    - Glassmorphism styling
  └── app.js                        - Frontend logic
- server.py                         - Flask backend API
- prompt.md                         - LLM system prompt framework
- .env                             - Environment variables (OpenAI key)

Multi-Agent Workflow:
--------------------
1. ResearchAgent: Gathers comprehensive project information via web search
2. QuestionAgent (x6): Parallel analysis of 6 diagnostic questions:
   - Q1: Gap-Filler? (Does it fill a technology gap NEAR lacks?)
   - Q2: New Proof-Points? (Does it enable new use cases/demos?)
   - Q3: One-Sentence Story? (Is there a clear value proposition?)
   - Q4: Developer-Friendly? (Easy integration and learning curve?)
   - Q5: Aligned Incentives? (Mutual benefit and non-competitive?)
   - Q6: Ecosystem Fit? (Does it match NEAR's target audience?)
3. SummaryAgent: Synthesizes all results into final recommendation

Key Features:
-------------
- Parallel execution of question agents (4-6x speed improvement)
- Project-specific caching to prevent data poisoning
- SQLite WAL mode for concurrent database access
- Comprehensive export with full traceability
- 24-hour data freshness checks
- Web dashboard for visualization

CLI Usage:
----------
python analyze_projects_multi_agent_v2.py [OPTIONS]

Options:
  --limit N             Process only N projects (0 for unlimited)
  --research-only       Only run general research agent
  --questions-only      Only run question agents (skip summary)
  --force-refresh       Ignore cache and refresh all data

Output:
-------
- SQLite database: project_analyses_multi_agent.db
- JSON export: multi_agent_analyses_YYYYMMDD_HHMMSS.json
- Web dashboard: http://localhost:5000 (run server.py)

For Future LLMs:
---------------
- The system uses OpenAI's gpt-4.1 model with web search capabilities
- All agents are stateless and can run independently
- Database schema is in database/database_manager.py
- Configuration constants are in agents/config.py
- Frontend communicates with Flask API in server.py
"""

import requests
import json
import os
import sys
import argparse
import time
import concurrent.futures
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# Import our modular components
from agents import (
    ResearchAgent, QuestionAgent, SummaryAgent,
    DIAGNOSTIC_QUESTIONS, NEAR_CATALOG_API
)
from database import DatabaseManager


def setup_environment():
    """
    Initialize environment and validate dependencies.
    
    Returns:
        OpenAI: Configured OpenAI client
        str: System prompt content
    """
    # Load environment variables from .env file
    load_dotenv()
    openai_key = os.getenv('openai_key')
    if not openai_key:
        print("ERROR: OpenAI key not found in .env file")
        print("Please create a .env file with: openai_key=your_api_key_here")
        sys.exit(1)

    # Initialize OpenAI client
    client = OpenAI(api_key=openai_key)

    # Load system prompt framework
    try:
        with open('prompt.md', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        print("ERROR: prompt.md file not found")
        print("This file contains the partnership evaluation framework.")
        sys.exit(1)
    
    return client, system_prompt


def fetch_near_projects(limit=None):
    """
    Fetch project list from NEAR Catalog API.
    
    Args:
        limit (int, optional): Maximum number of projects to fetch
        
    Returns:
        list: List of project slugs to process
    """
    try:
        print("Fetching project list from NEAR Catalog...")
        api_response = requests.get(
            NEAR_CATALOG_API['projects'], 
            timeout=NEAR_CATALOG_API['timeout']
        )
        api_response.raise_for_status()
        projects = api_response.json()
        
        project_slugs = list(projects.keys())
        if limit:
            project_slugs = project_slugs[:limit]
        
        print(f"Found {len(project_slugs)} projects to analyze")
        return project_slugs
        
    except Exception as e:
        print(f"ERROR: Failed to fetch projects from NEAR Catalog: {e}")
        sys.exit(1)


def fetch_project_details(slug):
    """
    Fetch detailed information for a specific project.
    
    Args:
        slug (str): Project slug identifier
        
    Returns:
        dict: Project details from NEAR Catalog
    """
    try:
        detail_url = NEAR_CATALOG_API['project_detail'].format(slug=slug)
        detail_response = requests.get(detail_url, timeout=NEAR_CATALOG_API['timeout'])
        detail_response.raise_for_status()
        return detail_response.json()
        
    except Exception as e:
        print(f"  ERROR: Failed to fetch project details for {slug}: {e}")
        return None


def should_skip_project(db_manager, project_name, force_refresh):
    """
    Check if project analysis should be skipped based on freshness.
    
    Args:
        db_manager (DatabaseManager): Database manager instance
        project_name (str): Name of the project
        force_refresh (bool): Whether to ignore cache
        
    Returns:
        bool: True if should skip, False if should analyze
    """
    if force_refresh:
        return False
    
    conn = None
    try:
        conn = db_manager.initialize_database()[0]
        cursor = conn.cursor()
        
        cursor.execute('SELECT updated_at FROM final_summaries WHERE project_name = ?', (project_name,))
        existing = cursor.fetchone()
        
        if existing:
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
            try:
                updated_at = datetime.fromisoformat(existing[0])
                if updated_at > twenty_four_hours_ago:
                    return True
            except:
                pass
        
        return False
        
    except Exception:
        return False
    finally:
        if conn:
            conn.close()


def run_parallel_question_analysis(client, project_name, general_research, db_path):
    """
    Execute all 6 question agents in parallel for maximum efficiency.
    
    Args:
        client (OpenAI): OpenAI client instance
        project_name (str): Name of the project
        general_research (str): General research context
        db_path (str): Path to SQLite database
        
    Returns:
        list: Results from all question agents, sorted by question ID
    """
    print(f"  Running 6 question-specific agents in parallel...")
    question_results = []
    start_time = time.time()
    
    # Initialize question agent
    question_agent = QuestionAgent(client)
    
    # Use ThreadPoolExecutor for parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Submit all question agents
        future_to_question = {
            executor.submit(
                question_agent.analyze, 
                project_name, 
                general_research, 
                question_config, 
                db_path
            ): question_config
            for question_config in DIAGNOSTIC_QUESTIONS
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_question):
            question_config = future_to_question[future]
            try:
                result = future.result(timeout=180)  # 3 minute timeout per question
                question_results.append(result)
                
                # Print progress
                status = "✓ Cached" if result.get('cached') else "✓ Analyzed"
                print(f"    Q{question_config['id']}: {question_config['question']} - {status}")
                
            except concurrent.futures.TimeoutError:
                print(f"    Q{question_config['id']}: {question_config['question']} - ⚠️ Timeout")
                # Add a failed result
                question_results.append({
                    "question_id": question_config["id"],
                    "research_data": "Analysis timed out",
                    "sources": [],
                    "analysis": f"Analysis timed out for Q{question_config['id']}",
                    "score": 0,
                    "confidence": "Low",
                    "error": "Timeout",
                    "cached": False
                })
            except Exception as e:
                print(f"    Q{question_config['id']}: {question_config['question']} - ❌ Error: {str(e)}")
                # Add a failed result
                question_results.append({
                    "question_id": question_config["id"],
                    "research_data": f"Analysis failed: {str(e)}",
                    "sources": [],
                    "analysis": f"Analysis failed for Q{question_config['id']}: {str(e)}",
                    "score": 0,
                    "confidence": "Low",
                    "error": str(e),
                    "cached": False
                })
    
    # Sort results by question_id to maintain order
    question_results.sort(key=lambda x: x.get('question_id', 0))
    
    elapsed_time = time.time() - start_time
    print(f"  ✓ All question agents completed in {elapsed_time:.1f} seconds")
    
    return question_results


def analyze_single_project(client, db_manager, project_data, system_prompt, args):
    """
    Analyze a single project using the multi-agent system.
    
    Args:
        client (OpenAI): OpenAI client instance
        db_manager (DatabaseManager): Database manager
        project_data (dict): Project information from NEAR Catalog
        system_prompt (str): System prompt for LLM
        args: Command line arguments
        
    Returns:
        bool: True if analysis completed successfully
    """
    slug = project_data['slug']
    detail = project_data['detail']
    
    # Extract project name
    name = detail.get('profile', {}).get('name', slug)
    print(f"  Project: {name}")

    # Check if we should skip this project
    if should_skip_project(db_manager, name, args.force_refresh):
        print(f"  Analysis exists and is recent (< 24h old). Skipping...")
        return True

    try:
        # Initialize database connection
        conn, cursor = db_manager.initialize_database()
        
        # Step 1: General Research Agent
        print(f"  Running general research agent...")
        research_agent = ResearchAgent(client)
        research_result = research_agent.analyze(name, detail)
        
        # Store general research
        cursor.execute('''INSERT OR REPLACE INTO project_research 
                         (project_name, slug, research_data, sources, success, error, created_at, updated_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name, slug, research_result["content"], json.dumps(research_result["sources"]),
                       research_result["success"], research_result.get("error"), 
                       datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        
        if args.research_only:
            print(f"  ✓ General research completed and stored")
            return True

        # Step 2: Question-Specific Agents (parallel execution)
        question_results = run_parallel_question_analysis(
            client, name, research_result["content"], db_manager.db_path
        )
        
        if args.questions_only:
            print(f"  ✓ Question analyses completed and stored")
            return True

        # Step 3: Summary Agent
        summary_agent = SummaryAgent(client)
        summary_result = summary_agent.analyze(
            name, research_result["content"], question_results, system_prompt
        )
        
        # Store final summary
        cursor.execute('''INSERT OR REPLACE INTO final_summaries 
                         (project_name, slug, summary, total_score, recommendation, success, error, created_at, updated_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name, slug, summary_result["summary"], summary_result["total_score"], 
                       summary_result["recommendation"], summary_result["success"], 
                       summary_result.get("error"), datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        
        print(f"  ✓ Complete analysis stored. Score: {summary_result['total_score']}/6")
        
        return True
        
    except Exception as e:
        print(f"  ERROR: Analysis failed for {name}: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def export_results(db_manager):
    """
    Export comprehensive analysis results to JSON file.
    
    Args:
        db_manager (DatabaseManager): Database manager instance
    """
    print("\nExporting comprehensive analysis data...")
    try:
        export_data, export_filename = db_manager.export_comprehensive_data()
        db_manager.save_export_data(export_data, export_filename)
        
        print(f"✓ Comprehensive data exported to {export_filename}")
        
        # Print summary statistics
        stats = db_manager.get_analysis_statistics(export_data)
        if stats:
            print(f"  Total projects analyzed: {stats['total_projects']}")
            print(f"  Score distribution: Min={stats['min_score']}, Max={stats['max_score']}, Avg={stats['avg_score']:.1f}")
        
    except Exception as e:
        print(f"ERROR: Failed to export data: {e}")


def main():
    """
    Main orchestrator function that coordinates the entire multi-agent analysis pipeline.
    
    This function:
    1. Parses command line arguments
    2. Sets up environment and dependencies
    3. Fetches projects from NEAR Catalog
    4. Orchestrates multi-agent analysis for each project
    5. Exports comprehensive results
    
    The system is designed to be resumable and handles caching automatically.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Multi-agent NEAR partnership analysis with full traceability.',
        epilog="""
Examples:
  python analyze_projects_multi_agent_v2.py --limit 5
  python analyze_projects_multi_agent_v2.py --research-only --limit 10
  python analyze_projects_multi_agent_v2.py --force-refresh
        """
    )
    parser.add_argument('--limit', type=int, default=None, 
                       help='Number of projects to process (0 for no limit)')
    parser.add_argument('--research-only', action='store_true', 
                       help='Only gather general research')
    parser.add_argument('--questions-only', action='store_true', 
                       help='Only analyze questions (skip summary)')
    parser.add_argument('--force-refresh', action='store_true', 
                       help='Ignore cache and refresh all data')
    args = parser.parse_args()

    # Validate arguments
    if args.limit is None:
        print('Warning: No limit specified. Processing all projects.')
        limit = None
    elif args.limit == 0:
        limit = None
    else:
        limit = args.limit

    print("🚀 NEAR Partnership Analysis - Multi-Agent System v2")
    print("=" * 60)
    
    # Setup environment
    client, system_prompt = setup_environment()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Fetch projects to analyze
    project_slugs = fetch_near_projects(limit)
    
    print(f"\nProcessing {len(project_slugs)} projects with multi-agent analysis...")
    
    # Process each project
    successful_analyses = 0
    for i, slug in enumerate(project_slugs, 1):
        print(f"\n[{i}/{len(project_slugs)}] Processing {slug}...")
        
        # Fetch project details
        detail = fetch_project_details(slug)
        if not detail:
            continue
        
        # Analyze the project
        project_data = {'slug': slug, 'detail': detail}
        if analyze_single_project(client, db_manager, project_data, system_prompt, args):
            successful_analyses += 1
        
        # Brief pause between projects to be respectful to APIs
        time.sleep(1)

    # Export comprehensive results
    export_results(db_manager)

    print(f"\n✅ Completed multi-agent processing!")
    print(f"   Successfully analyzed: {successful_analyses}/{len(project_slugs)} projects")
    print(f"   Database: {db_manager.db_path}")
    print(f"   Frontend: Run 'python server.py' to view dashboard")
    print("=" * 60)


if __name__ == "__main__":
    main() 