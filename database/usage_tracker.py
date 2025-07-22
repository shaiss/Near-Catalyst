# database/usage_tracker.py
"""
API Usage Tracker for NEAR Catalyst Framework

Comprehensive tracking of OpenAI API calls with real-time cost calculation.
Wraps OpenAI client calls to log usage data for cost analysis and optimization.
"""

import json
import time
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

from database.database_manager import DatabaseManager


class PricingManager:
    """
    Manages OpenAI model pricing data from LiteLLM or OpenAI docs.
    """
    
    def __init__(self):
        self.pricing_data = {}
        self.last_updated = None
        self._load_pricing_data()
    
    def _load_pricing_data(self):
        """Load pricing data from LiteLLM JSON source."""
        try:
            # Use LiteLLM pricing data as primary source
            url = "https://raw.githubusercontent.com/BerriAI/litellm/refs/heads/main/model_prices_and_context_window.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.pricing_data = data
            self.last_updated = datetime.now()
            print(f"    ✓ Loaded pricing data for {len(data)} models from LiteLLM")
            
        except Exception as e:
            print(f"    ⚠️ Failed to load LiteLLM pricing data: {e}")
            # Fallback to hardcoded OpenAI pricing (as of July 2025)
            self._load_fallback_pricing()
    
    def _load_fallback_pricing(self):
        """Fallback pricing for key OpenAI models."""
        self.pricing_data = {
            "gpt-4.1": {
                "input_cost_per_token": 0.00001, # $10 per 1M tokens
                "output_cost_per_token": 0.00003, # $30 per 1M tokens
                "litellm_provider": "openai"
            },
            "o3": {
                "input_cost_per_token": 0.00006, # $60 per 1M tokens
                "output_cost_per_token": 0.00024, # $240 per 1M tokens
                "litellm_provider": "openai"
            },
            "o4-mini": {
                "input_cost_per_token": 0.000015, # $15 per 1M tokens
                "output_cost_per_token": 0.00006, # $60 per 1M tokens
                "litellm_provider": "openai"
            },
            "o4-mini-deep-research-2025-06-26": {
                "input_cost_per_token": 0.0002, # $200 per 1M tokens (estimated)
                "output_cost_per_token": 0.0008, # $800 per 1M tokens (estimated)
                "litellm_provider": "openai"
            }
        }
        print(f"    📊 Using fallback pricing for {len(self.pricing_data)} models")
    
    def get_model_pricing(self, model_name: str) -> Dict[str, float]:
        """
        Get pricing information for a specific model.
        
        Args:
            model_name (str): Name of the model
            
        Returns:
            dict: Pricing info with input/output costs per token
        """
        if model_name in self.pricing_data:
            model_info = self.pricing_data[model_name]
            return {
                'input_cost_per_token': model_info.get('input_cost_per_token', 0.0),
                'output_cost_per_token': model_info.get('output_cost_per_token', 0.0)
            }
        
        # If model not found, try to infer pricing from similar models
        base_model = model_name.split('-')[0]
        if base_model in self.pricing_data:
            return self.get_model_pricing(base_model)
        
        print(f"    ⚠️ Unknown model pricing: {model_name}, using default rates")
        return {
            'input_cost_per_token': 0.00001,  # Default to GPT-4.1 rate
            'output_cost_per_token': 0.00003
        }
    
    def calculate_cost(self, model_name: str, prompt_tokens: int, 
                      completion_tokens: int, reasoning_tokens: int = 0) -> float:
        """
        Calculate the cost for a specific API call.
        
        Args:
            model_name (str): Name of the model used
            prompt_tokens (int): Number of input tokens
            completion_tokens (int): Number of output tokens
            reasoning_tokens (int): Number of reasoning tokens (for o-series)
            
        Returns:
            float: Total cost in USD
        """
        pricing = self.get_model_pricing(model_name)
        
        # For reasoning models, reasoning tokens are billed as output tokens
        total_output_tokens = completion_tokens + reasoning_tokens
        
        input_cost = prompt_tokens * pricing['input_cost_per_token']
        output_cost = total_output_tokens * pricing['output_cost_per_token']
        
        return input_cost + output_cost


