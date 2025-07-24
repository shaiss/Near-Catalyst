# agents/question_agent.py
"""
Question Agent for NEAR Catalyst Framework

This agent evaluates specific diagnostic questions to assess hackathon catalyst potential,
focusing on discovering co-creation partners that unlock developer potential during hackathons.

ENHANCED WITH REASONING MODELS:
- Uses o3 (production) or o4-mini (development) for complex multi-source analysis
- Unified completion API via LiteLLM Router with automatic local model routing and fallbacks
- Intelligent context optimization and token usage tracking
- Fallback to GPT-4.1 if reasoning models are unavailable
"""

import json
import sqlite3
import hashlib
import time
import os
from datetime import datetime

from config.config import TIMEOUTS, PARALLEL_CONFIG, QUESTION_AGENT_CONFIG, format_benchmark_examples_for_prompt, get_framework_principles
from agents.litellm_router import completion


class QuestionAgent:
    """
    Agents 2-7: Question-specific agents that research and analyze one diagnostic question
    each, using project-specific caching to prevent data poisoning and LiteLLM Router for
    automatic local model routing with fallbacks.
    """
    
    def __init__(self, client=None, db_manager=None, usage_tracker=None):
        """Initialize the question agent."""
        self.timeout = TIMEOUTS['question_agent']
        self.analysis_timeout = TIMEOUTS['analysis_agent']
        self.config = QUESTION_AGENT_CONFIG
        self.environment = self._detect_environment()
        self.db_manager = db_manager
        
        print(f"🧠 Question Agent initialized with {self._get_research_model()} → {self._get_reasoning_model()} ({self.environment} mode)")
    
    def _detect_environment(self):
        """Detect if we're in development or production environment."""
        # Check for explicit environment override
        env_override = os.getenv('REASONING_ENV')
        if env_override in ['development', 'production']:
            return env_override
            
        # Check for common development indicators
        if (os.getenv('FLASK_ENV') == 'development' or 
            os.getenv('DEBUG') == 'True' or
            os.getenv('NODE_ENV') == 'development' or
            'dev' in os.getcwd().lower() or
            'test' in os.getcwd().lower()):
            return 'development'
        return 'production'
    
    def _get_research_model(self):
        """Get the appropriate research model for web search based on environment."""
        return self.config['research_model'][self.environment]
    
    def _get_reasoning_model(self):
        """Get the appropriate reasoning model for analysis based on environment."""
        return self.config['reasoning_model'][self.environment]
        
    def analyze_question(self, question_id, question_data, project_name, general_research, 
                        deep_research=None, system_prompt=None, benchmark_format='auto'):
        """
        Analyze a specific diagnostic question with two-step workflow: research then analysis.
        
        Uses project-specific caching to prevent data contamination between different projects.
        
        Args:
            question_id: ID of the diagnostic question (1-6)
            question_data: Question configuration from DIAGNOSTIC_QUESTIONS
            project_name: Name of the project being analyzed (for cache isolation)
            general_research: General research context from Agent 1
            deep_research: Deep research data if available (from Agent 1.5)
            system_prompt: Framework system prompt
            benchmark_format: Format preference for benchmark data
            
        Returns:
            Dict with analysis, score, confidence, and cost information
        """
        
        # Get question details
        question_text = question_data['question']
        description = question_data['description']
        search_focus = question_data.get('search_focus', '')
        
        print(f"    Q{question_id}: {question_text}")
        
        try:
            # Step 1: Research phase - gather information specific to this question
            research_result = self._conduct_question_research(
                question_id, question_text, description, search_focus, 
                project_name, general_research, deep_research
            )
            
            if not research_result['success']:
                return research_result
            
            # Step 2: Analysis phase - analyze gathered information with reasoning model
            analysis_result = self._conduct_question_analysis(
                question_id, question_text, description, project_name,
                general_research, research_result['content'], benchmark_format
            )
            
            # Combine costs from both phases
            total_cost = research_result.get('cost', 0.0) + analysis_result.get('cost', 0.0)
            
            # Update analysis result with combined cost
            analysis_result['cost'] = total_cost
            
            if analysis_result['success']:
                print(f"    Q{question_id}: Score: {analysis_result.get('score', 0):+d} ({analysis_result.get('confidence', 'Unknown')}) - Cost: ${total_cost:.4f}")
                print(f"    Q{question_id}: {question_text} - ✓ Analyzed")
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"Question {question_id} analysis failed: {str(e)}"
            print(f"    ❌ {error_msg}")
            
            return {
                "question_id": question_id,
                "question": question_text,
                "analysis": f"Analysis failed: {error_msg}",
                "score": 0,
                "confidence": "Error",
                "success": False,
                "error": error_msg,
                "cost": 0.0
            }

    def _conduct_question_research(self, question_id, question_text, description, search_focus, 
                                 project_name, general_research, deep_research):
        """
        Step 1: Research phase using web search model to gather question-specific information.
        """
        
        # Create project-specific cache key to prevent data contamination
        cache_key = self._create_cache_key(f"research_q{question_id}", project_name, question_text)
        
        # Check cache first
        cached_result = self._check_cache(cache_key, "question_research")
        if cached_result:
            print(f"    Q{question_id}: Using cached research")
            return cached_result
        
        # Build research context
        research_context = self._build_research_context(general_research, deep_research)
        
        # Create research prompt
        research_prompt = f"""You are researching specific aspects of a potential hackathon partner for NEAR Protocol.

QUESTION FOCUS: {question_text}
DESCRIPTION: {description}
SEARCH TARGETS: {search_focus}

EXISTING CONTEXT:
{research_context[:2000]}

RESEARCH MISSION:
Conduct targeted research to answer: "{question_text}"

Focus your search on:
- {search_focus}
- Specific evidence that would help answer this question
- Technical details, documentation, or examples relevant to this question
- Community feedback or developer experiences related to this aspect

Provide comprehensive information that will enable detailed analysis of this specific question.
"""

        try:
            print(f"    Q{question_id}: Conducting research with {self._get_research_model()}...")
            print(f"      🧠 Using {self._get_research_model()} for research")
            
            # Use LiteLLM Router for research phase
            response = completion(
                model=self._get_research_model(),
                messages=[{"role": "user", "content": research_prompt}],
                max_tokens=self.config['research_model']['max_output_tokens'],
                timeout=self.config['workflow']['research_timeout']
            )
            
            research_content = response.choices[0].message.content
            cost = 0.0
            
            # Extract cost and routing information
            if hasattr(response, '_hidden_params'):
                cost = response._hidden_params.get('response_cost', 0.0)
                
            result = {
                "success": True,
                "content": research_content,
                "cost": cost
            }
            
            # Cache the result
            self._store_cache(cache_key, "question_research", result)
            
            return result
            
        except Exception as e:
            error_msg = f"Research failed for Q{question_id}: {str(e)}"
            print(f"    ❌ {error_msg}")
            
            return {
                "success": False,
                "content": "",
                "error": error_msg,
                "cost": 0.0
            }

    def _conduct_question_analysis(self, question_id, question_text, description, project_name,
                                 general_research, question_research, benchmark_format):
        """
        Step 2: Analysis phase using reasoning model for deep question analysis.
        """
        
        # Create project-specific cache key
        cache_key = self._create_cache_key(f"analysis_q{question_id}", project_name, question_text)
        
        # Check cache first
        cached_result = self._check_cache(cache_key, "question_analysis")
        if cached_result:
            print(f"    Q{question_id}: Using cached analysis")
            return cached_result
        
        # Build comprehensive context for analysis
        analysis_context = self._build_analysis_context(general_research, question_research)
        
        # Get framework benchmarks and principles
        benchmark_examples = format_benchmark_examples_for_prompt(benchmark_format)
        framework_principles = get_framework_principles(benchmark_format)
        
        # Create analysis prompt
        analysis_prompt = f"""You are a NEAR Protocol Partnership Scout analyzing hackathon catalyst potential.

DIAGNOSTIC QUESTION: {question_text}
DESCRIPTION: {description}

COMPREHENSIVE CONTEXT:
{analysis_context[:4000]}

{framework_principles}

{benchmark_examples}

ANALYSIS REQUIREMENTS:

1. **Evaluate the Evidence**: Based on all available information, analyze how well this project addresses: "{question_text}"

2. **Apply Scoring Framework**: Use the +1/0/-1 scoring system:
   - +1: Strong positive evidence, clear benefit to NEAR developers
   - 0: Neutral or mixed evidence, unclear benefit
   - -1: Negative evidence, potential friction or competition

3. **Assess Confidence**: Rate your confidence in this assessment:
   - High: Strong evidence and clear reasoning
   - Medium: Good evidence but some uncertainty
   - Low: Limited evidence or high uncertainty

4. **Provide Structured Output**:

ANALYSIS: [Detailed analysis of evidence and reasoning, 2-3 paragraphs]

SCORE: [+1, 0, or -1]

CONFIDENCE: [High, Medium, or Low]

Focus on hackathon catalyst potential and developer experience. Be specific about evidence and reasoning."""

        try:
            print(f"    Q{question_id}: Analyzing with {self._get_reasoning_model()}...")
            print(f"      🧠 Using {self._get_reasoning_model()} for analysis")
            
            # Use LiteLLM Router for analysis phase
            response = completion(
                model=self._get_reasoning_model(),
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=self.config['reasoning_model']['max_output_tokens'],
                timeout=self.config['workflow']['analysis_timeout']
            )
            
            analysis_content = response.choices[0].message.content
            cost = 0.0
            
            # Extract cost and routing information
            if hasattr(response, '_hidden_params'):
                cost = response._hidden_params.get('response_cost', 0.0)
                local_used = response._hidden_params.get('local_model_used', False)
                router_tags = response._hidden_params.get('router_tags', [])
                
                if local_used:
                    print(f"      🆓 Using local model ({', '.join(router_tags)}) - Cost: Free")
                else:
                    print(f"      💰 Using OpenAI model ({', '.join(router_tags)}) - Cost: ${cost:.4f}")
            
            # Parse structured output
            parsed_result = self._parse_analysis_output(analysis_content)
            
            result = {
                "question_id": question_id,
                "question": question_text,
                "analysis": parsed_result['analysis'],
                "score": parsed_result['score'],
                "confidence": parsed_result['confidence'],
                "success": True,
                "cost": cost
            }
            
            # Cache the result
            self._store_cache(cache_key, "question_analysis", result)
            
            return result
            
        except Exception as e:
            error_msg = f"Analysis failed for Q{question_id}: {str(e)}"
            print(f"    ❌ {error_msg}")
            
            return {
                "question_id": question_id,
                "question": question_text,
                "analysis": f"Analysis failed: {error_msg}",
                "score": 0,
                "confidence": "Error",
                "success": False,
                "error": error_msg,
                "cost": 0.0
            }

    def _build_research_context(self, general_research, deep_research):
        """Build context for research phase."""
        context_parts = []
        
        # Add general research (most important)
        if general_research:
            context_parts.append(f"GENERAL RESEARCH:\n{general_research}")
        
        # Add deep research if available (high value context)
        if deep_research:
            context_parts.append(f"DEEP RESEARCH:\n{deep_research}")
        
        context = "\n\n".join(context_parts)
        
        # Optimize context length for research phase
        max_context = self.config['context_optimization']['max_research_context']
        if len(context) > max_context:
            context = context[:max_context] + "\n... [context truncated for research optimization]"
        
        return context

    def _build_analysis_context(self, general_research, question_research):
        """Build context for analysis phase."""
        context_parts = []
        
        # Add question-specific research (most relevant)
        if question_research:
            context_parts.append(f"QUESTION-SPECIFIC RESEARCH:\n{question_research}")
        
        # Add general research for broader context
        if general_research:
            context_parts.append(f"GENERAL CONTEXT:\n{general_research}")
        
        context = "\n\n".join(context_parts)
        
        # Optimize context length for analysis phase
        max_context = self.config['context_optimization']['max_analysis_context']
        if len(context) > max_context:
            context = context[:max_context] + "\n... [context truncated for analysis optimization]"
        
        return context

    def _create_cache_key(self, operation, project_name, question_text):
        """Create project-specific cache key to prevent data contamination."""
        # Include project name and question text to ensure isolation
        cache_input = f"{operation}:{project_name}:{question_text}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def _check_cache(self, cache_key, table_name):
        """Check if cached result exists for this project-specific operation."""
        if not self.db_manager:
            return None
            
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Check if cache table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                return None
            
            # Look for cached result
            cursor.execute(f"SELECT result_data FROM {table_name} WHERE cache_key = ? AND created_at > datetime('now', '-24 hours')", (cache_key,))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0])
            
            return None
            
        except Exception:
            return None

    def _store_cache(self, cache_key, table_name, result_data):
        """Store result in project-specific cache."""
        if not self.db_manager:
            return
            
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Create cache table if it doesn't exist
            cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table_name} (
                cache_key TEXT PRIMARY KEY,
                result_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Store result
            cursor.execute(f"INSERT OR REPLACE INTO {table_name} (cache_key, result_data) VALUES (?, ?)",
                          (cache_key, json.dumps(result_data)))
            conn.commit()
            
        except Exception as e:
            print(f"    ⚠️ Cache storage failed: {e}")

    def _parse_analysis_output(self, analysis_content):
        """Parse structured analysis output from reasoning model."""
        
        # Default values
        analysis = analysis_content
        score = 0
        confidence = "Medium"
        
        try:
            # Split content into sections
            lines = analysis_content.split('\n')
            
            analysis_lines = []
            
            for line in lines:
                line = line.strip()
                
                if line.upper().startswith('SCORE:'):
                    # Extract score
                    score_text = line.replace('SCORE:', '').strip()
                    if '+1' in score_text or 'SCORE: 1' in score_text:
                        score = 1
                    elif '-1' in score_text or 'SCORE: -1' in score_text:
                        score = -1
                    else:
                        score = 0
                        
                elif line.upper().startswith('CONFIDENCE:'):
                    # Extract confidence
                    confidence_text = line.replace('CONFIDENCE:', '').strip()
                    if 'HIGH' in confidence_text.upper():
                        confidence = "High"
                    elif 'LOW' in confidence_text.upper():
                        confidence = "Low"
                    else:
                        confidence = "Medium"
                        
                elif not line.upper().startswith(('SCORE:', 'CONFIDENCE:')):
                    # Part of analysis content
                    if line and not line.upper().startswith('ANALYSIS:'):
                        analysis_lines.append(line)
            
            # Rebuild analysis without the structured fields
            if analysis_lines:
                analysis = '\n'.join(analysis_lines).strip()
            
        except Exception as e:
            print(f"    ⚠️ Failed to parse analysis output: {e}")
            # Use raw content as fallback
            analysis = analysis_content
        
        return {
            'analysis': analysis,
            'score': score,
            'confidence': confidence
        } 