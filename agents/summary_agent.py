# agents/summary_agent.py
"""
Summary Agent for NEAR Partnership Analysis

Agent 8: Synthesizes all research and question analyses into a final recommendation.
Generates comprehensive partnership evaluation reports.
"""

from .config import DIAGNOSTIC_QUESTIONS, TIMEOUTS, SCORE_THRESHOLDS, RECOMMENDATIONS, load_partnership_benchmarks


class SummaryAgent:
    """
    Agent 8: Summary agent that synthesizes all question analyses into final recommendation.
    """
    
    def __init__(self, client):
        """Initialize the summary agent with OpenAI client."""
        self.client = client
        self.timeout = TIMEOUTS['summary_agent']
    
    def analyze(self, project_name, general_research, question_results, system_prompt):
        """
        Generate comprehensive partnership analysis summary.
        
        Args:
            project_name (str): Name of the project
            general_research (str): General research about the project
            question_results (list): Results from all question agents
            system_prompt (str): System prompt with analysis framework
            
        Returns:
            dict: Summary results with recommendation and total score
        """
        print(f"  Generating final summary...")
        
        # Load partnership benchmarks
        benchmarks = load_partnership_benchmarks()
        
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
        
        # Generate recommendation based on score thresholds
        recommendation = self._generate_recommendation(total_score)
        
        # Format benchmark examples for summary
        complementary_examples = [f"{ex['partner']} ({ex['score']:+d})" for ex in benchmarks["framework_benchmarks"]["complementary_examples"]]
        competitive_examples = [f"{ex['partner']} ({ex['score']:+d})" for ex in benchmarks["framework_benchmarks"]["competitive_examples"]]
        
        summary_prompt = f"""
        Apply the "1+1=3" Partnership Framework to generate a comprehensive evaluation of {project_name} as a NEAR Protocol partner.
        
        FRAMEWORK CONTEXT: You are using the established framework that evaluates complementary partners (like {', '.join(complementary_examples)}) versus competitive/misaligned partners (like {', '.join(competitive_examples)}). The goal is to find partners that create exponential value when combined with NEAR Protocol.
        
        PROJECT RESEARCH:
        {general_research[:2000]}
        
        SIX-QUESTION DIAGNOSTIC ANALYSIS:
        {"".join(results_summary)}
        
        TOTAL FRAMEWORK SCORE: {total_score}/6
        
        Generate a partnership evaluation using framework methodology:
        
        1. **Partnership Diagnostic Table**: 
           Present all 6 framework questions with scores and rationales using framework language:
           - Gap-Filler? (strategic gap vs overlap)
           - New Proof-Points? (unlock joint use-cases)
           - Clear Story? ("Better Together" one-sentence pitch)
           - Shared Audience, Different Function? (same devs, different workflow steps)
           - Low-Friction Integration? (wire together in hours)
           - Hands-On Support? (mentors, bounties, tooling)
        
        2. **Framework Classification**:
           Compare to benchmark examples:
           • Complementary Partners ({', '.join(complementary_examples)}): Fill strategic gaps, unlock new use-cases
           • Competitive Partners ({', '.join(competitive_examples)}): Create either/or choices, overlap core functions
           
        3. **"1+1=3" Value Assessment**:
           - What exponential value does this partnership unlock?
           - Does this create capabilities neither platform can deliver alone?
           - Is there a clear "Better Together" narrative without diagrams?
        
        4. **Partnership Recommendation** (using framework thresholds):
           - **+4 to +6**: "Strong candidate; explore MoU/co-marketing" 
           - **0 to +3**: "Mixed; negotiate scope"
           - **< 0**: "Decline or redesign the collaboration"
        
        5. **Implementation Roadmap**: 
           - Specific next steps for NEAR partnership team
           - Integration requirements and hackathon readiness
           - Potential collaboration models (co-marketing, joint bounties, etc.)
        
        Use framework terminology throughout: "strategic gap," "Better Together," "exponential value," "complementary vs competitive."
        """
        
        try:
            summary_response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": summary_prompt}
                ],
                timeout=self.timeout
            )
            
            return {
                "summary": summary_response.choices[0].message.content,
                "total_score": total_score,
                "recommendation": recommendation,
                "success": True
            }
            
        except Exception as e:
            print(f"  ERROR: Summary generation failed: {e}")
            return {
                "summary": f"Summary generation failed for {project_name}: {str(e)}",
                "total_score": total_score,
                "recommendation": recommendation,
                "success": False,
                "error": str(e)
            }
    
    def _generate_recommendation(self, total_score):
        """Generate recommendation based on score thresholds."""
        if total_score >= SCORE_THRESHOLDS['strong_candidate']:
            return RECOMMENDATIONS['strong_candidate']
        elif total_score >= SCORE_THRESHOLDS['mixed_fit']:
            return RECOMMENDATIONS['mixed_fit']
        else:
            return RECOMMENDATIONS['decline'] 