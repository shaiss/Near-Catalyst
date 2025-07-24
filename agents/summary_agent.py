# agents/summary_agent.py
"""
Summary Agent for NEAR Catalyst Framework

This agent synthesizes all analysis results into final hackathon catalyst recommendations,
determining which partners can unlock developer potential and create exponential value.
"""

import json
from config.config import DIAGNOSTIC_QUESTIONS, TIMEOUTS, SCORE_THRESHOLDS, RECOMMENDATIONS, load_partnership_benchmarks
from typing import List, Dict
from agents.litellm_router import completion


class SummaryAgent:
    """
    Agent 8: Summary agent that synthesizes all question analyses into final recommendation
    using LiteLLM Router with automatic local model routing and fallbacks.
    """
    
    def __init__(self, db_manager=None, usage_tracker=None, provider='openai'):
        """Initialize the summary agent with provider selection."""
        self.timeout = TIMEOUTS['summary_agent']
        self.db_manager = db_manager
        self.provider = provider

    def analyze(self, project_name: str, general_research: str, question_analyses: List[Dict], 
               system_prompt: str = None, benchmark_format: str = 'auto') -> Dict:
        """
        Synthesize all analysis results into a final hackathon catalyst recommendation.
        
        Args:
            project_name: Name of the project being analyzed
            general_research: Research content from Agent 1
            question_analyses: List of question analysis results from Agents 2-7
            benchmark_format: Format preference for benchmark examples ('auto', 'json', 'csv')
        
        Returns:
            Dict with final recommendation, scoring breakdown, and cost information
        """
        
        # Load partnership benchmarks for context
        benchmarks = load_partnership_benchmarks(benchmark_format)
        
        # Build analysis summary for prompt
        analysis_summary = self._build_analysis_summary(general_research, question_analyses)
        
        # Build scoring summary
        scoring_summary = self._build_scoring_summary(question_analyses)
        
        # Build benchmark examples for context
        benchmark_examples = self._format_benchmark_examples(benchmarks)
        
        # Create synthesis prompt
        synthesis_prompt = f"""You are the NEAR Protocol Partnership Scout's final decision engine. Your role is to synthesize all research and analysis into a definitive hackathon catalyst recommendation.

PROJECT: {project_name}

COMPLETE ANALYSIS SUMMARY:
{analysis_summary}

SCORING BREAKDOWN:
{scoring_summary}

BENCHMARK EXAMPLES FOR CALIBRATION:
{benchmark_examples}

SYNTHESIS INSTRUCTIONS:

1. **Calculate Total Score**: Sum all individual question scores for final score
2. **Apply Framework Thresholds**: 
   - Score ≥ 4: "Strong candidate; explore MoU/co-marketing"
   - Score 0-3: "Mixed; negotiate scope"
   - Score < 0: "Decline or redesign the collaboration"

3. **Generate Structured Recommendation**:
   - Lead with clear numerical score (X/6)
   - State threshold-based recommendation
   - Summarize key strengths and concerns
   - Provide specific next steps

4. **Format as Partnership Brief**:
   Present your analysis in this exact structure:

   PARTNERSHIP ASSESSMENT: {project_name}
   
   FINAL SCORE: [X]/6
   RECOMMENDATION: [Threshold-based recommendation]
   
   KEY FINDINGS:
   • [Most compelling partnership strength]
   • [Primary concern or limitation]
   • [Integration/collaboration feasibility]
   
   NEXT STEPS:
   • [Specific actionable recommendation]
   • [Risk mitigation if needed]
   
   HACKATHON CATALYST POTENTIAL: [High/Medium/Low] - [Brief justification]

Synthesize with authority and precision. This recommendation will drive partnership decisions."""

        try:
            print(f"  📊 Generating final summary with LiteLLM Router...")
            
            # Use LiteLLM Router with provider-specific routing
            response = completion(
                model="gpt-4.1",
                messages=[{"role": "user", "content": synthesis_prompt}],
                temperature=0.1,
                max_tokens=2000,
                timeout=self.timeout,
                provider=self.provider
            )
            
            content = response.choices[0].message.content
            cost = 0.0
            
            # Extract cost and routing information from Router
            if hasattr(response, '_hidden_params'):
                cost = response._hidden_params.get('response_cost', 0.0)
                cost_source = response._hidden_params.get('cost_source', 'openai')
                local_used = response._hidden_params.get('local_model_used', False)
                router_tags = response._hidden_params.get('router_tags', [])
                
                if local_used:
                    print(f"  🆓 Using local model ({', '.join(router_tags)}) - Cost: Free")
                else:
                    print(f"  💰 Using OpenAI model ({', '.join(router_tags)}) - Cost: ${cost:.4f}")
            
            # Calculate total score from question analyses
            total_score = sum([q.get('score', 0) for q in question_analyses])
            
            # Determine recommendation based on thresholds
            recommendation = self._determine_recommendation(total_score)
            
            return {
                "success": True,
                "content": content,
                "total_score": total_score,
                "recommendation": recommendation,
                "cost": cost
            }
            
        except Exception as e:
            error_msg = f"Summary agent error: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "content": "",
                "total_score": 0,
                "recommendation": "Error in analysis",
                "error": error_msg,
                "cost": 0.0
            }

    def _build_analysis_summary(self, general_research: str, question_analyses: List[Dict]) -> str:
        """Build comprehensive analysis summary from all agents."""
        
        summary_parts = []
        
        # Add general research context
        if general_research:
            summary_parts.append(f"GENERAL RESEARCH:\n{general_research[:1000]}{'...' if len(general_research) > 1000 else ''}")
        
        # Add question-specific analyses
        summary_parts.append("\nQUESTION-SPECIFIC ANALYSES:")
        
        for q_analysis in question_analyses:
            question_text = q_analysis.get('question', 'Unknown Question')
            score = q_analysis.get('score', 0)
            confidence = q_analysis.get('confidence', 'Unknown')
            analysis_content = q_analysis.get('analysis', 'No analysis available')
            
            # Truncate long analyses
            truncated_analysis = analysis_content[:300] + '...' if len(analysis_content) > 300 else analysis_content
            
            summary_parts.append(f"\n{question_text}: {score:+d} ({confidence})")
            summary_parts.append(f"Analysis: {truncated_analysis}")
        
        return "\n".join(summary_parts)

    def _build_scoring_summary(self, question_analyses: List[Dict]) -> str:
        """Build scoring breakdown summary."""
        
        scores = []
        total = 0
        
        for q_analysis in question_analyses:
            question = q_analysis.get('question', 'Unknown')
            score = q_analysis.get('score', 0)
            confidence = q_analysis.get('confidence', 'Unknown')
            
            scores.append(f"{question}: {score:+d} ({confidence})")
            total += score
        
        scores.append(f"\nTOTAL SCORE: {total:+d}/6")
        
        return "\n".join(scores)

    def _format_benchmark_examples(self, benchmarks: Dict) -> str:
        """Format benchmark examples for prompt context."""
        
        examples = []
        
        # Add complementary examples
        for example in benchmarks.get("framework_benchmarks", {}).get("complementary_examples", []):
            partner = example.get('partner', 'Unknown')
            score = example.get('score', 0)
            description = example.get('description', '')
            examples.append(f"{partner}: {score:+d} ({description})")
        
        # Add competitive examples
        for example in benchmarks.get("framework_benchmarks", {}).get("competitive_examples", []):
            partner = example.get('partner', 'Unknown')
            score = example.get('score', 0)
            description = example.get('description', '')
            examples.append(f"{partner}: {score:+d} ({description})")
        
        return "\n".join(examples)

    def _determine_recommendation(self, total_score: int) -> str:
        """Determine recommendation based on score thresholds."""
        
        if total_score >= SCORE_THRESHOLDS['strong_candidate']:
            return RECOMMENDATIONS['strong_candidate']
        elif total_score >= SCORE_THRESHOLDS['mixed_fit']:
            return RECOMMENDATIONS['mixed_fit']
        else:
            return RECOMMENDATIONS['decline'] 