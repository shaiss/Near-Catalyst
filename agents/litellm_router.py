# agents/litellm_router.py
"""
LiteLLM Router Configuration for NEAR Catalyst Framework

Provides unified model routing with:
- Tag-based routing: "local" for LM Studio, "openai" for OpenAI models  
- Automatic fallbacks: Local models → OpenAI models when local fails
- Native LiteLLM cost tracking and error handling
- Environment-based model selection

Replaces custom Enhanced Completion system with LiteLLM's native Router.
"""

import os
from typing import Dict, List, Any, Optional
from litellm import Router
from config.config import LITELLM_CONFIG, get_lmstudio_endpoint


class NearCatalystRouter:
    """
    LiteLLM Router configured for NEAR Catalyst Framework with local/OpenAI fallbacks
    """
    
    def __init__(self):
        self.config = LITELLM_CONFIG
        self.endpoint_config = get_lmstudio_endpoint()
        self.router = None
        self.use_local_models = self.config.get('use_local_models', False)
        
        # Initialize router with model configuration
        self._setup_router()
        
        print(f"🔄 NEAR Catalyst Router initialized:")
        print(f"   Local models: {'enabled' if self.use_local_models else 'disabled'}")
        print(f"   LM Studio: {self.endpoint_config['url']}")
        print(f"   Default tags: {self._get_default_tags()}")
    
    def _setup_router(self):
        """Setup LiteLLM Router with local and OpenAI model configurations"""
        
        model_list = []
        fallbacks = []
        
        # Local model configurations (via LM Studio)
        if self.use_local_models:
            local_models = self._get_local_model_list()
            model_list.extend(local_models)
            
            # Add fallbacks: local → openai for each model
            for model_name in self.config['model_mapping'].keys():
                fallbacks.append({model_name: [f"{model_name}-openai"]})
        
        # OpenAI model configurations
        openai_models = self._get_openai_model_list()
        model_list.extend(openai_models)
        
        # Create router with fallback configuration
        router_config = {
            'model_list': model_list,
            'num_retries': 2,  # Retry each model 2 times before fallback
            'timeout': 120,    # 2 minute timeout per request
        }
        
        # Add fallbacks only if local models are enabled
        if fallbacks:
            router_config['fallbacks'] = fallbacks
            
        self.router = Router(**router_config)
        
        print(f"✅ Router configured with {len(model_list)} models and {len(fallbacks)} fallbacks")
    
    def _get_local_model_list(self) -> List[Dict[str, Any]]:
        """Generate local model configurations for LM Studio"""
        
        local_models = []
        
        for openai_model, local_model in self.config['model_mapping'].items():
            model_config = {
                "model_name": openai_model,  # Keep OpenAI model names for compatibility
                "litellm_params": {
                    "model": f"lm_studio/{local_model}",  # LiteLLM's LM Studio provider format
                    "api_base": self.endpoint_config['url'],
                    "rpm": 20,  # Requests per minute limit
                    "tags": ["local"]  # Tag for local model routing
                },
                "model_info": {
                    "id": f"{openai_model}-local",
                    "source": "lm_studio",
                    "cost_per_token": 0.0  # Local models are free
                }
            }
            
            # Add API key if provided (some LM Studio setups need it)
            if self.endpoint_config.get('api_key'):
                model_config["litellm_params"]["api_key"] = self.endpoint_config['api_key']
            
            local_models.append(model_config)
        
        return local_models
    
    def _get_openai_model_list(self) -> List[Dict[str, Any]]:
        """Generate OpenAI model configurations for fallback"""
        
        openai_models = []
        
        # Standard OpenAI models
        standard_models = [
            "gpt-4.1", "gpt-4", "gpt-4o", "gpt-4o-mini",
            "o3", "o4-mini", "o3-mini",
            "gpt-4o-search-preview"
        ]
        
        for model in standard_models:
            model_config = {
                "model_name": f"{model}-openai",  # Suffix to distinguish from local
                "litellm_params": {
                    "model": model,
                    "api_key": os.getenv('OPENAI_API_KEY'),
                    "rpm": 50,  # Higher RPM for OpenAI
                    "tags": ["openai"]  # Tag for OpenAI routing
                },
                "model_info": {
                    "id": f"{model}-openai",
                    "source": "openai"
                }
            }
            openai_models.append(model_config)
        
        return openai_models
    
    def _get_default_tags(self) -> List[str]:
        """Get default tags based on configuration"""
        if self.use_local_models:
            return ["local"]  # Try local first
        else:
            return ["openai"]  # OpenAI only
    
    def completion(self, model: str, messages: List[Dict], **kwargs) -> Any:
        """
        Route completion through LiteLLM Router with automatic fallbacks
        
        Args:
            model: Model name (e.g. "gpt-4.1", "o3", "o4-mini")
            messages: Chat messages
            **kwargs: Additional completion parameters
            
        Returns:
            LiteLLM completion response with automatic fallback handling
        """
        
        # Determine tags based on configuration
        tags = kwargs.pop('tags', self._get_default_tags())
        
        # Add model routing and fallback info
        completion_params = {
            'model': model,
            'messages': messages,
            'tags': tags,
            **kwargs
        }
        
        try:
            # Use LiteLLM Router for completion with automatic fallbacks
            response = self.router.completion(**completion_params)
            
            # Add cost and routing information
            self._add_routing_metadata(response, tags)
            
            return response
            
        except Exception as e:
            print(f"❌ Router completion failed: {e}")
            raise
    
    def _add_routing_metadata(self, response: Any, tags: List[str]) -> None:
        """Add routing metadata to response for cost tracking"""
        
        if not hasattr(response, '_hidden_params'):
            response._hidden_params = {}
        
        # Determine if local or OpenAI was used based on the tags used in the request
        # This is more reliable than parsing model IDs from the response
        local_used = 'local' in tags
        
        if local_used:
            response._hidden_params['cost_source'] = 'local'
            response._hidden_params['response_cost'] = 0.0  # Local is free
            response._hidden_params['local_model_used'] = True
        else:
            response._hidden_params['cost_source'] = 'openai'
            response._hidden_params['local_model_used'] = False
            # Get actual cost from LiteLLM's cost tracking if available
            actual_cost = response._hidden_params.get('response_cost', 0.0)
            response._hidden_params['response_cost'] = actual_cost
        
        response._hidden_params['router_tags'] = tags
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models by tag"""
        
        models = {
            'local': [],
            'openai': []
        }
        
        if hasattr(self.router, 'model_list'):
            for model in self.router.model_list:
                tags = model.get('litellm_params', {}).get('tags', [])
                model_name = model.get('model_name', '')
                
                if 'local' in tags:
                    models['local'].append(model_name)
                elif 'openai' in tags:
                    models['openai'].append(model_name)
        
        return models
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of router and available models"""
        
        fallbacks = getattr(self.router, 'fallbacks', None)
        fallbacks_count = len(fallbacks) if fallbacks else 0
        
        health = {
            'router_status': 'healthy' if self.router else 'unhealthy',
            'local_models_enabled': self.use_local_models,
            'lm_studio_endpoint': self.endpoint_config['url'],
            'available_models': self.get_available_models(),
            'fallbacks_configured': fallbacks_count > 0,
            'fallbacks_count': fallbacks_count
        }
        
        return health


# Global router instance (singleton pattern)
_router_instance = None

def get_router() -> NearCatalystRouter:
    """Get global router instance (singleton)"""
    global _router_instance
    
    if _router_instance is None:
        _router_instance = NearCatalystRouter()
    
    return _router_instance

def completion(model: str, messages: List[Dict], **kwargs) -> Any:
    """
    Convenience function for router completion
    
    Usage:
        from agents.litellm_router import completion
        response = completion("gpt-4.1", messages)
    """
    router = get_router()
    return router.completion(model, messages, **kwargs) 