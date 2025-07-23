#!/usr/bin/env python3
"""
Helper script to test which OpenAI models support reasoning through LiteLLM.

This script tests various OpenAI models to determine which ones support
reasoning capabilities for the NEAR Catalyst Framework analysis workflow.
"""

import litellm
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_reasoning_support():
    """Test which OpenAI models support reasoning through LiteLLM."""
    
    print("🧠 Testing OpenAI Model Reasoning Support via LiteLLM")
    print("=" * 60)
    
    # List of OpenAI models to test
    openai_models = [
        # GPT-4 family
        "gpt-4o",
        "gpt-4o-mini", 
        "gpt-4o-search-preview",
        "gpt-4.1",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-4",
        
        # O-series (reasoning models)
        "o1",
        "o1-mini",
        "o1-preview", 
        "o3-mini",
        "o4-mini",
        "o4-mini-deep-research-2025-06-26",
        
        # Other potential reasoning models
        "gpt-4o-reasoning-alpha",
        "chatgpt-4o-latest"
    ]
    
    reasoning_models = []
    non_reasoning_models = []
    unavailable_models = []
    
    for model in openai_models:
        try:
            # Test if model supports reasoning
            supports_reasoning = litellm.supports_reasoning(model=model)
            
            if supports_reasoning:
                reasoning_models.append(model)
                print(f"✅ {model} - REASONING SUPPORTED")
            else:
                non_reasoning_models.append(model)
                print(f"❌ {model} - No reasoning support")
                
        except Exception as e:
            unavailable_models.append((model, str(e)))
            print(f"⚠️  {model} - Unavailable or error: {str(e)[:50]}...")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    print(f"\n✅ REASONING MODELS ({len(reasoning_models)}):")
    for model in reasoning_models:
        print(f"   • {model}")
    
    print(f"\n❌ NON-REASONING MODELS ({len(non_reasoning_models)}):")
    for model in non_reasoning_models:
        print(f"   • {model}")
    
    print(f"\n⚠️  UNAVAILABLE/ERROR ({len(unavailable_models)}):")
    for model, error in unavailable_models:
        print(f"   • {model} - {error[:30]}...")
    
    # Recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    print("-" * 30)
    
    if reasoning_models:
        best_reasoning = reasoning_models[0]  # First available reasoning model
        print(f"📈 Best reasoning model for analysis: {best_reasoning}")
        print(f"🔍 Keep using gpt-4o-search-preview for research")
        print(f"💡 Suggested workflow:")
        print(f"   1. Research: gpt-4o-search-preview (web search)")
        print(f"   2. Analysis: {best_reasoning} (reasoning)")
    else:
        print("⚠️  No reasoning models available - check API access or model names")
    
    return {
        'reasoning_models': reasoning_models,
        'non_reasoning_models': non_reasoning_models,
        'unavailable_models': unavailable_models,
        'recommended_reasoning': reasoning_models[0] if reasoning_models else None
    }

def test_model_availability():
    """Test if we can actually call the reasoning models."""
    
    print("\n🧪 TESTING MODEL AVAILABILITY")
    print("=" * 60)
    
    test_models = ["o1-mini", "o1", "gpt-4o", "gpt-4o-search-preview"]
    
    for model in test_models:
        try:
            # Try a simple completion to test availability
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            print(f"✅ {model} - Available and working")
            
        except Exception as e:
            print(f"❌ {model} - Error: {str(e)[:50]}...")

if __name__ == "__main__":
    try:
        # Test reasoning support
        results = test_reasoning_support()
        
        # Test actual model availability
        test_model_availability()
        
        # Export results for config update
        if results['recommended_reasoning']:
            print(f"\n🔧 CONFIG UPDATE NEEDED:")
            print(f"Update config/config.py QUESTION_AGENT_CONFIG:")
            print(f"   reasoning_model: '{results['recommended_reasoning']}'")
            print(f"   research_model: 'gpt-4o-search-preview'")
        
    except Exception as e:
        print(f"❌ Script error: {e}")
        print("Make sure you have OPENAI_API_KEY set and litellm installed") 