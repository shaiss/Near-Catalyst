import requests
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import sqlite3
import argparse
import time
from datetime import datetime, timedelta

def main():
    # Parse arguments first
    parser = argparse.ArgumentParser(description='Analyze NEAR projects for partnerships.')
    parser.add_argument('--limit', type=int, default=None, help='Number of projects to process (0 for no limit)')
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

    # Initialize SQLite database
    try:
        conn = sqlite3.connect('project_analyses.db')
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                slug TEXT PRIMARY KEY,
                name TEXT,
                analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if created_at column exists and add it if missing (migration)
        cursor.execute("PRAGMA table_info(analyses)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'created_at' not in columns:
            print("Migrating database: Adding created_at column...")
            cursor.execute('ALTER TABLE analyses ADD COLUMN created_at TIMESTAMP')
            # Update existing records with current timestamp
            cursor.execute('UPDATE analyses SET created_at = ? WHERE created_at IS NULL', (datetime.now().isoformat(),))
            print("✓ Database migration completed")
        
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
    
    print(f"Processing {len(project_slugs)} projects...")

    # Calculate 24 hours ago
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

    for i, slug in enumerate(project_slugs, 1):
        print(f"[{i}/{len(project_slugs)}] Processing {slug}...")
        
        # Check if analysis already exists and is recent (less than 24 hours old)
        cursor.execute('SELECT analysis, created_at FROM analyses WHERE slug = ?', (slug,))
        existing = cursor.fetchone()
        if existing:
            created_at_str = existing[1]
            try:
                # Parse the timestamp (SQLite format)
                created_at = datetime.fromisoformat(created_at_str.replace(' ', 'T'))
                if created_at > twenty_four_hours_ago:
                    print(f"  Analysis exists and is recent (< 24h old). Skipping...")
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
        print(f"  Analyzing: {name}")

        # Step 3: Make LLM call
        user_message = f"Analyze a potential partnership between NEAR and {name}."

        try:
            llm_response = client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",  # Using a more reliable model gpt-4.1-nano-2025-04-14 do not change this model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                timeout=60
            )
            analysis = llm_response.choices[0].message.content
            
            # Store in database
            cursor.execute('INSERT OR REPLACE INTO analyses (slug, name, analysis, created_at) VALUES (?, ?, ?, ?)', 
                         (slug, name, analysis, datetime.now().isoformat()))
            conn.commit()
            print(f"  ✓ Analysis stored successfully")
            
            # Rate limiting to avoid hitting API limits
            time.sleep(1)
            
        except Exception as e:
            print(f"  ERROR: LLM analysis failed for {name}: {e}")
            continue

    # Export data to JSON
    print("\nExporting data to JSON...")
    try:
        cursor.execute('SELECT slug, name, analysis, created_at FROM analyses ORDER BY created_at DESC')
        all_analyses = cursor.fetchall()
        
        export_data = []
        for row in all_analyses:
            export_data.append({
                'slug': row[0],
                'name': row[1],
                'analysis': row[2],
                'created_at': row[3]
            })
        
        export_filename = f"project_analyses_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Data exported to {export_filename}")
        print(f"  Total analyses: {len(export_data)}")
        
    except Exception as e:
        print(f"ERROR: Failed to export data: {e}")

    print(f"\nCompleted processing. Results stored in project_analyses.db")
    conn.close()

if __name__ == "__main__":
    main() 