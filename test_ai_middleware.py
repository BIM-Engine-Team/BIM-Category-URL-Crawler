#!/usr/bin/env python3
"""
Test script for AI middleware functionality
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from util.ai_client import send_ai_prompt


def test_basic_prompt():
    """Test basic AI prompt using config defaults"""
    print("Testing basic AI prompt with config defaults...")

    try:
        response = send_ai_prompt(
            system_prompt="You are a helpful assistant that gives very brief answers.",
            instruction_prompt="What is 2 + 2? Answer with just the number."
        )
        print(f"✅ Success: {response.strip()}")
        return True
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_specific_provider():
    """Test with specific provider override"""
    print("\nTesting with specific provider (anthropic)...")

    try:
        response = send_ai_prompt(
            system_prompt="You are a helpful assistant that gives very brief answers.",
            instruction_prompt="What is the capital of France? Answer with just the city name.",
            provider="anthropic"
        )
        print(f"✅ Success: {response.strip()}")
        return True
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_with_output_structure():
    """Test with output structure prompt"""
    print("\nTesting with output structure prompt...")

    try:
        response = send_ai_prompt(
            system_prompt="You are a helpful assistant.",
            instruction_prompt="List 3 colors",
            output_structure_prompt="Format your response as a JSON array of strings."
        )
        print(f"✅ Success: {response.strip()}")
        return True
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_different_providers():
    """Test different providers if they're available"""
    providers = ["anthropic", "openai", "google"]

    print("\nTesting different providers...")

    for provider in providers:
        print(f"\n  Testing {provider}...")
        try:
            response = send_ai_prompt(
                system_prompt="You are a helpful assistant.",
                instruction_prompt="Say 'Hello from " + provider + "'",
                provider=provider
            )
            print(f"  ✅ {provider}: {response.strip()}")
        except Exception as e:
            print(f"  ❌ {provider}: {str(e)}")


def main():
    print("🤖 AI Middleware Test Suite")
    print("=" * 40)

    # Check if config file exists
    if not os.path.exists("config.json"):
        print("❌ config.json not found! Please make sure it exists.")
        return

    # Read and display current config
    try:
        import json
        with open("config.json", "r") as f:
            config = json.load(f)
        print(f"📋 Current config: Provider={config.get('ai_provider')}, Model={config.get('ai_model')}")
        print("=" * 40)
    except Exception as e:
        print(f"⚠️  Could not read config: {e}")

    # Run tests
    tests = [
        test_basic_prompt,
        test_specific_provider,
        test_with_output_structure,
        test_different_providers
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")

    print("\n" + "=" * 40)
    print(f"🏁 Test Summary: {passed}/{len(tests)} basic tests passed")
    print("Note: Some provider tests may fail if API keys are not configured.")


if __name__ == "__main__":
    main()