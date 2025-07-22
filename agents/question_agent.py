# agents/question_agent.py
"""
Question Agent for NEAR Catalyst Framework

This agent evaluates specific diagnostic questions to assess hackathon catalyst potential,
focusing on discovering co-creation partners that unlock developer potential during hackathons.
"""

import json
import sqlite3
import hashlib
import time
from datetime import datetime

from config.config import TIMEOUTS, PARALLEL_CONFIG, format_benchmark_examples_for_prompt, get_framework_principles


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
    
    def _generate_cache_key(self, project_name, question_config):
        """
        Generate cache key for project-specific question analysis.
        
        Args:
            project_name (str): Name of the project
            question_config (dict): Question configuration with key
            
        Returns:
            str: MD5 hash for cache key
        """
        question_key = question_config.get('key', question_config.get('id', 'unknown'))
        return hashlib.md5(f"{project_name.lower()}_{question_key}".encode()).hexdigest()
    
    def analyze(self, project_name, general_research, question_config, db_path, benchmark_format='auto'):
        """
        Analyze a specific diagnostic question for a project.
        
        Args:
            project_name (str): Name of the project to analyze
            general_research (str): General research context from ResearchAgent or DeepResearchAgent
            question_config (dict): Question configuration from DIAGNOSTIC_QUESTIONS
            db_path (str): Path to SQLite database
            benchmark_format (str): Benchmark format preference ('auto', 'json', 'csv')
            
        Returns:
            dict: Analysis results with question research, scoring, and metadata
        """
        # Generate cache key for this specific analysis
        cache_key = self._generate_cache_key(project_name, question_config)
        
        # Check for existing analysis first
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM question_analyses WHERE cache_key = ?', (cache_key,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            # Return cached result
            return {
                "question_id": existing[2],
                "research_data": existing[4],
                "sources": json.loads(existing[5]) if existing[5] else [],
                "analysis": existing[6],
                "score": existing[7],
                "confidence": existing[8],
                "cached": True
            }
        
        try:
            conn.close()
            
            # Step 1: Research specific question
            print(f"    Q{question_config['id']}: Conducting research...")
            question_research = self._conduct_research(
                project_name, question_config["question"], question_config["description"], question_config["search_focus"]
            )
            
            # Step 2: Analyze the question with research
            print(f"    Q{question_config['id']}: Analyzing with GPT-4.1...")
            analysis_result = self._analyze_question(project_name, question_config, general_research, question_research, benchmark_format)
            
            # Step 3: Store results in database
            self._cache_results(project_name, question_config, question_research, analysis_result, cache_key, db_path)
            
            print(f"    Q{question_config['id']}: Score: {analysis_result['score']:+d} ({analysis_result['confidence']})")
            
            return {
                "question_id": question_config["id"],
                "research_data": question_research["content"],
                "sources": question_research["sources"],
                "analysis": analysis_result["analysis"],
                "score": analysis_result["score"],
                "confidence": analysis_result["confidence"],
                "cached": False
            }
            
        except Exception as e:
            print(f"    Q{question_config['id']}: ERROR - {str(e)}")
            return {
                "question_id": question_config["id"],
                "research_data": f"Research failed: {str(e)}",
                "sources": [],
                "analysis": f"Analysis failed: {str(e)}",
                "score": 0,
                "confidence": "Low",
                "error": str(e),
                "cached": False
            }
    
    def _conduct_research(self, project_name, question_text, description, search_focus):
        """Conduct question-specific research using web search."""
        research_prompt = f"""
For the project "{project_name}", research specifically for NEAR Catalyst Framework hackathon evaluation.

Focus ONLY on: {description}

Search specifically for: {search_focus}

Your goal is to gather targeted information about this project's potential as a hackathon catalyst that can:
- Unlock developer potential during time-constrained hackathons
- Create "1 + 1 = 3" value when combined with NEAR
- Provide hands-on support and mentorship during developer events
- Enable rapid prototyping and integration within hackathon timeframes

Consider NEAR's context:
- NEAR Protocol is a developer-friendly blockchain with focus on usability
- NEAR hackathons typically last 48-72 hours with rapid prototyping needs
- NEAR developers use JavaScript/TypeScript, Rust, and AssemblyScript
- NEAR ecosystem emphasizes developer experience and easy onboarding

Return comprehensive details that help evaluate: {question_text}
"""
        
        research_response = self.client.responses.create(
            model="gpt-4.1",  # Using GPT-4.1 as specified in memory
            tools=[{"type": "web_search_preview", "search_context_size": "high"}],
            input=research_prompt,
            timeout=self.timeout
        )
        
        # Extract research content and sources
        research_content = ""
        sources = []
        
        # Process the response output according to Responses API structure
        for item in research_response.output:
            if item.type == "message":
                # Look for output_text content according to OpenAI docs
                for content_item in item.content:
                    if content_item.type == "output_text":
                        research_content = content_item.text
                        # Extract sources/citations if available
                        if hasattr(content_item, 'annotations'):
                            for annotation in content_item.annotations:
                                if annotation.type == "url_citation":
                                    sources.append({
                                        "url": annotation.url,
                                        "title": getattr(annotation, 'title', 'No title'),
                                        "start_index": annotation.start_index,
                                        "end_index": annotation.end_index
                                    })
                        break
                break
        
        return {"content": research_content, "sources": sources}
    
    def _analyze_question(self, project_name, question_config, general_research, question_research, benchmark_format='auto'):
        """
        Analyze the specific question with all available context.
        
        Args:
            project_name (str): Name of the project
            question_config (dict): Question configuration
            general_research (str): General research context (may be deep research if available)
            question_research (dict): Question-specific research results
            benchmark_format (str): Benchmark format preference
            
        Returns:
            dict: Analysis result with score, confidence, and detailed analysis
        """
        # Get framework context with specified format
        benchmark_examples = format_benchmark_examples_for_prompt(benchmark_format)
        framework_principles = get_framework_principles(benchmark_format)
        
        # Truncate research to fit context limits
        truncated_general = general_research[:2000]
        truncated_question = question_research["content"][:3000]
        
        # Check if this is deep research data (longer and more comprehensive)
        research_type = "deep research" if len(general_research) > 5000 else "general research"
        
        analysis_prompt = f"""You are analyzing potential hackathon catalyst opportunities for NEAR Protocol.

Based on the following research about {project_name}, evaluate this specific question for hackathon co-creation potential:

**QUESTION {question_config['id']}: {question_config['question']}**
**Description:** {question_config['description']}

**Context from {research_type}:**
{truncated_general}

**Question-Specific Research:**
{truncated_question}

**Analysis Framework:**
Using the NEAR Catalyst Framework, determine if this project can act as a force multiplier for hackathon developers. Consider:

1. **Hackathon Readiness**: Can developers integrate this during a 48-72 hour hackathon?
2. **Value Amplification**: Does combining this with NEAR create exponential value (1+1=3)?
3. **Developer Support**: Will this partner actively support hackathon participants?
4. **Friction Assessment**: Does this add complexity or reduce it for developers?

{framework_principles}

{benchmark_examples}

**CRITICAL: Your response MUST follow this exact format:**

ANALYSIS: [Provide a detailed rationale specifically focused on hackathon catalyst potential, citing specific evidence from the research. Must be at least 2 sentences.]

SCORE: [Must be exactly one of: +1, 0, or -1]
- +1 = Strong hackathon catalyst potential
- 0 = Neutral or unclear potential  
- -1 = Poor fit for hackathons

CONFIDENCE: [Must be exactly one of: High, Medium, or Low]

Focus on hackathon-specific evidence: integration speed, developer support, time-to-value, and hands-on mentorship capabilities.
"""

        try:
            # Using gpt-4.1 for analysis as specified in memory requirements
            response = self.client.chat.completions.create(
                model="gpt-4.1",  # CRITICAL: Use GPT-4.1 as required
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=500,
                timeout=TIMEOUTS['question_agent']
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Parse the structured response with enhanced error handling
            parsed_result = self._parse_analysis_response(analysis_text, question_config['id'])
            
            # Validate that we got a proper analysis
            if not parsed_result["analysis"] or parsed_result["analysis"] == "":
                print(f"      WARNING Q{question_config['id']}: Empty analysis detected. Raw response: {analysis_text[:200]}...")
                # Try to extract any meaningful content
                parsed_result["analysis"] = analysis_text[:200] + "... [parsing failed]"
                parsed_result["confidence"] = "Low"
            
            return parsed_result
            
        except Exception as e:
            print(f"      ERROR Q{question_config['id']}: Analysis failed - {str(e)}")
            return {
                "analysis": f"Analysis failed: {str(e)}",
                "score": 0,
                "confidence": "Low"
            }
    
    def _parse_analysis_response(self, analysis_text, question_id):
        """
        Parses the structured analysis response from the AI with enhanced error handling.
        
        Args:
            analysis_text (str): The full analysis response from the AI
            question_id (int): Question ID for debugging
            
        Returns:
            dict: A dictionary containing 'analysis', 'score', and 'confidence'
        """
        analysis = ""
        score = 0
        confidence = "Medium"
        
        # Enhanced parsing with better error handling
        try:
            lines = analysis_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('ANALYSIS:'):
                    analysis = line.split('ANALYSIS:', 1)[1].strip()
                elif line.startswith('SCORE:'):
                    score_text = line.split('SCORE:', 1)[1].strip()
                    # More robust score parsing
                    if '+1' in score_text or 'Strong' in score_text or score_text.strip() == '1':
                        score = 1
                    elif '-1' in score_text or 'Weak' in score_text or 'Poor' in score_text:
                        score = -1
                    elif '0' in score_text or 'Neutral' in score_text or 'unclear' in score_text.lower():
                        score = 0
                    else:
                        print(f"      WARNING Q{question_id}: Could not parse score from: '{score_text}'")
                elif line.startswith('CONFIDENCE:'):
                    conf_text = line.split('CONFIDENCE:', 1)[1].strip()
                    if conf_text in ['High', 'Medium', 'Low']:
                        confidence = conf_text
                    else:
                        print(f"      WARNING Q{question_id}: Invalid confidence '{conf_text}', using Medium")
            
            # If analysis is still empty, try to extract from raw text
            if not analysis:
                # Look for content that might be analysis
                for line in lines:
                    if len(line.strip()) > 20 and not line.strip().startswith(('SCORE:', 'CONFIDENCE:')):
                        analysis = line.strip()
                        break
                
                if not analysis:
                    analysis = f"Could not parse analysis from response. Raw: {analysis_text[:100]}..."
                    print(f"      WARNING Q{question_id}: Failed to extract analysis from response")
            
        except Exception as e:
            print(f"      ERROR Q{question_id}: Parsing failed - {str(e)}")
            analysis = f"Parsing error: {str(e)}"
        
        result = {
            "analysis": analysis,
            "score": score,
            "confidence": confidence
        }
        
        # Debug logging for empty results
        if not analysis or analysis == "":
            print(f"      DEBUG Q{question_id}: Empty analysis result. Raw text: {analysis_text}")
        
        return result
    
    def _cache_results(self, project_name, question_config, question_research, analysis_result, cache_key, db_path):
        """Cache the analysis results with retry logic for concurrent access."""
        max_retries = PARALLEL_CONFIG['retry_attempts']
        
        # Debug logging before storing
        if not analysis_result.get("analysis") or analysis_result.get("analysis") == "":
            print(f"      WARNING Q{question_config['id']}: Storing empty analysis to database!")
            print(f"        Analysis: '{analysis_result.get('analysis')}'")
            print(f"        Score: {analysis_result.get('score')}")
            print(f"        Confidence: {analysis_result.get('confidence')}")
        
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('''INSERT OR REPLACE INTO question_analyses 
                                 (cache_key, project_name, question_id, question_key, research_data, sources, 
                                  analysis, score, confidence, created_at) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (cache_key, project_name, question_config["id"], question_config["key"], 
                               question_research["content"], json.dumps(question_research["sources"]), 
                               analysis_result["analysis"], analysis_result["score"], analysis_result["confidence"], 
                               datetime.now().isoformat()))
                conn.commit()
                conn.close()
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(PARALLEL_CONFIG['retry_backoff'] * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"    Database error on Q{question_config['id']}, attempt {attempt + 1}: {e}")
                    break 