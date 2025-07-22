import requests
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import sqlite3
import argparse
import time
from datetime import datetime, timedelta
import concurrent.futures
import hashlib

# Define the 6 diagnostic questions from the framework
DIAGNOSTIC_QUESTIONS = [
    {
        "id": 1,
        "key": "gap_filler",
        "question": "Gap-Filler?",
        "description": "Does the partner fill a technology gap NEAR lacks?",
        "search_focus": "technical capabilities, infrastructure, services that NEAR doesn't provide natively"
    },
    {
        "id": 2,
        "key": "new_proof_points", 
        "question": "New Proof-Points?",
        "description": "Does it enable new use cases/demos?",
        "search_focus": "use cases, applications, demos, innovative implementations"
    },
    {
        "id": 3,
        "key": "clear_story",
        "question": "One-Sentence Story?",
        "description": "Is there a clear value proposition?",
        "search_focus": "value proposition, messaging, developer experience, integration benefits"
    },
    {
        "id": 4,
        "key": "developer_friendly",
        "question": "Developer-Friendly?",
        "description": "Easy integration and learning curve?",
        "search_focus": "documentation, APIs, SDKs, developer tools, integration guides, tutorials"
    },
    {
        "id": 5,
        "key": "aligned_incentives",
        "question": "Aligned Incentives?",
        "description": "Mutual benefit and non-competitive?",
        "search_focus": "business model, partnerships, competition analysis, ecosystem positioning"
    },
    {
        "id": 6,
        "key": "ecosystem_fit",
        "question": "Ecosystem Fit?",
        "description": "Does it match NEAR's target audience?",
        "search_focus": "target audience, developer community, use cases that overlap with NEAR ecosystem"
    }
]

def generate_cache_key(project_name, question_key):
    """Generate a unique cache key for project-specific question research"""
    return hashlib.md5(f"{project_name.lower()}_{question_key}".encode()).hexdigest()

def research_agent(client, project_name, project_data):
    """
    Agent 1: Research agent that gathers comprehensive information about the project
    """
    profile = project_data.get('profile', {})
    tagline = profile.get('tagline', 'No tagline available')
    tags = ', '.join(profile.get('tags', {}).values())
    phase = profile.get('phase', 'Unknown')
    
    research_prompt = f"""
    Research the project "{project_name}" comprehensively. Known info from NEAR catalog:
    - Tagline: {tagline}
    - Tags: {tags}
    - Phase: {phase}
    
    Please provide detailed information about:
    1. Official website, documentation, and repositories
    2. Technical architecture and core technology stack
    3. Current development status and recent updates
    4. Team background, advisors, and funding history
    5. Integration capabilities, APIs, and developer tools
    6. Community size, adoption metrics, and partnerships
    7. Business model and tokenomics (if applicable)
    8. Competitive landscape and positioning
    """
    
    try:
        research_response = client.responses.create(
            model="gpt-4.1",
            tools=[{
                "type": "web_search_preview",
                "search_context_size": "high"
            }],
            input=research_prompt
        )
        
        research_content = ""
        sources = []
        
        for item in research_response.output:
            if item.type == "message" and item.role == "assistant":
                research_content = item.content[0].text
                # Extract sources/citations if available
                if hasattr(item.content[0], 'annotations'):
                    for annotation in item.content[0].annotations:
                        if annotation.type == "url_citation":
                            sources.append({
                                "url": annotation.url,
                                "title": getattr(annotation, 'title', 'No title'),
                                "start_index": annotation.start_index,
                                "end_index": annotation.end_index
                            })
                break
                
        return {
            "content": research_content,
            "sources": sources,
            "success": True
        }
        
    except Exception as e:
        print(f"  WARNING: General research failed: {e}")
        return {
            "content": f"Basic info - {project_name}: {tagline}. Tags: {tags}. Phase: {phase}",
            "sources": [],
            "success": False,
            "error": str(e)
        }

