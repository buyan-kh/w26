#!/usr/bin/env python3
"""
Basic usage examples for the Prompt Registry.

This script demonstrates how to use the prompt registry for common tasks.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import prompt_registry
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_registry import PromptRegistry, PromptGrader, InputPreprocessor


def main():
    """Demonstrate basic prompt registry functionality."""
    print("🚀 Prompt Registry Demo")
    print("=" * 50)
    
    # Initialize the registry
    registry = PromptRegistry()
    
    # Install the basic prompts package
    prompts_path = Path(__file__).parent.parent / "prompts" / "packages" / "basic-prompts"
    if prompts_path.exists():
        print(f"📦 Installing prompts from {prompts_path}")
        registry.install(str(prompts_path))
        print("✅ Prompts installed successfully!")
    else:
        print("❌ Prompts directory not found. Please ensure prompts are in the correct location.")
        return
    
    print("\n📋 Available Prompts:")
    print("-" * 30)
    
    # List all prompts
    prompts = registry.list_prompts()
    for prompt in prompts:
        print(f"  • {prompt.id} (v{prompt.version}) - {prompt.name}")
        if prompt.description:
            print(f"    {prompt.description}")
        print()
    
    # Demonstrate getting a specific prompt
    print("🔍 Getting Customer Support Prompt:")
    print("-" * 40)
    
    try:
        customer_support = registry.get("customer-support")
        print(f"Prompt: {customer_support.name}")
        print(f"Content preview: {customer_support.content[:200]}...")
        print()
    except Exception as e:
        print(f"❌ Error getting prompt: {e}")
    
    # Demonstrate search functionality
    print("🔎 Searching for 'code' prompts:")
    print("-" * 35)
    
    search_results = registry.search("code")
    for result in search_results:
        print(f"  • {result.id} - {result.name}")
    print()
    
    # Demonstrate input preprocessing
    print("🔄 Input Preprocessing Demo:")
    print("-" * 30)
    
    preprocessor = InputPreprocessor()
    
    test_inputs = [
        "hello tell me how twosum works",
        "can you please help me with my code?",
        "what is machine learning?",
    ]
    
    for input_text in test_inputs:
        print(f"Original: '{input_text}'")
        processed = preprocessor.preprocess(input_text)
        print(f"Processed: '{processed.processed_input}'")
        print(f"Transformations: {processed.transformations_applied}")
        print(f"Confidence: {processed.confidence:.2f}")
        print()
    
    # Demonstrate prompt grading
    print("📊 Prompt Grading Demo:")
    print("-" * 25)
    
    grader = PromptGrader()
    
    # Simulate a prompt execution
    prompt_id = "customer-support"
    user_input = "I'm having trouble with my account"
    ai_response = "I'd be happy to help you with your account issue. Can you please provide more details about what specific problem you're experiencing?"
    
    try:
        grade = grader.grade_execution(prompt_id, user_input, ai_response)
        print(f"Prompt: {prompt_id}")
        print(f"User Input: {user_input}")
        print(f"AI Response: {ai_response}")
        print(f"Overall Score: {grade.overall_score:.1f}/10")
        print(f"Accuracy: {grade.accuracy:.1f}/10")
        print(f"Helpfulness: {grade.helpfulness:.1f}/10")
        print(f"Completeness: {grade.completeness:.1f}/10")
        print(f"Clarity: {grade.clarity:.1f}/10")
        print(f"Successful: {grade.is_successful}")
        print(f"Reasoning: {grade.reasoning}")
        print()
    except Exception as e:
        print(f"❌ Error grading prompt: {e}")
    
    # Demonstrate analytics
    print("📈 Analytics Demo:")
    print("-" * 20)
    
    # Get analytics for a prompt
    analytics = registry.get_analytics("customer-support")
    if analytics:
        print(f"Customer Support Prompt Analytics:")
        print(f"  Total Uses: {analytics.total_uses}")
        print(f"  Success Rate: {analytics.success_rate:.1%}")
        print(f"  Average Score: {analytics.average_score:.1f}")
        print(f"  Last Updated: {analytics.last_updated}")
    else:
        print("No analytics available yet.")
    
    print("\n✅ Demo completed successfully!")
    print("\n💡 Next Steps:")
    print("  • Try the CLI: python -m prompt_registry.cli --help")
    print("  • Set up the MCP server in your .cursor/mcp.json")
    print("  • Create your own prompt packages")


if __name__ == "__main__":
    main()
