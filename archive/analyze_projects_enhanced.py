import requests
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import sqlite3
import argparse
import time
from datetime import datetime, timedelta

def fetch_project_info_with_search(client, project_name, project_data):
    """
    Agent 1: Research agent that gathers comprehensive information about the project
    """
    # Extract basic info from API
    profile = project_data.get('profile', {})
    tagline = profile.get('tagline', 'No tagline available')
    tags = ', '.join(profile.get('tags', {}).values())
    phase = profile.get('phase', 'Unknown')
    
    # Create research prompt
    research_prompt = f"""
    Research the project "{project_name}" in detail. Here's what I know from the NEAR catalog:
    - Tagline: {tagline}
    - Tags: {tags}
    - Phase: {phase}
    
    Please find and provide:
    1. Official website and documentation
    2. Technical architecture and key features
    3. Current development status and recent updates
    4. Team background and funding
    5. Integration capabilities and APIs
    6. Community size and adoption metrics
    7. Partnerships and ecosystem connections
    """
    
    try:
        research_response = client.responses.create(
            model="gpt-4.1",  # Web search supported model
            tools=[{
                "type": "web_search_preview",
                "search_context_size": "high"
            }],
            input=research_prompt
        )
        
        # Extract the research content
        research_content = ""
        for item in research_response.output:
            if item.type == "message" and item.role == "assistant":
                research_content = item.content[0].text
                break
                
        return research_content
        
    except Exception as e:
        print(f"  WARNING: Web search failed, using basic info: {e}")
        return f"Basic info - {project_name}: {tagline}. Tags: {tags}. Phase: {phase}"

def analyze_partnership_potential(client, project_name, research_data, system_prompt):
    """
    Agent 2: Analysis agent that evaluates partnership potential using the research data
    """
    analysis_prompt = f"""
    Based on the following research about {project_name}, analyze the potential partnership with NEAR Protocol:

    RESEARCH DATA:
    {research_data}

    Please provide a comprehensive partnership analysis following the framework provided in the system prompt.
    """
    
    try:
        # Use chat completions for the analysis (doesn't need web search)
        analysis_response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt}
            ],
            timeout=60
        )
        
        return analysis_response.choices[0].message.content
        
    except Exception as e:
        print(f"  ERROR: Analysis failed: {e}")
        return f"Analysis failed for {project_name}: {str(e)}"

def main():
    # Parse arguments first
    parser = argparse.ArgumentParser(description='Analyze NEAR projects for partnerships with enhanced web search.')
    parser.add_argument('--limit', type=int, default=None, help='Number of projects to process (0 for no limit)')
    parser.add_argument('--research-only', action='store_true', help='Only gather research, skip analysis')
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

    # Load system prompt from prompt.md with error handling
    try:
        with open('prompt.md', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        print("ERROR: prompt.md file not found")
        return
    except Exception as e:
        print(f"ERROR: Could not read prompt.md: {e}")
        return

    # Initialize SQLite database with enhanced schema
    try:
        conn = sqlite3.connect('project_analyses_enhanced.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhanced_analyses (
                slug TEXT PRIMARY KEY,
                name TEXT,
                research_data TEXT,
                analysis TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        conn.commit()
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}")
        return

    # Step 1: Fetch all projects
    try:
        url = "https://api.nearcatalog.org/projects"
        api_response = requests.get(url, timeout=30)
        api_response.raise_for_status()
        projects = api_response.json()
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch projects from API: {e}")
        conn.close()
        return
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON response from API: {e}")
        conn.close()
        return

    project_slugs = list(projects.keys())
    if limit:
        project_slugs = project_slugs[:limit]
    
    print(f"Processing {len(project_slugs)} projects with enhanced research...")

    # Calculate 24 hours ago
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

    for i, slug in enumerate(project_slugs, 1):
        print(f"[{i}/{len(project_slugs)}] Processing {slug}...")
        
        # Check if analysis already exists and is recent
        cursor.execute('SELECT research_data, analysis, updated_at FROM enhanced_analyses WHERE slug = ?', (slug,))
        existing = cursor.fetchone()
        if existing and existing[2]:
            try:
                updated_at = datetime.fromisoformat(existing[2])
                if updated_at > twenty_four_hours_ago:
                    print(f"  Enhanced analysis exists and is recent (< 24h old). Skipping...")
                    continue
                else:
                    print(f"  Analysis exists but is old (> 24h). Re-analyzing...")
            except (ValueError, AttributeError):
                print(f"  Analysis exists but timestamp invalid. Re-analyzing...")

        # Step 2: Fetch project details
        try:
            detail_url = f"https://api.nearcatalog.org/project?pid={slug}"
            detail_response = requests.get(detail_url, timeout=30)
            detail_response.raise_for_status()
            detail = detail_response.json()
        except requests.RequestException as e:
            print(f"  ERROR: Failed to fetch project details: {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"  ERROR: Invalid JSON in project details: {e}")
            continue

        name = detail.get('profile', {}).get('name', slug)
        print(f"  Researching: {name}")

        # Step 3: Research phase (Agent 1)
        research_data = fetch_project_info_with_search(client, name, detail)
        print(f"  ✓ Research completed")
        
        if args.research_only:
            # Store only research data
            cursor.execute('''INSERT OR REPLACE INTO enhanced_analyses 
                             (slug, name, research_data, analysis, created_at, updated_at) 
                             VALUES (?, ?, ?, ?, ?, ?)''', 
                         (slug, name, research_data, "Research only - no analysis", 
                          datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            print(f"  ✓ Research data stored")
            continue

        # Step 4: Analysis phase (Agent 2)
        print(f"  Analyzing partnership potential...")
        analysis = analyze_partnership_potential(client, name, research_data, system_prompt)
        
        # Store in database
        cursor.execute('''INSERT OR REPLACE INTO enhanced_analyses 
                         (slug, name, research_data, analysis, created_at, updated_at) 
                         VALUES (?, ?, ?, ?, ?, ?)''', 
                     (slug, name, research_data, analysis, 
                      datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        print(f"  ✓ Enhanced analysis stored successfully")
        
        # Rate limiting to avoid hitting API limits
        time.sleep(2)  # Longer delay due to multiple API calls

    # Export enhanced data to JSON
    print("\nExporting enhanced data to JSON...")
    try:
        cursor.execute('''SELECT slug, name, research_data, analysis, created_at, updated_at 
                         FROM enhanced_analyses ORDER BY updated_at DESC''')
        all_analyses = cursor.fetchall()
        
        export_data = []
        for row in all_analyses:
            export_data.append({
                'slug': row[0],
                'name': row[1],
                'research_data': row[2],
                'analysis': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        
        export_filename = f"enhanced_project_analyses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Enhanced data exported to {export_filename}")
        print(f"  Total analyses: {len(export_data)}")
        
    except Exception as e:
        print(f"ERROR: Failed to export data: {e}")

    print(f"\nCompleted enhanced processing. Results stored in project_analyses_enhanced.db")
    conn.close()

if __name__ == "__main__":
    main() 