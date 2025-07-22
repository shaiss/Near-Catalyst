# agents/summary_agent.py
"""
Summary Agent for NEAR Partnership Analysis

Agent 8: Synthesizes all research and question analyses into a final recommendation.
Generates comprehensive partnership evaluation reports.
"""

from .config import DIAGNOSTIC_QUESTIONS, TIMEOUTS, SCORE_THRESHOLDS, RECOMMENDATIONS


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
        if total_score >= SCORE_THRESHOLDS['green_light']:
            return RECOMMENDATIONS['green_light']
        elif total_score >= SCORE_THRESHOLDS['mid_tier']:
            return RECOMMENDATIONS['mid_tier']
        else:
            return RECOMMENDATIONS['decline'] 