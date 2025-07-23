# agents/model_manager.py
"""
LM Studio Model Manager for NEAR Catalyst Framework Phase 2

Provides programmatic model management via LM Studio Python SDK:
- Automatic model loading and unloading
- Smart memory management 
- Model switching based on task requirements
- Health monitoring and error handling

This replaces manual GUI model management with Python code control.
"""

import asyncio
import time
from typing import Dict, Optional, List, Any
from config.config import LITELLM_CONFIG, LMSTUDIO_CONFIG

try:
    import lmstudio as lms
    LMSTUDIO_AVAILABLE = True
except ImportError:
    LMSTUDIO_AVAILABLE = False
    print("⚠️ LM Studio SDK not available. Install with: pip install lmstudio")


class LMStudioModelManager:
    """
    Manages LM Studio models programmatically via Python SDK
    """
    
    def __init__(self):
        self.client = None
        self.loaded_models = {}
        self.config = LMSTUDIO_CONFIG
        self.model_mapping = LITELLM_CONFIG['model_mapping']
        self.last_used = {}
        
        if LMSTUDIO_AVAILABLE and self.config['use_sdk']:
            try:
                self.client = lms.Client()
                print("✓ LM Studio SDK client initialized")
            except Exception as e:
                print(f"⚠️ LM Studio SDK client failed: {e}")
                self.client = None
        else:
            print("ℹ️ LM Studio SDK disabled or unavailable")
    
    async def ensure_model_loaded(self, model_name: str) -> bool:
        """
        Ensure a specific model is loaded and ready
        
        Args:
            model_name: OpenAI model name (will be mapped to local model)
            
        Returns:
            bool: True if model is ready, False otherwise
        """
        if not self.client:
            print("ℹ️ LM Studio SDK not available, falling back to OpenAI")
            return False
            
        # Map OpenAI model to local model
        local_model = self.model_mapping.get(model_name, model_name)
        
        # Check if already loaded and cached
        if local_model in self.loaded_models:
            self.last_used[local_model] = time.time()
            return True
            
        try:
            # Check if model is loaded in backend but not in our cache
            loaded_models = await self.client.models.list_loaded()
            for model in loaded_models:
                if model.identifier == local_model:
                    self.loaded_models[local_model] = model
                    self.last_used[local_model] = time.time()
                    print(f"✓ Found already loaded: {local_model}")
                    return True
            
            # Model not loaded, need to load it
            print(f"📦 Loading {local_model} for {model_name}...")
            
            # Apply generation config
            load_config = self.config['default_generation_config'].copy()
            
            # Load the model with timeout
            model = await asyncio.wait_for(
                self.client.models.load(local_model, config=load_config),
                timeout=self.config['model_load_timeout']
            )
            
            self.loaded_models[local_model] = model
            self.last_used[local_model] = time.time()
            print(f"✓ Successfully loaded: {local_model}")
            return True
            
        except asyncio.TimeoutError:
            print(f"⏰ Timeout loading {local_model} after {self.config['model_load_timeout']}s")
            return False
        except Exception as e:
            print(f"❌ Failed to load {local_model}: {e}")
            return False
    
    async def smart_model_switching(self, task_type: str, target_model: str) -> str:
        """
        Intelligently switch models based on task requirements
        
        Args:
            task_type: Type of task (general, reasoning, research)
            target_model: OpenAI model name to map
            
        Returns:
            str: Local model name that was loaded
        """
        if not self.client:
            return target_model  # Fall back to original model name
            
        local_model = self.model_mapping.get(target_model, target_model)
        
        # Check if we need to free memory by unloading unused models
        if task_type == 'reasoning' and len(self.loaded_models) > 1:
            await self._optimize_memory_for_reasoning()
        
        # Ensure target model is loaded
        success = await self.ensure_model_loaded(target_model)
        if success:
            return local_model
        else:
            print(f"⚠️ Failed to load {local_model}, falling back to OpenAI")
            return target_model
    
    async def _optimize_memory_for_reasoning(self):
        """
        Optimize memory usage for reasoning tasks by unloading general models
        """
        try:
            # Find general purpose models to unload
            general_models = ['qwen2.5-72b-instruct']
            
            for model_name in general_models:
                if model_name in self.loaded_models:
                    await self._unload_model(model_name)
                    print(f"🧹 Unloaded {model_name} to free memory for reasoning")
                    
        except Exception as e:
            print(f"⚠️ Memory optimization failed: {e}")
    
    async def _unload_model(self, local_model_name: str):
        """
        Unload a specific model to free memory
        
        Args:
            local_model_name: Local model identifier to unload
        """
        if local_model_name in self.loaded_models:
            try:
                model = self.loaded_models[local_model_name]
                if hasattr(model, 'unload'):
                    await model.unload()
                del self.loaded_models[local_model_name]
                if local_model_name in self.last_used:
                    del self.last_used[local_model_name]
                print(f"✓ Unloaded {local_model_name}")
            except Exception as e:
                print(f"⚠️ Failed to unload {local_model_name}: {e}")
    
    async def get_loaded_models(self) -> List[str]:
        """
        Get list of currently loaded models
        
        Returns:
            List of loaded model identifiers
        """
        if not self.client:
            return []
            
        try:
            loaded_models = await self.client.models.list_loaded()
            return [model.identifier for model in loaded_models]
        except Exception as e:
            print(f"⚠️ Failed to get loaded models: {e}")
            return list(self.loaded_models.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on LM Studio SDK setup
        
        Returns:
            Dict with health status information
        """
        health_status = {
            'sdk_available': LMSTUDIO_AVAILABLE,
            'client_connected': self.client is not None,
            'loaded_models': [],
            'total_models': 0,
            'memory_usage': 'unknown'
        }
        
        if self.client:
            try:
                loaded_models = await self.client.models.list_loaded()
                health_status['loaded_models'] = [m.identifier for m in loaded_models]
                health_status['total_models'] = len(loaded_models)
                health_status['status'] = 'healthy'
            except Exception as e:
                health_status['status'] = 'unhealthy'
                health_status['error'] = str(e)
        else:
            health_status['status'] = 'unavailable'
            
        return health_status
    
    def is_local_model_available(self, model_name: str) -> bool:
        """
        Check if a model has a local equivalent available
        
        Args:
            model_name: OpenAI model name
            
        Returns:
            bool: True if local model mapping exists
        """
        return model_name in self.model_mapping and self.client is not None


# Global model manager instance
_global_model_manager = None

def get_model_manager() -> LMStudioModelManager:
    """
    Get the global model manager instance (singleton pattern)
    
    Returns:
        LMStudioModelManager instance
    """
    global _global_model_manager
    if _global_model_manager is None:
        _global_model_manager = LMStudioModelManager()
    return _global_model_manager