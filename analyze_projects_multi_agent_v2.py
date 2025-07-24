#!/usr/bin/env python3
"""
NEAR Catalyst Framework - Multi-Agent System (Modular Version)

Authors: AI Assistant & User
Date: December 2024

This is the main orchestrator for the NEAR Catalyst Framework - a system designed to
discover hackathon co-creation partners that unlock developer potential and create
exponential value through "1 + 1 = 3" collaborations.

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
- Configuration constants are in config/config.py
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
import litellm

# Set up LiteLLM cost tracking
class CostTracker:
    """Simple cost tracker using LiteLLM's built-in cost calculation"""
    
    def __init__(self):
        self.total_cost = 0.0
        self.call_count = 0
        self.model_usage = {}
        self.session_start = time.time()
    
    def track_completion(self, response):
        """Track a completion response"""
        if hasattr(response, '_hidden_params'):
            cost = response._hidden_params.get('response_cost', 0.0)
            model = response._hidden_params.get('litellm_model_name', 'unknown')
            
            self.total_cost += cost
            self.call_count += 1
            
            if model not in self.model_usage:
                self.model_usage[model] = {'calls': 0, 'cost': 0.0}
            
            self.model_usage[model]['calls'] += 1
            self.model_usage[model]['cost'] += cost
    
    def print_session_summary(self, project_name=None):
        """Print session cost summary"""
        session_time = time.time() - self.session_start
        
        if project_name:
            print(f"\n💰 Cost Summary for {project_name}:")
        else:
            print(f"\n💰 Session Cost Summary:")
        print(f"   Total Cost: ${self.total_cost:.4f}")
        print(f"   API Calls: {self.call_count}")
        print(f"   Session Time: {session_time:.1f}s")
        
        if self.model_usage:
            print("   Model Breakdown:")
            for model, stats in self.model_usage.items():
                print(f"     {model}: {stats['calls']} calls, ${stats['cost']:.4f}")

# Global cost tracker
cost_tracker = CostTracker()

# Import our modular components
from agents import (
    ResearchAgent, QuestionAgent, SummaryAgent, DeepResearchAgent,
    DIAGNOSTIC_QUESTIONS, NEAR_CATALOG_API, BATCH_PROCESSING_CONFIG, DEEP_RESEARCH_CONFIG
)
from database import DatabaseManager