def question_agent(client, project_name, general_research, question_config, db_path):
    """
    Agents 2-7: Question-specific agents that research and analyze one diagnostic question
    """
    question_id = question_config["id"]
    question_key = question_config["key"]
    question_text = question_config["question"]
    description = question_config["description"]
    search_focus = question_config["search_focus"]
    
    print(f"    Analyzing Q{question_id}: {question_text}")
    
    # Create a new database connection for this thread
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL;')
    cursor = conn.cursor()
    
    try:
        # Check cache first (project-specific)
        cache_key = generate_cache_key(project_name, question_key)
        cursor.execute('SELECT research_data, sources, analysis, score, confidence FROM question_analyses WHERE cache_key = ?', (cache_key,))
        cached = cursor.fetchone()

        if cached:
            print(f"    ✓ Using cached analysis for Q{question_id}")
            return {
                "question_id": question_id,
                "research_data": cached[0],
                "sources": json.loads(cached[1]) if cached[1] else [],
                "analysis": cached[2],
                "score": cached[3],
                "confidence": cached[4],
                "cached": True
            }
        
        # Conduct question-specific research
        research_prompt = f"""
        For the project "{project_name}", research specifically about: {description}
        
        Search Focus: {search_focus}
        
        Use web search to find relevant information about this project.
        Return comprehensive details about: {question_text}
        """
        
        research_response = client.responses.create(
            model="gpt-4.1",
            messages=[
                {"role": "user", "content": research_prompt}
            ],
            tools=[{"type": "web_search_preview", "search_context_size": "high"}],
            timeout=120
        )
        
        # Extract research content and sources
        research_content = research_response.output.content[0].text
        sources = []
        
        # Extract sources from annotations
        for annotation in research_response.output.content[0].annotations:
            if hasattr(annotation, 'url'):
                sources.append({
                    "url": annotation.url,
                    "title": getattr(annotation, 'title', ''),
                    "index": getattr(annotation, 'index', 0)
                })
        
        # Analyze the research for this specific question
        analysis_prompt = f"""
        Project: {project_name}
        
        General Research Context:
        {general_research[:2000]}  # Truncate to avoid token limits
        
        Question-Specific Research:
        {research_content}
        
        Based on this research, analyze: {question_text}
        
        Description: {description}
        
        Provide your analysis with:
        1. Clear rationale
        2. Specific evidence from the research
        3. A definitive score and confidence level
        
        Format your response EXACTLY as:
        ANALYSIS: [Your detailed analysis here]
        SCORE: [+1 (Strong Yes), 0 (Neutral/Unclear), or -1 (Strong No)]
        CONFIDENCE: [High/Medium/Low]
        """
        
        analysis_response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "user", "content": analysis_prompt}
            ],
            timeout=60
        )
        
        analysis_content = analysis_response.choices[0].message.content
        
        # Extract score and confidence
        score = 0
        confidence = "Medium"
        
        lines = analysis_content.split('\n')
        for line in lines:
            if line.startswith('SCORE:'):
                try:
                    score_text = line.split('SCORE:')[1].strip()
                    if '+1' in score_text or 'Strong' in score_text:
                        score = 1
                    elif '-1' in score_text or 'Weak' in score_text:
                        score = -1
                    else:
                        score = 0
                except:
                    pass
            elif line.startswith('CONFIDENCE:'):
                confidence = line.split('CONFIDENCE:')[1].strip()
        
        # Cache the results (project-specific) with retry logic for concurrent access
        max_retries = 3
        for attempt in range(max_retries):
            try:
                cursor.execute('''INSERT OR REPLACE INTO question_analyses 
                                 (cache_key, project_name, question_id, question_key, research_data, sources, 
                                  analysis, score, confidence, created_at) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (cache_key, project_name, question_id, question_key, research_content, 
                               json.dumps(sources), analysis_content, score, confidence, 
                               datetime.now().isoformat()))
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"    Database error on Q{question_id}, attempt {attempt + 1}: {e}")
                    break
        
        # Commit the transaction
        conn.commit()
        
        return {
            "question_id": question_id,
            "research_data": research_content,
            "sources": sources,
            "analysis": analysis_content,
            "score": score,
            "confidence": confidence,
            "cached": False
        }
    
    finally:
        # Always close the database connection
        conn.close()
        
    except Exception as e:
        print(f"    ERROR: Q{question_id} analysis failed: {e}")
        return {
            "question_id": question_id,
            "research_data": f"Research failed: {str(e)}",
            "sources": [],
            "analysis": f"Analysis failed for {project_name} Q{question_id}: {str(e)}",
            "score": 0,
            "confidence": "Low",
            "error": str(e),
            "cached": False
        }

def summary_agent(client, project_name, general_research, question_results, system_prompt):
    """
    Agent 8: Summary agent that synthesizes all question analyses into final recommendation
    """
    print(f"  Generating final summary...")
    
    # Prepare question results summary
    results_summary = []
    total_score = 0
    
    for result in question_results:
        q_config = next(q for q in DIAGNOSTIC_QUESTIONS if q["id"] == result["question_id"])
        results_summary.append(f"""
Q{result['question_id']}: {q_config['question']} - {q_config['description']}
Score: {result['score']} | Confidence: {result['confidence']}
Analysis: {result['analysis'][:500]}...
""")
        total_score += result["score"]
    
    summary_prompt = f"""
    Create a comprehensive partnership analysis summary for {project_name} and NEAR Protocol.
    
    PROJECT RESEARCH:
    {general_research[:2000]}
    
    QUESTION-BY-QUESTION ANALYSIS:
    {"".join(results_summary)}
    
    TOTAL SCORE: {total_score}/6
    
    Please provide:
    1. A structured table with all 6 questions, scores, and concise rationales
    2. The total score and recommendation based on these thresholds:
       - +4 to +6: "Green-light partnership. Strong candidate for strategic collaboration."
       - 0 to +3: "Solid mid-tier fit. Worth pursuing, but may require integration polish or focused support."
       - < 0: "Likely misaligned. Proceed with caution or decline, as it may create friction."
    3. Key strengths and potential concerns
    4. Specific next steps or recommendations
    
    Follow the format from the system prompt framework.
    """
    
    try:
        summary_response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": summary_prompt}
            ],
            timeout=90
        )
        
        return {
            "summary": summary_response.choices[0].message.content,
            "total_score": total_score,
            "success": True
        }
        
    except Exception as e:
        print(f"  ERROR: Summary generation failed: {e}")
        return {
            "summary": f"Summary generation failed for {project_name}: {str(e)}",
            "total_score": total_score,
            "success": False,
            "error": str(e)
        }

def initialize_database():
    """Initialize enhanced database schema with full traceability and concurrent access support"""
    # Enable WAL mode for better concurrent access
    conn = sqlite3.connect('project_analyses_multi_agent.db')
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.execute('PRAGMA cache_size=10000;')
    conn.execute('PRAGMA temp_store=memory;')
    
    cursor = conn.cursor()
    
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
    
    conn.commit()
    return conn, cursor

def main():
    parser = argparse.ArgumentParser(description='Multi-agent NEAR partnership analysis with full traceability.')
    parser.add_argument('--limit', type=int, default=None, help='Number of projects to process (0 for no limit)')
    parser.add_argument('--research-only', action='store_true', help='Only gather general research')
    parser.add_argument('--questions-only', action='store_true', help='Only analyze questions (skip summary)')
    parser.add_argument('--force-refresh', action='store_true', help='Ignore cache and refresh all data')
    args = parser.parse_args()

    if args.limit is None:
        print('Warning: No limit specified. Processing all projects.')
        limit = None
    elif args.limit == 0:
        limit = None
    else:
        limit = args.limit

    # Load environment variables
    load_dotenv()
    openai_key = os.getenv('openai_key')
    if not openai_key:
        print("ERROR: OpenAI key not found in .env file")
        return

    client = OpenAI(api_key=openai_key)

    # Load system prompt
    try:
        with open('prompt.md', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        print("ERROR: prompt.md file not found")
        return

    # Initialize database
    try:
        conn, cursor = initialize_database()
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}")
        return

    # Fetch projects
    try:
        url = "https://api.nearcatalog.org/projects"
        api_response = requests.get(url, timeout=30)
        api_response.raise_for_status()
        projects = api_response.json()
    except Exception as e:
        print(f"ERROR: Failed to fetch projects: {e}")
        conn.close()
        return

    project_slugs = list(projects.keys())
    if limit:
        project_slugs = project_slugs[:limit]
    
    print(f"Processing {len(project_slugs)} projects with multi-agent analysis...")

    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

    for i, slug in enumerate(project_slugs, 1):
        print(f"\n[{i}/{len(project_slugs)}] Processing {slug}...")
        
        # Fetch project details
        try:
            detail_url = f"https://api.nearcatalog.org/project?pid={slug}"
            detail_response = requests.get(detail_url, timeout=30)
            detail_response.raise_for_status()
            detail = detail_response.json()
        except Exception as e:
            print(f"  ERROR: Failed to fetch project details: {e}")
            continue

        name = detail.get('profile', {}).get('name', slug)
        print(f"  Project: {name}")

        # Check if we should skip (unless force refresh)
        if not args.force_refresh:
            cursor.execute('SELECT updated_at FROM final_summaries WHERE project_name = ?', (name,))
            existing = cursor.fetchone()
            if existing:
                try:
                    updated_at = datetime.fromisoformat(existing[0])
                    if updated_at > twenty_four_hours_ago:
                        print(f"  Analysis exists and is recent (< 24h old). Skipping...")
                        continue
                except:
                    pass

        # Step 1: General Research Agent
        print(f"  Running general research agent...")
        research_result = research_agent(client, name, detail)
        
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
            continue

        # Step 2: Question-Specific Agents (run in parallel)
        print(f"  Running 6 question-specific agents in parallel...")
        question_results = []
        start_time = time.time()
        
        # Use ThreadPoolExecutor for parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all question agents
            future_to_question = {
                executor.submit(question_agent, client, name, research_result["content"], question_config, 'project_analyses_multi_agent.db'): question_config
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
        
        if args.questions_only:
            print(f"  ✓ Question analyses completed and stored")
            continue

        # Step 3: Summary Agent
        summary_result = summary_agent(client, name, research_result["content"], question_results, system_prompt)
        
        # Determine recommendation
        total_score = summary_result["total_score"]
        if total_score >= 4:
            recommendation = "Green-light partnership. Strong candidate for strategic collaboration."
        elif total_score >= 0:
            recommendation = "Solid mid-tier fit. Worth pursuing, but may require integration polish or focused support."
        else:
            recommendation = "Likely misaligned. Proceed with caution or decline, as it may create friction."
        
        # Store final summary
        cursor.execute('''INSERT OR REPLACE INTO final_summaries 
                         (project_name, slug, summary, total_score, recommendation, success, error, created_at, updated_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name, slug, summary_result["summary"], total_score, recommendation,
                       summary_result["success"], summary_result.get("error"),
                       datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        
        print(f"  ✓ Complete analysis stored. Score: {total_score}/6")
        
        # Brief pause between projects to be respectful to APIs
        time.sleep(1)

    # Export comprehensive data
    print("\nExporting comprehensive analysis data...")
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
        with open(export_filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Comprehensive data exported to {export_filename}")
        print(f"  Total projects analyzed: {len(export_data)}")
        
        # Print summary statistics
        if export_data:
            scores = [item["total_score"] for item in export_data]
            print(f"  Score distribution: Min={min(scores)}, Max={max(scores)}, Avg={sum(scores)/len(scores):.1f}")
        
    except Exception as e:
        print(f"ERROR: Failed to export data: {e}")

    print(f"\nCompleted multi-agent processing. Results in project_analyses_multi_agent.db")
    conn.close()

if __name__ == "__main__":
    main() 