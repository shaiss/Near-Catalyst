# agents/question_agent.py
"""
Question Agent for NEAR Partnership Analysis

Agents 2-7: Specialized agents that research and analyze specific diagnostic questions.
Each agent focuses on one of the 6 partnership criteria with targeted web search.
"""

import sqlite3
import json
import time
import hashlib
from datetime import datetime
from .config import TIMEOUTS, PARALLEL_CONFIG, format_benchmark_examples_for_prompt, get_framework_principles


class QuestionAgent:
    """
    Agents 2-7: Question-specific agents that research and analyze one diagnostic question
    each, using project-specific caching to prevent data poisoning.
    """
    
    def __init__(self, client):
        """Initialize the question agent with OpenAI client."""
        self.client = client
        self.timeout = TIMEOUTS['question_agent']
        self.analysis_timeout = TIMEOUTS['analysis_agent']
    
    def generate_cache_key(self, project_name, question_key):
        """Generate a unique cache key for project-specific question research."""
        return hashlib.md5(f"{project_name.lower()}_{question_key}".encode()).hexdigest()
    
    def analyze(self, project_name, general_research, question_config, db_path):
        """
        Analyze a specific diagnostic question for a project.
        
        Args:
            project_name (str): Name of the project
            general_research (str): General research context
            question_config (dict): Question configuration from DIAGNOSTIC_QUESTIONS
            db_path (str): Path to SQLite database
            
        Returns:
            dict: Analysis results with score, confidence, sources, etc.
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
            cache_key = self.generate_cache_key(project_name, question_key)
            cursor.execute(
                'SELECT research_data, sources, analysis, score, confidence FROM question_analyses WHERE cache_key = ?', 
                (cache_key,)
            )
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
            research_content, sources = self._conduct_research(
                project_name, question_text, description, search_focus
            )
            
            # Analyze the research for this specific question
            analysis_content, score, confidence = self._analyze_research(
                project_name, general_research, research_content, question_text, description
            )
            
            # Cache the results with retry logic for concurrent access
            self._cache_results(
                cursor, cache_key, project_name, question_id, question_key,
                research_content, sources, analysis_content, score, confidence
            )
            
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
        
        finally:
            # Always close the database connection
            conn.close()
    
    def _conduct_research(self, project_name, question_text, description, search_focus):
        """Conduct question-specific research using web search."""
        research_prompt = f"""
        For the project "{project_name}", research specifically for NEAR Protocol hackathon partnership evaluation.
        
        Focus Question: {description}
        Search Focus: {search_focus}
        
        Research this project's potential as a NEAR Protocol hackathon partner, specifically addressing: {question_text}
        
        Consider NEAR's context:
        - NEAR Protocol is a developer-friendly blockchain with focus on usability
        - NEAR hackathons typically last 48-72 hours with rapid prototyping needs
        - NEAR developers use JavaScript/TypeScript, Rust, and AssemblyScript
        - NEAR ecosystem emphasizes developer experience and easy onboarding
        
        Return comprehensive details that help evaluate: {question_text}
        """
        
        research_response = self.client.responses.create(
            model="gpt-4.1",
            tools=[{"type": "web_search_preview", "search_context_size": "high"}],
            input=research_prompt,
            timeout=self.timeout
        )
        
        # Extract research content and sources
        research_content = ""
        sources = []
        
        # Process the response output according to Responses API structure
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
        
        return research_content, sources
    
    def _analyze_research(self, project_name, general_research, research_content, question_text, description):
        """Analyze the research data for the specific question."""
        
        # Load framework benchmarks and principles
        benchmark_examples = format_benchmark_examples_for_prompt()
        framework_principles = get_framework_principles()
        
        analysis_prompt = f"""
        Project: {project_name}
        NEAR Protocol Partnership Framework Evaluation
        
        General Research Context:
        {general_research[:2000]}  # Truncate to avoid token limits
        
        Question-Specific Research:
        {research_content}
        
        Evaluate this project using the "1+1=3" Partnership Framework for: {question_text}
        
        Evaluation Context: {description}
        
        {benchmark_examples}
        
        {framework_principles}
        
        Specific Evaluation Criteria for {question_text}:
        - Does this create exponential value (1+1=3) when combined with NEAR?
        - Is this complementary to NEAR's core blockchain functionality or competitive?
        - How does this compare to the framework benchmark examples?
        - What specific evidence supports the score?
        
        Consider NEAR's Position:
        - Developer-friendly blockchain with chain abstraction focus
        - JavaScript/TypeScript/Rust developer ecosystem
        - 48-72 hour hackathon rapid prototyping requirements
        - Target audience: Web3 builders and traditional developers entering blockchain
        
        Provide your analysis with:
        1. Clear rationale using framework language ("strategic gap," "Better Together," etc.)
        2. Comparison to framework benchmark examples (referenced above)
        3. Specific evidence of complementary vs competitive positioning
        4. Hackathon integration feasibility assessment
        
        Format your response EXACTLY as:
        ANALYSIS: [Your detailed framework-aligned analysis here, referencing benchmarks]
        SCORE: [+1 (Strong Yes), 0 (Neutral/Unclear), or -1 (Strong No)]
        CONFIDENCE: [High/Medium/Low]
        """
        
        analysis_response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "user", "content": analysis_prompt}
            ],
            timeout=self.analysis_timeout
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
        
        return analysis_content, score, confidence
    
    def _cache_results(self, cursor, cache_key, project_name, question_id, question_key,
                      research_content, sources, analysis_content, score, confidence):
        """Cache the analysis results with retry logic for concurrent access."""
        max_retries = PARALLEL_CONFIG['retry_attempts']
        
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
                    time.sleep(PARALLEL_CONFIG['retry_backoff'] * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"    Database error on Q{question_id}, attempt {attempt + 1}: {e}")
                    break 