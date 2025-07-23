#!/usr/bin/env python3
"""
Helper Script: Check Web Search Support for OpenAI Models

This script tests which OpenAI models support web search capabilities
using LiteLLM's supports_web_search() function.
"""

import litellm
from config.config import QUESTION_AGENT_CONFIG

def check_web_search_support():
    """Check which OpenAI models support web search."""
    print("🔍 Checking Web Search Support for OpenAI Models\n")
    
    # Models from our config
    current_models = [
        QUESTION_AGENT_CONFIG['reasoning_model']['production'],
        QUESTION_AGENT_CONFIG['reasoning_model']['development'], 
        QUESTION_AGENT_CONFIG['fallback_model']
    ]
    
    # Additional OpenAI models to test
    test_models = [
        "openai/gpt-4o",
        "openai/gpt-4o-search-preview",
        "openai/gpt-4o-mini", 
        "openai/gpt-4.1",
        "openai/gpt-4",
        "openai/gpt-3.5-turbo",
        "openai/o1",
        "openai/o1-mini",
        "openai/o3",
        "openai/o3-mini",
        "gpt-4o",
        "gpt-4o-search-preview",
        "gpt-4o-mini",
        "gpt-4.1",
        "o1",
        "o1-mini", 
        "o3",
        "o3-mini"
    ]
    
    # Combine and deduplicate
    all_models = list(set(current_models + test_models))
    
    print("📋 Current Config Models:")
    for model in current_models:
        supports = litellm.supports_web_search(model=model)
        status = "✅ YES" if supports else "❌ NO"
        print(f"  {model:<30} {status}")
    
    print(f"\n🧪 Testing {len(all_models)} OpenAI Models for Web Search Support:")
    print("=" * 70)
    
    supported_models = []
    unsupported_models = []
    
    for model in sorted(all_models):
        try:
            supports = litellm.supports_web_search(model=model)
            status = "✅ YES" if supports else "❌ NO"
            print(f"  {model:<30} {status}")
            
            if supports:
                supported_models.append(model)
            else:
                unsupported_models.append(model)
                
        except Exception as e:
            print(f"  {model:<30} ⚠️  ERROR: {str(e)[:30]}...")
            unsupported_models.append(model)
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Supported models: {len(supported_models)}")
    print(f"  ❌ Unsupported models: {len(unsupported_models)}")
    
    if supported_models:
        print(f"\n🎯 Recommended Models for Web Search:")
        for model in supported_models[:5]:  # Show top 5
            print(f"  • {model}")
    
    if not any(litellm.supports_web_search(model=model) for model in current_models):
        print(f"\n🚨 CRITICAL: None of our current config models support web search!")
        print(f"   Current models: {current_models}")
        if supported_models:
            print(f"   Recommended switch to: {supported_models[0]}")
    
    return {
        'supported': supported_models,
        'unsupported': unsupported_models,
        'current_config_support': {model: litellm.supports_web_search(model=model) for model in current_models}
    }

if __name__ == "__main__":
    try:
        results = check_web_search_support()
        print(f"\n✅ Web search support check completed!")
    except Exception as e:
        print(f"❌ Error checking web search support: {e}")
        import traceback
        traceback.print_exc() 