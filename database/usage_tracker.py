# database/usage_tracker.py
"""
API Usage Tracker for NEAR Catalyst Framework

Enhanced tracking of LiteLLM API calls with built-in cost calculation.
Uses LiteLLM's native cost tracking instead of custom pricing management.
"""

import json
import time
import uuid
import sqlite3
import litellm
from datetime import datetime
from typing import Dict, List, Optional, Any

from database.database_manager import DatabaseManager


class APIUsageTracker:
    """
    Enhanced API usage tracker that uses LiteLLM's built-in cost tracking.
    Eliminates custom pricing management for better efficiency and accuracy.
    """
    
    def __init__(self, client=None, db_manager: DatabaseManager = None, session_id: str = None):
        """
        Initialize the usage tracker with LiteLLM native cost tracking and Phase 2 enhanced completion.
        
        Args:
            client: Not used (kept for compatibility) - LiteLLM handles API calls directly
            db_manager: Database manager for storing usage data
            session_id: Optional session ID (will generate if not provided)
        """
        # client parameter kept for compatibility but not used since LiteLLM handles API calls
        self.db_manager = db_manager or DatabaseManager()
        self.session_id = session_id or self._generate_session_id()
        self.current_project = None
        self.current_agent = None
        
        # Phase 2: Enhanced completion support
        self.enhanced_completion = None
        try:
            from agents.enhanced_completion import get_enhanced_completion
            self.enhanced_completion = get_enhanced_completion()
            print(f"    🔄 Enhanced completion integration enabled")
        except ImportError:
            print(f"    ℹ️ Enhanced completion not available, using standard LiteLLM")
        
        # Load LiteLLM pricing data (automatic)
        try:
            # LiteLLM automatically loads pricing for 1,245+ models
            model_count = len(litellm.model_cost) if hasattr(litellm, 'model_cost') else "1,245+"
            print(f"    ✓ Loaded pricing data for {model_count} models from LiteLLM")
        except Exception as e:
            print(f"    ⚠️ LiteLLM pricing data: {e}")
        
        print(f"    🔍 API Usage Tracker initialized with LiteLLM (session: {self.session_id[:8]}...)")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def set_context(self, project_name: str, agent_type: str):
        """
        Set the current context for tracking.
        
        Args:
            project_name (str): Name of the project being analyzed
            agent_type (str): Type of agent making calls
        """
        self.current_project = project_name
        self.current_agent = agent_type
    
    def _extract_usage_data(self, response) -> Dict[str, Any]:
        """Extract token usage data from LiteLLM response."""
        usage_data = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'reasoning_tokens': 0,
            'total_tokens': 0
        }
        
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            usage_data['prompt_tokens'] = getattr(usage, 'prompt_tokens', 0) or getattr(usage, 'input_tokens', 0)
            usage_data['completion_tokens'] = getattr(usage, 'completion_tokens', 0) or getattr(usage, 'output_tokens', 0)
            usage_data['total_tokens'] = getattr(usage, 'total_tokens', 0)
            
            # Handle reasoning tokens for o-series models
            if hasattr(usage, 'output_tokens_details') and usage.output_tokens_details:
                usage_data['reasoning_tokens'] = getattr(usage.output_tokens_details, 'reasoning_tokens', 0)
        
        return usage_data
    
    def _get_litellm_cost(self, response) -> float:
        """
        Extract cost from LiteLLM response using built-in cost tracking.
        Enhanced for Phase 2 to handle local model cost reporting.
        
        Args:
            response: LiteLLM completion response
            
        Returns:
            float: Cost in USD from LiteLLM's built-in tracking (0.0 for local models)
        """
        # Phase 2: Check if this was a local model (cost = 0)
        if hasattr(response, '_hidden_params') and response._hidden_params:
            if response._hidden_params.get('cost_source') == 'local':
                return 0.0  # Local models are free
            
            cost = response._hidden_params.get('response_cost', 0.0)
            if cost and cost > 0:
                return float(cost)
        
        # Consolidated cost extraction using single litellm.completion_cost() approach
        try:
            # Primary method: Use response object directly (preferred)
            cost = litellm.completion_cost(completion_response=response)
            if cost and cost > 0:
                return float(cost)
                
            # Fallback: Manual calculation if response object method fails
            if hasattr(response, 'usage') and response.usage and hasattr(response, 'model'):
                cost = litellm.completion_cost(
                    model=response.model,
                    prompt_tokens=getattr(response.usage, 'prompt_tokens', 0),
                    completion_tokens=getattr(response.usage, 'completion_tokens', 0)
                )
                if cost and cost > 0:
                    return float(cost)
            
        except ValueError as e:
            # Expected: Invalid model name or unsupported model
            print(f"      ℹ️ Cost calculation skipped (unsupported model): {e}")
        except (TypeError, AttributeError) as e:
            # Unexpected: Malformed response structure
            print(f"      ⚠️ Cost extraction failed (malformed response): {e}")
        except KeyError as e:
            # Expected: Missing usage data for free/local models
            print(f"      ℹ️ Cost calculation skipped (missing usage data): {e}")
        except Exception as e:
            # Unexpected: Log for investigation but don't crash
            print(f"      🚨 Unexpected cost calculation error: {e}")
        
        return 0.0  # Fallback if all methods fail

    def track_responses_create(self, model: str, operation_type: str, **kwargs) -> Any:
        """
        Track a LiteLLM completion call using built-in cost tracking.
        
        Args:
            model (str): Model name
            operation_type (str): Type of operation (research, analysis, etc.)
            **kwargs: Arguments to pass to litellm.completion()
            
        Returns:
            API response object
        """
        start_time = time.time()
        error_message = None
        success = False
        response = None
        
        # Convert old responses.create() format to LiteLLM completion format
        if 'input' in kwargs:
            # Convert 'input' to 'messages' format for LiteLLM
            if isinstance(kwargs['input'], str):
                kwargs['messages'] = [{"role": "user", "content": kwargs['input']}]
            elif isinstance(kwargs['input'], list):
                kwargs['messages'] = kwargs['input']
            del kwargs['input']
        
        try:
            response = litellm.completion(model=model, **kwargs)
            success = True
            
        except Exception as e:
            error_message = str(e)
            raise  # Re-raise the exception
            
        finally:
            response_time = time.time() - start_time
            
            # Extract usage data
            if response and success:
                usage_data = self._extract_usage_data(response)
                # Use LiteLLM's built-in cost tracking
                estimated_cost = self._get_litellm_cost(response)
            else:
                usage_data = {'prompt_tokens': 0, 'completion_tokens': 0, 'reasoning_tokens': 0, 'total_tokens': 0}
                estimated_cost = 0.0
            
            # Store usage data
            if self.current_project and self.current_agent:
                self.db_manager.store_api_usage(
                    session_id=self.session_id,
                    project_name=self.current_project,
                    agent_type=self.current_agent,
                    operation_type=operation_type,
                    model_name=model,
                    prompt_tokens=usage_data['prompt_tokens'],
                    completion_tokens=usage_data['completion_tokens'],
                    reasoning_tokens=usage_data['reasoning_tokens'],
                    total_tokens=usage_data['total_tokens'],
                    estimated_cost=estimated_cost,
                    response_time=response_time,
                    success=success,
                    error_message=error_message,
                    request_details={'model': model, 'operation_type': operation_type, **kwargs},
                    response_details={'usage': usage_data} if success else None
                )
                
                # Log the usage with LiteLLM cost data and Phase 2 enhancements  
                if success:
                    # Check if local model was used
                    cost_source = getattr(response, '_hidden_params', {}).get('cost_source', 'unknown')
                    local_model = getattr(response, '_hidden_params', {}).get('local_model_used', None)
                    
                    cost_indicator = "🆓" if estimated_cost == 0.0 else f"${estimated_cost:.4f}"
                    model_info = f"({local_model})" if local_model else f"({model})"
                    
                    if usage_data['reasoning_tokens'] > 0:
                        reasoning_pct = (usage_data['reasoning_tokens'] / usage_data['total_tokens'] * 100) if usage_data['total_tokens'] > 0 else 0
                        print(f"      💭 {operation_type}: {usage_data['reasoning_tokens']:,} reasoning tokens ({reasoning_pct:.1f}% of {usage_data['total_tokens']:,} total) - {cost_indicator} {model_info}")
                    else:
                        print(f"      📊 {operation_type}: {usage_data['total_tokens']:,} tokens - {cost_indicator} {model_info}")
                else:
                    print(f"      ❌ {operation_type} failed: {error_message[:50]}...")
        
        return response
    
    def track_chat_completions_create(self, model: str, operation_type: str, **kwargs) -> Any:
        """
        Track a LiteLLM completion call using built-in cost tracking.
        
        Args:
            model (str): Model name
            operation_type (str): Type of operation
            **kwargs: Arguments to pass to litellm.completion()
            
        Returns:
            API response object
        """
        start_time = time.time()
        error_message = None
        success = False
        response = None
        
        try:
            # Phase 2: Use enhanced completion if available, otherwise use standard LiteLLM
            if self.enhanced_completion:
                response = self.enhanced_completion.sync_completion(model=model, **kwargs)
            else:
                response = litellm.completion(model=model, **kwargs)
            success = True
            
        except Exception as e:
            error_message = str(e)
            raise  # Re-raise the exception
            
        finally:
            response_time = time.time() - start_time
            
            # Extract usage data
            if response and success:
                usage_data = self._extract_usage_data(response)
                # Use LiteLLM's built-in cost tracking
                estimated_cost = self._get_litellm_cost(response)
            else:
                usage_data = {'prompt_tokens': 0, 'completion_tokens': 0, 'reasoning_tokens': 0, 'total_tokens': 0}
                estimated_cost = 0.0
            
            # Store usage data
            if self.current_project and self.current_agent:
                self.db_manager.store_api_usage(
                    session_id=self.session_id,
                    project_name=self.current_project,
                    agent_type=self.current_agent,
                    operation_type=operation_type,
                    model_name=model,
                    prompt_tokens=usage_data['prompt_tokens'],
                    completion_tokens=usage_data['completion_tokens'],
                    reasoning_tokens=usage_data['reasoning_tokens'],
                    total_tokens=usage_data['total_tokens'],
                    estimated_cost=estimated_cost,
                    response_time=response_time,
                    success=success,
                    error_message=error_message,
                    request_details={'model': model, 'operation_type': operation_type, **kwargs},
                    response_details={'usage': usage_data} if success else None
                )
                
                # Log the usage with LiteLLM cost data and Phase 2 enhancements
                if success:
                    # Check if local model was used
                    cost_source = getattr(response, '_hidden_params', {}).get('cost_source', 'unknown')
                    local_model = getattr(response, '_hidden_params', {}).get('local_model_used', None)
                    
                    cost_indicator = "🆓" if estimated_cost == 0.0 else f"${estimated_cost:.4f}"
                    model_info = f"({local_model})" if local_model else f"({model})"
                    
                    if usage_data['reasoning_tokens'] > 0:
                        reasoning_pct = (usage_data['reasoning_tokens'] / usage_data['total_tokens'] * 100) if usage_data['total_tokens'] > 0 else 0
                        print(f"      💭 {operation_type}: {usage_data['reasoning_tokens']:,} reasoning tokens ({reasoning_pct:.1f}% of {usage_data['total_tokens']:,} total) - {cost_indicator} {model_info}")
                    else:
                        print(f"      📊 {operation_type}: {usage_data['total_tokens']:,} tokens - {cost_indicator} {model_info}")
                else:
                    print(f"      ❌ {operation_type} failed: {error_message[:50]}...")
        
        return response

    def print_session_summary(self):
        """Print session usage summary using actual database data."""
        if not self.current_project:
            print("No active project context for summary")
            return
            
        conn = None
        try:
            conn = self.db_manager.get_db_connection()
            cursor = conn.cursor()
            
            # Get session summary
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(total_tokens) as total_tokens,
                    SUM(estimated_cost) as total_cost,
                    SUM(response_time) as total_time,
                    AVG(estimated_cost) as avg_cost_per_call,
                    COUNT(CASE WHEN success = 1 THEN 1 END) as successful_calls,
                    COUNT(CASE WHEN reasoning_tokens > 0 THEN 1 END) as reasoning_calls,
                    SUM(reasoning_tokens) as total_reasoning_tokens
                FROM api_usage_tracking 
                WHERE session_id = ? AND project_name = ?
            ''', (self.session_id, self.current_project))
            
            session_data = cursor.fetchone()
            
            if session_data and session_data[0] > 0:
                total_calls, total_tokens, total_cost, total_time, avg_cost, successful_calls, reasoning_calls, reasoning_tokens = session_data
                success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
                
                print(f"\n💰 Session Usage Summary (ID: {self.session_id[:8]}...)")
                print(f"   Total API Calls: {total_calls}")
                print(f"   Total Tokens: {total_tokens:,}")
                print(f"   Total Cost: ${total_cost:.4f}")
                print(f"   Average Response Time: {total_time/total_calls:.2f}s" if total_calls > 0 else "   Average Response Time: N/A")
                print(f"   Success Rate: {successful_calls}/{total_calls} ({success_rate:.1f}%)")
                
                if reasoning_calls > 0:
                    print(f"   Reasoning Calls: {reasoning_calls}")
                    print(f"   Reasoning Tokens: {reasoning_tokens:,}")
                
                # Get breakdown by agent type
                cursor.execute('''
                    SELECT 
                        agent_type,
                        COUNT(*) as calls,
                        SUM(total_tokens) as tokens,
                        SUM(estimated_cost) as cost
                    FROM api_usage_tracking 
                    WHERE session_id = ? AND project_name = ?
                    GROUP BY agent_type
                    ORDER BY cost DESC
                ''', (self.session_id, self.current_project))
                
                agent_breakdown = cursor.fetchall()
                if agent_breakdown:
                    print("   Agent Breakdown:")
                    for agent_type, calls, tokens, cost in agent_breakdown:
                        print(f"     • {agent_type}: {calls} calls, {tokens:,} tokens, ${cost:.4f}")
                
                # Get breakdown by model
                cursor.execute('''
                    SELECT 
                        model_name,
                        COUNT(*) as calls,
                        SUM(total_tokens) as tokens,
                        SUM(estimated_cost) as cost
                    FROM api_usage_tracking 
                    WHERE session_id = ? AND project_name = ?
                    GROUP BY model_name
                    ORDER BY cost DESC
                ''', (self.session_id, self.current_project))
                
                model_breakdown = cursor.fetchall()
                if model_breakdown:
                    print("   Model Breakdown:")
                    for model_name, calls, tokens, cost in model_breakdown:
                        print(f"     • {model_name}: {calls} calls, {tokens:,} tokens, ${cost:.4f}")
                        
            else:
                print("No usage data found for current session")
                
        except Exception as e:
            print(f"Error generating session summary: {e}")
        finally:
            if conn:
                conn.close()


# Backwards compatibility aliases
PricingManager = APIUsageTracker  # For any code that might still reference PricingManager 