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
import requests
from typing import Dict, Optional, List, Any
from config.config import LITELLM_CONFIG, LMSTUDIO_CONFIG, get_lmstudio_endpoint

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
        
        # Get endpoint configuration (local vs remote)
        self.endpoint_config = get_lmstudio_endpoint()
        self.is_remote = self.endpoint_config['is_remote']
        
        if self.is_remote:
            print(f"🌐 Using remote LM Studio server: {self.endpoint_config['url']}")
            # For remote servers, don't use Python SDK (it's for local control only)
            self.client = None
        elif LMSTUDIO_AVAILABLE and self.config['use_sdk']:
            try:
                self.client = lms.Client()
                print("✓ LM Studio SDK client initialized (local)")
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
        # For remote LM Studio servers, just check if server is available
        if self.is_remote:
            return await self._check_remote_server_availability()
        
        # For local LM Studio, use SDK for model management
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
    
    async def _check_remote_server_availability(self) -> bool:
        """
        Check if remote LM Studio server is available and has models
        
        Returns:
            bool: True if remote server is accessible, False otherwise
        """
        try:
            # Use requests for async HTTP call
            import asyncio
            loop = asyncio.get_event_loop()
            
            def check_server():
                headers = {}
                if self.endpoint_config['api_key']:
                    headers['Authorization'] = f"Bearer {self.endpoint_config['api_key']}"
                
                response = requests.get(
                    f"{self.endpoint_config['url'].rstrip('/v1')}/v1/models",
                    headers=headers,
                    timeout=10
                )
                return response.status_code == 200, response.json() if response.status_code == 200 else None
            
            # Run the synchronous request in a thread
            success, data = await loop.run_in_executor(None, check_server)
            
            if success and data:
                models = data.get('data', [])
                print(f"🌐 Remote LM Studio: {len(models)} models available")
                return len(models) > 0
            else:
                print("⚠️ Remote LM Studio server not responding")
                return False
                
        except Exception as e:
            print(f"❌ Failed to check remote LM Studio server: {e}")
            return False
    
    async def _optimize_memory_for_reasoning(self):
        """
        Optimize memory usage for reasoning tasks by unloading general models
        Note: Only works for local LM Studio servers
        """
        if self.is_remote:
            print("ℹ️ Memory optimization skipped for remote LM Studio server")
            return
            
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
        if self.is_remote:
            # For remote servers, query via HTTP API
            try:
                loop = asyncio.get_event_loop()
                
                def get_remote_models():
                    headers = {}
                    if self.endpoint_config['api_key']:
                        headers['Authorization'] = f"Bearer {self.endpoint_config['api_key']}"
                        
                    response = requests.get(
                        f"{self.endpoint_config['url'].rstrip('/v1')}/v1/models",
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return [model['id'] for model in data.get('data', [])]
                    return []
                
                return await loop.run_in_executor(None, get_remote_models)
            except Exception as e:
                print(f"⚠️ Failed to get remote models: {e}")
                return []
        
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
        Perform health check on LM Studio setup (local SDK or remote server)
        
        Returns:
            Dict with health status information
        """
        health_status = {
            'sdk_available': LMSTUDIO_AVAILABLE,
            'is_remote': self.is_remote,
            'endpoint_url': self.endpoint_config['url'],
            'client_connected': self.client is not None,
            'loaded_models': [],
            'total_models': 0,
            'memory_usage': 'unknown'
        }
        
        if self.is_remote:
            # Health check for remote LM Studio server
            try:
                available = await self._check_remote_server_availability()
                if available:
                    loaded_models = await self.get_loaded_models()
                    health_status['loaded_models'] = loaded_models
                    health_status['total_models'] = len(loaded_models)
                    health_status['status'] = 'healthy'
                    health_status['server_type'] = 'remote'
                else:
                    health_status['status'] = 'unhealthy'
                    health_status['error'] = 'Remote server not accessible'
            except Exception as e:
                health_status['status'] = 'unhealthy'
                health_status['error'] = str(e)
        elif self.client:
            # Health check for local LM Studio SDK
            try:
                loaded_models = await self.client.models.list_loaded()
                health_status['loaded_models'] = [m.identifier for m in loaded_models]
                health_status['total_models'] = len(loaded_models)
                health_status['status'] = 'healthy'
                health_status['server_type'] = 'local'
            except Exception as e:
                health_status['status'] = 'unhealthy'
                health_status['error'] = str(e)
        else:
            health_status['status'] = 'unavailable'
            health_status['server_type'] = 'none'
            
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