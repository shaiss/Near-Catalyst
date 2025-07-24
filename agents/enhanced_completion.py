# agents/enhanced_completion.py
"""
Enhanced Completion Bridge for NEAR Catalyst Framework Phase 2

Bridges LiteLLM's API abstraction with LM Studio SDK's model management.
Provides seamless switching between OpenAI and local models with automatic fallback.

Architecture:
- LiteLLM: Unified API interface
- LM Studio SDK: Programmatic model management
- Automatic fallback: OpenAI when local models unavailable
"""

import asyncio
import litellm
from typing import Any, Dict, Optional
from config.config import LITELLM_CONFIG, get_lmstudio_endpoint
from agents.model_manager import get_model_manager


class EnhancedCompletion:
    """
    Enhanced completion that bridges LiteLLM with LM Studio SDK
    
    Features:
    - Automatic model loading via LM Studio SDK
    - Seamless OpenAI/local model switching
    - Intelligent fallback handling
    - Cost tracking for both local and OpenAI models
    """
    
    def __init__(self):
        self.config = LITELLM_CONFIG
        self.model_manager = get_model_manager()
        self.local_models_enabled = self.config['use_local_models']
        self.lmstudio_sdk_enabled = self.config['use_lmstudio_sdk']
        
        # Get LM Studio endpoint configuration (local vs remote)
        self.endpoint_config = get_lmstudio_endpoint()
        
        print(f"🔄 Enhanced Completion initialized:")
        print(f"   Local models: {'enabled' if self.local_models_enabled else 'disabled'}")
        print(f"   LM Studio: {'remote' if self.endpoint_config['is_remote'] else 'local'} ({self.endpoint_config['url']})")
        print(f"   SDK control: {'enabled' if self.lmstudio_sdk_enabled and not self.endpoint_config['is_remote'] else 'disabled'}")
    
    async def completion(self, model: str, messages: list, **kwargs) -> Any:
        """
        Enhanced completion with automatic model management
        
        Args:
            model: OpenAI model name (will be mapped to local if available)
            messages: Chat messages
            **kwargs: Additional completion parameters
            
        Returns:
            LiteLLM completion response (OpenAI compatible)
        """
        # Determine if we should use local models
        should_use_local = (
            self.local_models_enabled and 
            self.lmstudio_sdk_enabled and 
            self.model_manager.is_local_model_available(model)
        )
        
        if should_use_local:
            return await self._local_completion(model, messages, **kwargs)
        else:
            return await self._openai_completion(model, messages, **kwargs)
    
    async def _local_completion(self, model: str, messages: list, **kwargs) -> Any:
        """
        Complete using local models via LM Studio SDK + LiteLLM
        
        Args:
            model: OpenAI model name
            messages: Chat messages  
            **kwargs: Additional parameters
            
        Returns:
            LiteLLM response via local model
        """
        try:
            # Step 1: Ensure model is loaded via LM Studio SDK
            model_loaded = await self.model_manager.ensure_model_loaded(model)
            
            if not model_loaded:
                print(f"⚠️ Failed to load local model for {model}, falling back to OpenAI")
                return await self._openai_completion(model, messages, **kwargs)
            
            # Step 2: Map to local model name
            local_model = self.config['model_mapping'][model]
            
            # Step 3: Route through LiteLLM to LM Studio API (local or remote)
            completion_params = {
                'model': f"lm_studio/{local_model}",  # LiteLLM LM Studio provider format
                'messages': messages,
                'api_base': self.endpoint_config['url'],
                **kwargs
            }
            
            # Only add API key if one is provided (LM Studio often doesn't need auth)
            if self.endpoint_config['api_key']:
                completion_params['api_key'] = self.endpoint_config['api_key']
            
            response = litellm.completion(**completion_params)
            
            # Add local model metadata to response
            if hasattr(response, '_hidden_params'):
                response._hidden_params['local_model_used'] = local_model
                response._hidden_params['cost_source'] = 'local'
            
            return response
            
        except Exception as e:
            print(f"⚠️ Local completion failed for {model}: {e}")
            print(f"🔄 Falling back to OpenAI for {model}")
            return await self._openai_completion(model, messages, **kwargs)
    
    async def _openai_completion(self, model: str, messages: list, **kwargs) -> Any:
        """
        Complete using OpenAI models via LiteLLM
        
        Args:
            model: OpenAI model name
            messages: Chat messages
            **kwargs: Additional parameters
            
        Returns:
            LiteLLM response via OpenAI
        """
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                **kwargs
            )
            
            # Add OpenAI metadata to response
            if hasattr(response, '_hidden_params'):
                response._hidden_params['cost_source'] = 'openai'
            
            return response
            
        except Exception as e:
            print(f"❌ OpenAI completion failed for {model}: {e}")
            raise  # Re-raise for upstream error handling
    
    def sync_completion(self, model: str, messages: list, **kwargs) -> Any:
        """
        Synchronous wrapper for completion (for backwards compatibility)
        
        Args:
            model: Model name
            messages: Chat messages
            **kwargs: Additional parameters
            
        Returns:
            Completion response
        """
        try:
            # Try to use existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Running in async context, create new task
                import threading
                import queue
                result_queue = queue.Queue()
                
                def run_async():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(self.completion(model, messages, **kwargs))
                        result_queue.put(('success', result))
                    except Exception as e:
                        result_queue.put(('error', e))
                    finally:
                        new_loop.close()
                
                thread = threading.Thread(target=run_async)
                thread.start()
                thread.join()
                
                result_type, result = result_queue.get()
                if result_type == 'error':
                    raise result
                return result
            else:
                # No event loop running, use run_until_complete
                return loop.run_until_complete(self.completion(model, messages, **kwargs))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.completion(model, messages, **kwargs))
    
    def get_cost_info(self, model: str) -> Dict[str, Any]:
        """
        Get cost information for a model
        
        Args:
            model: Model name
            
        Returns:
            Dict with cost information
        """
        cost_info = {
            'model': model,
            'local_available': self.model_manager.is_local_model_available(model),
            'would_use_local': (
                self.local_models_enabled and 
                self.lmstudio_sdk_enabled and 
                self.model_manager.is_local_model_available(model)
            )
        }
        
        # Add cost comparison if available
        if model in self.config['cost_comparison']:
            cost_info.update(self.config['cost_comparison'][model])
        
        return cost_info


# Global enhanced completion instance
_global_enhanced_completion = None

def get_enhanced_completion() -> EnhancedCompletion:
    """
    Get the global enhanced completion instance (singleton pattern)
    
    Returns:
        EnhancedCompletion instance
    """
    global _global_enhanced_completion
    if _global_enhanced_completion is None:
        _global_enhanced_completion = EnhancedCompletion()
    return _global_enhanced_completion


# Backwards compatibility: direct function interface
async def enhanced_completion(model: str, messages: list, **kwargs) -> Any:
    """
    Direct function interface for enhanced completion
    
    Args:
        model: Model name
        messages: Chat messages
        **kwargs: Additional parameters
        
    Returns:
        Completion response
    """
    completion_handler = get_enhanced_completion()
    return await completion_handler.completion(model, messages, **kwargs)


def sync_enhanced_completion(model: str, messages: list, **kwargs) -> Any:
    """
    Synchronous direct function interface for enhanced completion
    
    Args:
        model: Model name  
        messages: Chat messages
        **kwargs: Additional parameters
        
    Returns:
        Completion response
    """
    completion_handler = get_enhanced_completion()
    return completion_handler.sync_completion(model, messages, **kwargs)