def setup_environment():
    """Load environment variables and check OpenAI API key"""
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        sys.exit(1)
    
    # Set up LiteLLM for native cost tracking
    print(f"✅ Environment setup complete - using LiteLLM with built-in cost tracking")

    # Load system prompt framework
    try:
        with open('prompt.md', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        print("❌ Error: prompt.md file not found")
        print("This file contains the partnership evaluation framework.")
        sys.exit(1)
    
    return system_prompt


def fetch_full_project_details(project_slug):
    """
    Fetch comprehensive project details from NEAR Catalog API.
    This provides rich context for the research agent.
    
    Args:
        project_slug (str): Project slug/identifier
        
    Returns:
        dict: Full project details or basic fallback data
    """
    try:
        print(f"    📋 Fetching project details from NEAR catalog...")
        catalog_url = f"https://api.nearcatalog.org/project?pid={project_slug}"
        response = requests.get(catalog_url, timeout=30)
        
        if response.status_code == 200:
            catalog_data = response.json()
            print(f"    ✓ Retrieved comprehensive project data from NEAR catalog")
            return catalog_data
        else:
            print(f"    ⚠️ NEAR catalog returned {response.status_code}, using basic data")
            return None
            
    except Exception as e:
        print(f"    ⚠️ Could not fetch NEAR catalog data: {e}")
        return None


def create_enriched_project_context(project_name, project_basic_data, catalog_data=None):
    """
    Create enriched project context by combining basic NEAR list data with full catalog details.
    This gives the research agent much richer context to work with.
    
    Args:
        project_name (str): Project name
        project_basic_data (dict): Basic data from NEAR project list
        catalog_data (dict): Full catalog data from NEAR catalog API
        
    Returns:
        dict: Enriched project context for research agent
    """
    # Start with basic data
    enriched_context = {
        'project_name': project_name,
        'basic_profile': project_basic_data.get('profile', {}),
        'catalog_data': catalog_data
    }
    
    # Add rich context from catalog if available
    if catalog_data:
        enriched_context.update({
            'description': catalog_data.get('description', ''),
            'category': catalog_data.get('category', ''),
            'stage': catalog_data.get('stage', ''),
            'tech_stack': catalog_data.get('tech_stack', ''),
            'website': catalog_data.get('website', ''),
            'github': catalog_data.get('github', ''),
            'documentation': catalog_data.get('documentation', ''),
            'tags': catalog_data.get('tags', []),
            'team_size': catalog_data.get('team_size', ''),
            'founded': catalog_data.get('founded', ''),
            'location': catalog_data.get('location', ''),
            'blockchain_networks': catalog_data.get('blockchain_networks', ''),
            'twitter': catalog_data.get('twitter', ''),
            'discord': catalog_data.get('discord', ''),
            'telegram': catalog_data.get('telegram', '')
        })
        
        print(f"    📊 Research agent will have rich context:")
        if catalog_data.get('description'):
            print(f"      • Description: {catalog_data['description'][:100]}...")
        if catalog_data.get('category'):
            print(f"      • Category: {catalog_data['category']}")
        if catalog_data.get('tech_stack'):
            print(f"      • Tech Stack: {catalog_data['tech_stack']}")
        if catalog_data.get('github'):
            print(f"      • GitHub: {catalog_data['github']}")
    else:
        print(f"    ⚠️ Research agent will use basic data only")
    
    return enriched_context


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
        dict: Project details or None if failed
    """
    try:
        detail_url = f"https://api.nearcatalog.org/project?pid={slug}"
        detail_response = requests.get(detail_url, timeout=30)
        detail_response.raise_for_status()
        return detail_response.json()
    except Exception as e:
        print(f"      ERROR: Failed to fetch basic project details for {slug}: {e}")
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


def run_parallel_question_analysis(client, project_name, general_research, db_path, benchmark_format='auto'):
    """
    Execute all 6 question agents in parallel for maximum efficiency.
    
    Args:
        client (OpenAI): OpenAI client instance
        project_name (str): Name of the project
        general_research (str): General research context
        db_path (str): Path to SQLite database
        benchmark_format (str): Benchmark format preference
        
    Returns:
        list: Results from all question agents, sorted by question ID
    """
    print(f"  Running 6 question-specific agents in parallel...")
    question_results = []
    start_time = time.time()
    
    # Initialize question agent with usage tracking
    db_manager = DatabaseManager(db_path)
    question_agent = QuestionAgent(None, db_manager)
    
    # Use ThreadPoolExecutor for parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Submit all question agents
        future_to_question = {
            executor.submit(
                question_agent.analyze, 
                project_name, 
                general_research, 
                question_config, 
                db_path,
                benchmark_format
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
        
        # Initialize usage tracking for this project analysis
        # LiteLLM handles cost tracking internally
        
        # Step 1: General Research Agent
        print(f"  Running general research agent...")
        research_agent = ResearchAgent(None, db_manager)
        
        # Fetch full project details for research context
        catalog_data = fetch_full_project_details(slug)
        enriched_context = create_enriched_project_context(name, detail, catalog_data)
        
        # Store catalog data for frontend use (avoids duplicate API calls)
        if catalog_data:
            db_manager.store_catalog_data(name, slug, catalog_data)
        
        research_result = research_agent.analyze(name, enriched_context)
        
        # Track research cost if available
        if research_result.get("cost"):
            print(f"      💰 Research cost: ${research_result['cost']:.4f}")
        
        # Store general research
        cursor.execute('''INSERT OR REPLACE INTO project_research 
                         (project_name, slug, research_data, sources, success, error, created_at, updated_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name, slug, research_result["content"], json.dumps(research_result["sources"]),
                       research_result["success"], research_result.get("error"), 
                       datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        
        # Step 1.5: Deep Research Agent (optional)
        deep_research_result = None
        if args.deep_research and research_result["success"]:
            print(f"  🔬 Deep research requested...")
            deep_research_agent = DeepResearchAgent(None, db_manager)
            
            # Check if deep research is enabled via config OR command line flag (flag overrides config)
            config_enabled = deep_research_agent.is_enabled()
            flag_override = args.deep_research
            
            if not config_enabled and flag_override:
                print(f"  🚀 Deep research enabled via --deep-research flag (overriding config)")
                print(f"      Estimated cost: ${deep_research_agent.get_estimated_cost():.2f} per project")
                # Force enable for this execution by temporarily modifying the agent's config
                deep_research_agent.config['enabled'] = True
            elif not config_enabled:
                print(f"  ⚠️  Deep research is disabled in configuration")
                print(f"      To enable: Set DEEP_RESEARCH_CONFIG['enabled'] = True in config/config.py")
                print(f"      Or use --deep-research flag to override")
                print(f"      Estimated cost: ${deep_research_agent.get_estimated_cost():.2f} per project")
            
            # Execute deep research if enabled (via config or flag)
            if config_enabled or flag_override:
                # Show cost warning for first project in batch
                if hasattr(args, '_deep_research_cost_shown') is False:
                    print(f"  💰 Deep research enabled - Cost: ${deep_research_agent.get_estimated_cost():.2f} per project")
                    args._deep_research_cost_shown = True
                
                deep_research_result = deep_research_agent.analyze(name, research_result["content"])
                
                # Track deep research cost if available
                if deep_research_result.get("cost"):
                    print(f"      💰 Deep research cost: ${deep_research_result['cost']:.4f}")
                
                # Store deep research results
                db_manager.store_deep_research_data(name, slug, deep_research_result)
                
                if deep_research_result["success"]:
                    print(f"  ✓ Deep research completed ({deep_research_result.get('tool_calls_made', 0)} tool calls)")

        if args.research_only:
            print(f"  ✓ General research completed and stored")
            if args.deep_research and deep_research_result:
                print(f"  ✓ Deep research completed and stored")
            return True

        # Step 2: Question-Specific Agents (parallel execution)
        # Use deep research data if available and successful, otherwise use general research
        research_context = research_result["content"]
        if deep_research_result and deep_research_result.get("success"):
            research_context = deep_research_result["content"]
            print(f"  📊 Using deep research data for question analysis")
        
        question_results = run_parallel_question_analysis(
            client, name, research_context, db_manager.db_path, args.benchmark_format
        )
        
        # Track question analysis costs
        total_question_cost = sum(q.get('cost', 0.0) for q in question_results)
        if total_question_cost > 0:
            print(f"      💰 Total question analysis cost: ${total_question_cost:.4f}")
        
        if args.questions_only:
            print(f"  ✓ Question analyses completed and stored")
            return True

        # Step 3: Summary Agent
        summary_agent = SummaryAgent(None, db_manager)
        summary_result = summary_agent.analyze(
            name, research_context, question_results, system_prompt, args.benchmark_format
        )
        
        # Track summary cost if available
        if summary_result.get("cost"):
            print(f"      💰 Summary cost: ${summary_result['cost']:.4f}")
        
        # Store final summary
        cursor.execute('''INSERT OR REPLACE INTO final_summaries 
                         (project_name, slug, summary, total_score, recommendation, success, error, created_at, updated_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name, slug, summary_result["summary"], summary_result["total_score"], 
                       summary_result["recommendation"], summary_result["success"], 
                       summary_result.get("error"), datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        
        score_info = f"Score: {summary_result['total_score']}/6"
        if deep_research_result and deep_research_result.get("success"):
            score_info += " (with deep research)"
        print(f"  ✓ Complete analysis stored. {score_info}")
        
        # Print total cost summary for this project
        total_project_cost = (
            research_result.get("cost", 0.0) + 
            (deep_research_result.get("cost", 0.0) if deep_research_result else 0.0) +
            total_question_cost +
            summary_result.get("cost", 0.0)
        )
        
        if total_project_cost > 0:
            print(f"  💰 Total project cost: ${total_project_cost:.4f}")
        
        return True
        
    except Exception as e:
        print(f"  ERROR: Analysis failed for {name}: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def process_project_batch(batch_data, batch_num, total_batches):
    """
    Process a batch of projects concurrently.
    
    Args:
        batch_data (dict): Contains client, db_manager, project_slugs, system_prompt, args
        batch_num (int): Current batch number
        total_batches (int): Total number of batches
        
    Returns:
        tuple: (successful_count, total_count)
    """
    client = batch_data['client']
    db_manager = batch_data['db_manager']
    project_slugs = batch_data['project_slugs']
    system_prompt = batch_data['system_prompt']
    args = batch_data['args']
    
    # Track deep research override status for the completion summary
    if args.deep_research and not hasattr(args, '_deep_research_was_overridden'):
        deep_research_agent_temp = DeepResearchAgent(None)
        args._deep_research_was_overridden = not deep_research_agent_temp.is_enabled()
    
    print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(project_slugs)} projects)")
    
    successful_analyses = 0
    batch_start_time = time.time()
    
    def process_single_project_wrapper(slug_with_index):
        """Wrapper function for processing a single project with error handling."""
        slug, project_index = slug_with_index
        try:
            # Add small delay between projects to be respectful to APIs
            time.sleep(BATCH_PROCESSING_CONFIG['project_delay'] * project_index)
            
            print(f"  [{project_index + 1}/{len(project_slugs)}] Processing {slug}...")
            
            # Fetch project details
            detail = fetch_project_details(slug)
            if not detail:
                return False
            
            # Analyze the project
            project_data = {'slug': slug, 'detail': detail}
            return analyze_single_project(client, db_manager, project_data, system_prompt, args)
            
        except Exception as e:
            print(f"  ERROR: Failed to process {slug}: {e}")
            return False
    
    # Use ThreadPoolExecutor for concurrent processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(project_slugs)) as executor:
        # Submit all projects in the batch
        future_to_slug = {
            executor.submit(process_single_project_wrapper, (slug, i)): slug
            for i, slug in enumerate(project_slugs)
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_slug):
            slug = future_to_slug[future]
            try:
                if future.result(timeout=300):  # 5 minute timeout per project
                    successful_analyses += 1
            except concurrent.futures.TimeoutError:
                print(f"  ⚠️ Timeout processing {slug}")
            except Exception as e:
                print(f"  ❌ Error processing {slug}: {e}")
    
    batch_elapsed = time.time() - batch_start_time
    print(f"  ✅ Batch {batch_num} completed in {batch_elapsed:.1f}s ({successful_analyses}/{len(project_slugs)} successful)")
    
    return successful_analyses, len(project_slugs)


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
    4. Orchestrates multi-agent analysis for each project (with batch processing)
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
  python analyze_projects_multi_agent_v2.py --force-refresh --threads 3
  python analyze_projects_multi_agent_v2.py --threads 8 --limit 50
  python analyze_projects_multi_agent_v2.py --deep-research --limit 3
  python analyze_projects_multi_agent_v2.py --deep-research --research-only --limit 1
  
Deep Research:
  Deep research uses OpenAI's o4-mini-deep-research model for comprehensive analysis.
  Cost: ~$2 per project. Can be enabled via flag (overrides config) or config file.
  
Database management:
  python analyze_projects_multi_agent_v2.py --list
  python analyze_projects_multi_agent_v2.py --clear all
  python analyze_projects_multi_agent_v2.py --clear project1 project2 project3
        """
    )
    parser.add_argument('--limit', type=int, default=None, 
                       help='Number of projects to process (0 for no limit)')
    parser.add_argument('--threads', type=int, default=BATCH_PROCESSING_CONFIG['default_batch_size'],
                       help=f'Number of projects to process concurrently (default: {BATCH_PROCESSING_CONFIG["default_batch_size"]})')
    parser.add_argument('--benchmark-format', choices=['auto', 'json', 'csv'], default='auto',
                       help='Benchmark data format preference: auto (detect), json, or csv (default: auto)')
    parser.add_argument('--research-only', action='store_true', 
                       help='Only gather general research')
    parser.add_argument('--questions-only', action='store_true', 
                       help='Only analyze questions (skip summary)')
    parser.add_argument('--force-refresh', action='store_true', 
                       help='Ignore cache and refresh all data')
    parser.add_argument('--deep-research', action='store_true', 
                       help='Enable deep research (overrides config setting if disabled)')
    parser.add_argument('--clear', nargs='*', metavar='PROJECT', 
                       help='Clear specific project(s) from database or "all" to clear everything')
    parser.add_argument('--list', action='store_true', 
                       help='List all projects in the database')
    args = parser.parse_args()

    # Initialize database manager first for database operations
    db_path = os.getenv('DATABASE_PATH', 'project_analyses_multi_agent.db')
    db_manager = DatabaseManager(db_path)
    
    # Handle database listing
    if args.list:
        print("🗃️ Projects in database:")
        print("=" * 60)
        projects = db_manager.list_projects()
        if not projects:
            print("No projects found in database.")
        else:
            print(f"{'Name':<30} {'Slug':<20} {'Score':<6} {'Deep':<5} {'Updated'}")
            print("-" * 60)
            for project in projects:
                score = f"{project['score']}/6" if project['score'] is not None else "N/A"
                deep_research = "✓" if project.get('deep_research_performed') else " "
                updated = project['updated_at'][:16] if project['updated_at'] else "N/A"
                print(f"{project['name'][:29]:<30} {project['slug'][:19]:<20} {score:<6} {deep_research:<5} {updated}")
            print(f"\nTotal: {len(projects)} projects")
            print("Deep: ✓ indicates deep research was performed")
        return
    
    # Handle database clearing
    if args.clear is not None:
        print("🗑️ Database clearing operation")
        print("=" * 60)
        
        # If no arguments provided with --clear, treat as 'all'
        if len(args.clear) == 0:
            identifiers = 'all'
        elif len(args.clear) == 1 and args.clear[0].lower() == 'all':
            identifiers = 'all'
        else:
            identifiers = args.clear
        
        # Confirmation for clearing all
        if identifiers == 'all':
            print("⚠️  WARNING: This will clear ALL projects from the database!")
            projects = db_manager.list_projects()
            if projects:
                print(f"About to delete {len(projects)} projects:")
                for project in projects[:5]:  # Show first 5
                    print(f"  - {project['name']}")
                if len(projects) > 5:
                    print(f"  ... and {len(projects) - 5} more projects")
                
                confirm = input("\nAre you sure? Type 'yes' to confirm: ")
                if confirm.lower() != 'yes':
                    print("Operation cancelled.")
                    return
            else:
                print("Database is already empty.")
                return
        
        # Perform the clearing operation
        try:
            result = db_manager.clear_projects(identifiers)
            print(f"✅ {result['message']}")
            
            if 'cleared_records' in result:
                print("Cleared records:")
                for table, count in result['cleared_records'].items():
                    print(f"  - {table}: {count} records")
            
            if 'not_found' in result:
                print(f"⚠️  Projects not found: {', '.join(result['not_found'])}")
                
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
        
        return

    # Validate arguments for normal processing
    if args.limit is None:
        print('Warning: No limit specified. Processing all projects.')
        limit = None
    elif args.limit == 0:
        limit = None
    else:
        limit = args.limit

    # Validate threads parameter
    if args.threads > BATCH_PROCESSING_CONFIG['max_batch_size']:
        print(f"Warning: Threads ({args.threads}) exceeds max batch size ({BATCH_PROCESSING_CONFIG['max_batch_size']})")
        print(f"Setting threads to {BATCH_PROCESSING_CONFIG['max_batch_size']} to prevent API rate limiting")
        args.threads = BATCH_PROCESSING_CONFIG['max_batch_size']
    elif args.threads < 1:
        print("Error: Threads must be at least 1")
        sys.exit(1)

    print("🚀 NEAR Catalyst Framework - Multi-Agent System v2")
    print("=" * 60)
    print(f"Batch processing: {args.threads} projects concurrently")
    print(f"Benchmark format: {args.benchmark_format}")
    
    # Show deep research status
    if args.deep_research:
        deep_research_agent = DeepResearchAgent(None)  # Just for config checking
        config_enabled = deep_research_agent.is_enabled()
        if config_enabled:
            print(f"🔬 Deep research: ENABLED in config (${deep_research_agent.get_estimated_cost():.2f} per project)")
        else:
            print(f"🚀 Deep research: ENABLED via --deep-research flag (${deep_research_agent.get_estimated_cost():.2f} per project)")
            print(f"    Config setting: DISABLED (flag overrides config)")
    else:
        print(f"📊 Deep research: DISABLED (use --deep-research to enable)")
    
    # Setup environment
    system_prompt = setup_environment()
    
    # Fetch projects to analyze
    project_slugs = fetch_near_projects(limit)
    
    print(f"\nProcessing {len(project_slugs)} projects with multi-agent analysis...")
    
    # Process projects in batches
    successful_analyses = 0
    total_processed = 0
    
    # Split projects into batches
    batch_size = args.threads
    batches = [project_slugs[i:i + batch_size] for i in range(0, len(project_slugs), batch_size)]
    total_batches = len(batches)
    
    print(f"Split into {total_batches} batches of {batch_size} projects each")
    
    batch_data = {
        'client': None, # LiteLLM handles API calls directly, so no client object needed here
        'db_manager': db_manager,
        'system_prompt': system_prompt,
        'args': args
    }
    
    for batch_num, batch_slugs in enumerate(batches, 1):
        batch_data['project_slugs'] = batch_slugs
        
        batch_successful, batch_total = process_project_batch(batch_data, batch_num, total_batches)
        successful_analyses += batch_successful
        total_processed += batch_total
        
        # Add delay between batches to be respectful to APIs
        if batch_num < total_batches:
            print(f"  Waiting {BATCH_PROCESSING_CONFIG['inter_batch_delay']}s before next batch...")
            time.sleep(BATCH_PROCESSING_CONFIG['inter_batch_delay'])

    # Export comprehensive results
    export_results(db_manager)

    print(f"\n✅ Completed multi-agent processing!")
    print(f"   Successfully analyzed: {successful_analyses}/{total_processed} projects")
    print(f"   Batch processing: {args.threads} concurrent projects")
    print(f"   Benchmark format: {args.benchmark_format}")
    
    # Show deep research summary if enabled
    if args.deep_research:
        deep_research_agent = DeepResearchAgent(None)
        config_enabled = deep_research_agent.is_enabled()
        estimated_total_cost = successful_analyses * deep_research_agent.get_estimated_cost()
        
        # Use tracked override status if available, otherwise check config
        was_overridden = getattr(args, '_deep_research_was_overridden', False)
        
        if config_enabled and not was_overridden:
            print(f"   Deep research: ENABLED in config (est. total cost: ${estimated_total_cost:.2f})")
        else:
            print(f"   Deep research: ENABLED via flag override (est. total cost: ${estimated_total_cost:.2f})")
    
    # Print final session cost summary
    print(f"\n💰 Session Summary:")
    print(f"   Projects analyzed: {successful_analyses}")
    print(f"   Cost tracking: Native LiteLLM cost calculation")
    print(f"   Note: Individual costs shown per project above")
    
    print(f"   Database: {db_manager.db_path}")
    print(f"   Frontend: Run 'python server.py' to view dashboard")
    print("=" * 60)


if __name__ == "__main__":
    main() 