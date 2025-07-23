# agents/summary_agent.py
"""
Summary Agent for NEAR Catalyst Framework

This agent synthesizes all analysis results into final hackathon catalyst recommendations,
determining which partners can unlock developer potential and create exponential value.
"""

import json
import litellm
from config.config import DIAGNOSTIC_QUESTIONS, TIMEOUTS, SCORE_THRESHOLDS, RECOMMENDATIONS, load_partnership_benchmarks
from database.usage_tracker import APIUsageTracker
from database.database_manager import DatabaseManager
from typing import List, Dict


class SummaryAgent:
    """
    Agent 8: Summary agent that synthesizes all question analyses into final recommendation
    with cost tracking via LiteLLM.
    """
    
    def __init__(self, client=None, db_manager=None, usage_tracker=None):
        """Initialize the summary agent with usage tracking."""
        self.timeout = TIMEOUTS['summary_agent']
        
        # Initialize usage tracking
        self.db_manager = db_manager or DatabaseManager()
        self.usage_tracker = usage_tracker or APIUsageTracker(None, self.db_manager)
    
    def analyze(self, project_name: str, general_research: str, question_analyses: List[Dict], system_prompt: str, benchmark_format: str = 'auto') -> Dict:
        """
        Analyze and synthesize all results into final recommendation.
        
        This method provides a consistent interface with other agents.
        
        Args:
            project_name: Name of the project being evaluated
            general_research: Research findings from research agent (may be deep research if available)
            question_analyses: List of question analysis results
            system_prompt: System prompt (not used in this agent but kept for consistency)
            benchmark_format: Format preference for benchmark data
            
        Returns:
            Dictionary containing final catalyst assessment and recommendation
        """
        return self.generate_final_summary(project_name, general_research, question_analyses, benchmark_format)
    
    def generate_final_summary(self, project_name: str, general_research: str, question_analyses: List[Dict], benchmark_format: str = 'auto') -> Dict:
        """
        Synthesize all analysis results into a final hackathon catalyst recommendation.
        
        Args:
            project_name: Name of the project being evaluated
            general_research: General research data or deep research if available
            question_analyses: List of individual question analysis results
            benchmark_format: Format preference for benchmark examples
            
        Returns:
            Dictionary containing synthesis results with scoring and recommendation
        """
        # Set context for usage tracking
        self.usage_tracker.set_context(project_name, "summary_agent")
        
        try:
            # Load benchmarks in the specified format
            benchmarks = load_partnership_benchmarks(benchmark_format)
            
            # Calculate total score from question analyses
            total_score = sum(q.get('score', 0) for q in question_analyses)
            
            # Determine recommendation based on scoring framework
            recommendation = self._determine_recommendation(total_score)
            
            # Create synthesis prompt
            synthesis_prompt = self._create_synthesis_prompt(
                project_name, general_research, question_analyses, 
                total_score, recommendation, benchmarks
            )
            
            # Get LLM synthesis using GPT-4.1 with usage tracking
            print(f"  📊 Generating final summary with GPT-4.1...")
            response = self.usage_tracker.track_chat_completions_create(
                model="gpt-4.1",
                operation_type="synthesis",
                messages=[
                    {"role": "system", "content": "You are a NEAR Partnership Analysis expert synthesizing hackathon catalyst evaluations."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                max_tokens=800,
                timeout=TIMEOUTS['summary_agent']
            )
            
            summary_text = response.choices[0].message.content.strip()
            
            # Validate summary quality
            if len(summary_text) < 50:
                print(f"  ⚠️  WARNING: Generated summary is very short ({len(summary_text)} chars)")
            
            print(f"  ✅ Final summary generated: {total_score}/6 score, {recommendation}")
            
            return {
                "project_name": project_name,
                "total_score": total_score,
                "recommendation": recommendation,
                "summary": summary_text,
                "question_scores": {f"Q{q.get('question_id', i+1)}": q.get('score', 0) for i, q in enumerate(question_analyses)},
                "success": True
            }
            
        except Exception as e:
            print(f"      ❌ Summary generation failed: {str(e)}")
            
            # Calculate fallback score from available data
            fallback_score = sum(q.get('score', 0) for q in question_analyses)
            fallback_recommendation = self._determine_recommendation(fallback_score)
            
            return {
                "project_name": project_name,
                "total_score": fallback_score,
                "recommendation": fallback_recommendation,
                "summary": f"Summary generation failed: {str(e)}. Score based on individual analyses: {fallback_score}/6",
                "question_scores": {f"Q{q.get('question_id', i+1)}": q.get('score', 0) for i, q in enumerate(question_analyses)},
                "success": False,
                "error": str(e)
            }
    
    def _determine_recommendation(self, total_score):
        """Generate recommendation based on score thresholds."""
        if total_score >= SCORE_THRESHOLDS['strong_candidate']:
            return RECOMMENDATIONS['strong_candidate']
        elif total_score >= SCORE_THRESHOLDS['mixed_fit']:
            return RECOMMENDATIONS['mixed_fit']
        else:
            return RECOMMENDATIONS['decline']
    
    def _create_synthesis_prompt(self, project_name, general_research, question_analyses, total_score, recommendation, benchmarks):
        """Create a comprehensive synthesis prompt for the LLM."""
        
        # Check if this appears to be deep research data
        research_type = "deep research" if len(general_research) > 5000 else "general research"
        
        # Build question summaries
        question_summaries = []
        for q in question_analyses:
            q_id = q.get('question_id', '?')
            score = q.get('score', 0)
            confidence = q.get('confidence', 'Unknown')
            analysis = q.get('analysis', 'No analysis available')
            
            # Get question text from config
            question_text = "Unknown question"
            for diag_q in DIAGNOSTIC_QUESTIONS:
                if diag_q['id'] == q_id:
                    question_text = diag_q['question']
                    break
            
            question_summaries.append(f"""
**Q{q_id}: {question_text}**
Score: {score:+d} | Confidence: {confidence}
Analysis: {analysis[:200]}{'...' if len(analysis) > 200 else ''}
""")
        
        # Create the synthesis prompt
        synthesis_prompt = f"""
Synthesize a comprehensive hackathon catalyst evaluation for {project_name}.

**PROJECT CONTEXT (from {research_type}):**
{general_research[:1500]}

**DETAILED QUESTION ANALYSIS:**
{''.join(question_summaries)}

**OVERALL SCORING:**
Total Score: {total_score}/6
Recommendation: {recommendation}

**FRAMEWORK BENCHMARKS:**
{self._format_benchmarks_for_prompt(benchmarks)}

**SYNTHESIS REQUIREMENTS:**
Create a comprehensive summary that:

1. **Executive Summary**: One paragraph overview of {project_name}'s hackathon catalyst potential
2. **Strengths & Opportunities**: Key areas where this partnership could unlock developer potential
3. **Challenges & Risks**: Potential friction points or integration challenges
4. **Recommendation Rationale**: Why this score/recommendation makes sense
5. **Next Steps**: Specific actions if pursuing this partnership

**OUTPUT FORMAT:**
Structure your response as a professional partnership evaluation report. Focus on:
- Hackathon-specific value proposition
- Developer experience and integration complexity
- Partnership readiness and support capabilities
- Risk assessment and mitigation strategies

Keep the tone analytical but accessible, suitable for both technical and business stakeholders.
"""
        
        return synthesis_prompt
    
    def _format_benchmarks_for_prompt(self, benchmarks):
        """Format benchmark examples for the synthesis prompt."""
        try:
            examples = []
            
            # Add complementary examples
            for example in benchmarks.get("framework_benchmarks", {}).get("complementary_examples", []):
                examples.append(f"✅ {example['partner']} ({example['score']:+d}): {example['description']}")
            
            # Add competitive examples  
            for example in benchmarks.get("framework_benchmarks", {}).get("competitive_examples", []):
                examples.append(f"❌ {example['partner']} ({example['score']:+d}): {example['description']}")
            
            return "\n".join(examples) if examples else "No benchmark examples available"
            
        except Exception:
            return "Benchmark formatting failed" 