class APIUsageTracker:
    """
    Comprehensive API usage tracker that wraps OpenAI client calls.
    """
    
    def __init__(self, client, db_manager: DatabaseManager, session_id: str = None):
        """
        Initialize the usage tracker.
        
        Args:
            client: OpenAI client instance
            db_manager: Database manager for storing usage data
            session_id: Optional session ID (will generate if not provided)
        """
        self.client = client
        self.db_manager = db_manager
        self.session_id = session_id or self._generate_session_id()
        self.pricing_manager = PricingManager()
        self.current_project = None
        self.current_agent = None
        
        print(f"    🔍 API Usage Tracker initialized (session: {self.session_id[:8]}...)")
    
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
        """Extract token usage data from OpenAI response."""
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
    
    def track_responses_create(self, model: str, operation_type: str, **kwargs) -> Any:
        """
        Track a responses.create() call (for reasoning models).
        
        Args:
            model (str): Model name
            operation_type (str): Type of operation (research, analysis, etc.)
            **kwargs: Arguments to pass to responses.create()
            
        Returns:
            API response object
        """
        start_time = time.time()
        error_message = None
        success = False
        response = None
        
        try:
            response = self.client.responses.create(model=model, **kwargs)
            success = True
            
        except Exception as e:
            error_message = str(e)
            raise  # Re-raise the exception
            
        finally:
            response_time = time.time() - start_time
            
            # Extract usage data
            if response and success:
                usage_data = self._extract_usage_data(response)
            else:
                usage_data = {'prompt_tokens': 0, 'completion_tokens': 0, 'reasoning_tokens': 0, 'total_tokens': 0}
            
            # Calculate cost
            estimated_cost = self.pricing_manager.calculate_cost(
                model, 
                usage_data['prompt_tokens'],
                usage_data['completion_tokens'],
                usage_data['reasoning_tokens']
            )
            
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
                
                # Log the usage
                if success:
                    if usage_data['reasoning_tokens'] > 0:
                        reasoning_pct = (usage_data['reasoning_tokens'] / usage_data['total_tokens'] * 100) if usage_data['total_tokens'] > 0 else 0
                        print(f"      💭 {operation_type}: {usage_data['reasoning_tokens']:,} reasoning tokens ({reasoning_pct:.1f}% of {usage_data['total_tokens']:,} total) - ${estimated_cost:.4f}")
                    else:
                        print(f"      📊 {operation_type}: {usage_data['total_tokens']:,} tokens - ${estimated_cost:.4f}")
                else:
                    print(f"      ❌ {operation_type} failed: {error_message[:50]}...")
        
        return response
    
    def track_chat_completions_create(self, model: str, operation_type: str, **kwargs) -> Any:
        """
        Track a chat.completions.create() call (for standard models).
        
        Args:
            model (str): Model name
            operation_type (str): Type of operation
            **kwargs: Arguments to pass to chat.completions.create()
            
        Returns:
            API response object
        """
        start_time = time.time()
        error_message = None
        success = False
        response = None
        
        try:
            response = self.client.chat.completions.create(model=model, **kwargs)
            success = True
            
        except Exception as e:
            error_message = str(e)
            raise  # Re-raise the exception
            
        finally:
            response_time = time.time() - start_time
            
            # Extract usage data
            if response and success:
                usage_data = self._extract_usage_data(response)
            else:
                usage_data = {'prompt_tokens': 0, 'completion_tokens': 0, 'reasoning_tokens': 0, 'total_tokens': 0}
            
            # Calculate cost
            estimated_cost = self.pricing_manager.calculate_cost(
                model, 
                usage_data['prompt_tokens'],
                usage_data['completion_tokens'],
                usage_data['reasoning_tokens']
            )
            
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
                
                # Log the usage
                if success:
                    print(f"      📊 {operation_type}: {usage_data['total_tokens']:,} tokens - ${estimated_cost:.4f}")
                else:
                    print(f"      ❌ {operation_type} failed: {error_message[:50]}...")
        
        return response
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get usage summary for the current session."""
        return self.db_manager.get_session_usage_summary(self.session_id)
    
    def print_session_summary(self):
        """Print a formatted session summary."""
        summary = self.get_session_summary()
        
        if summary and summary.get('total_calls', 0) > 0:
            print(f"\n💰 Session Usage Summary (ID: {self.session_id[:8]}...)")
            print(f"   Total API Calls: {summary['total_calls']}")
            print(f"   Total Tokens: {summary['total_tokens']:,}")
            print(f"   Total Cost: ${summary['total_cost']:.4f}")
            print(f"   Average Response Time: {summary['avg_response_time']:.2f}s")
            print(f"   Success Rate: {summary['successful_calls']}/{summary['total_calls']} ({summary['successful_calls']/summary['total_calls']*100:.1f}%)")
            
            if summary.get('agent_breakdown'):
                print(f"   Agent Breakdown:")
                for agent in summary['agent_breakdown']:
                    print(f"     • {agent['agent_type']}: {agent['calls']} calls, {agent['tokens']:,} tokens, ${agent['cost']:.4f}")
            
            if summary.get('model_breakdown'):
                print(f"   Model Breakdown:")
                for model in summary['model_breakdown']:
                    print(f"     • {model['model_name']}: {model['calls']} calls, {model['tokens']:,} tokens, ${model['cost']:.4f}") 