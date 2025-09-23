#!/usr/bin/env python3
"""
MCP Integration Example

This script demonstrates how to integrate the prompt registry with an MCP server
and use it in a real AI application workflow.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_registry import PromptRegistry, PromptGrader, InputPreprocessor


class AIApplication:
    """Example AI application that uses the prompt registry."""
    
    def __init__(self):
        self.registry = PromptRegistry()
        self.grader = PromptGrader()
        self.preprocessor = InputPreprocessor()
        
        # Install prompts
        prompts_path = Path(__file__).parent.parent / "prompts" / "packages" / "basic-prompts"
        if prompts_path.exists():
            self.registry.install(str(prompts_path))
    
    async def process_user_request(self, user_input: str, user_id: str = "default_user"):
        """Process a user request using the prompt registry."""
        print(f"👤 User: {user_input}")
        
        # Step 1: Preprocess the input
        print("🔄 Preprocessing input...")
        processed_input = self.preprocessor.preprocess(user_input)
        print(f"   Original: {processed_input.original_input}")
        print(f"   Processed: {processed_input.processed_input}")
        print(f"   Confidence: {processed_input.confidence:.2f}")
        
        # Step 2: Find the best prompt
        print("🔍 Finding best prompt...")
        best_prompt = self._find_best_prompt(processed_input.processed_input)
        print(f"   Selected: {best_prompt.id} - {best_prompt.name}")
        
        # Step 3: Generate response (simulated)
        print("🤖 Generating response...")
        ai_response = await self._generate_response(best_prompt, processed_input.processed_input)
        print(f"   Response: {ai_response}")
        
        # Step 4: Grade the response
        print("📊 Grading response...")
        grade = self.grader.grade_execution(
            best_prompt.id,
            processed_input.original_input,
            ai_response
        )
        print(f"   Overall Score: {grade.overall_score:.1f}/10")
        print(f"   Successful: {grade.is_successful}")
        
        # Step 5: Update analytics
        print("📈 Updating analytics...")
        self.registry.increment_usage(best_prompt.id)
        
        # Get updated analytics
        analytics = self.registry.get_analytics(best_prompt.id)
        if analytics:
            analytics.update_from_grade(grade)
            self.registry.update_analytics(best_prompt.id, analytics)
            print(f"   Success Rate: {analytics.success_rate:.1%}")
        
        return {
            "user_input": user_input,
            "processed_input": processed_input.processed_input,
            "prompt_used": best_prompt.id,
            "response": ai_response,
            "grade": grade.overall_score,
            "successful": grade.is_successful
        }
    
    def _find_best_prompt(self, processed_input: str):
        """Find the best prompt for the processed input."""
        input_lower = processed_input.lower()
        
        # Simple prompt selection logic
        if any(word in input_lower for word in ["code", "programming", "debug", "review"]):
            return self.registry.get("code-review")
        elif any(word in input_lower for word in ["help", "support", "problem", "issue"]):
            return self.registry.get("customer-support")
        elif any(word in input_lower for word in ["explain", "what is", "how does", "teach"]):
            return self.registry.get("educational")
        elif any(word in input_lower for word in ["write", "story", "creative", "fiction"]):
            return self.registry.get("creative-writing")
        elif any(word in input_lower for word in ["data", "analysis", "statistics", "chart"]):
            return self.registry.get("data-analysis")
        else:
            # Default to customer support
            return self.registry.get("customer-support")
    
    async def _generate_response(self, prompt, user_input):
        """Simulate AI response generation."""
        # In a real application, this would call an LLM API
        # For demo purposes, we'll simulate different responses based on the prompt
        
        if prompt.id == "customer-support":
            return "I'd be happy to help you with that! Can you please provide more details about the specific issue you're experiencing?"
        elif prompt.id == "code-review":
            return "I'll review your code and provide feedback on functionality, performance, and best practices. Please share the code you'd like me to review."
        elif prompt.id == "educational":
            return "I'd be glad to explain that concept! Let me break it down into easy-to-understand parts."
        elif prompt.id == "creative-writing":
            return "I can help you with your creative writing! What kind of story or piece are you working on?"
        elif prompt.id == "data-analysis":
            return "I can help you analyze your data and extract meaningful insights. What kind of data are you working with?"
        else:
            return "I'm here to help! How can I assist you today?"


async def main():
    """Run the MCP integration demo."""
    print("🚀 MCP Integration Demo")
    print("=" * 50)
    
    app = AIApplication()
    
    # Test different types of user inputs
    test_inputs = [
        "hello tell me how twosum works",
        "can you help me debug my Python code?",
        "I need help with my account login",
        "explain machine learning to me",
        "help me write a short story",
        "analyze this sales data for me"
    ]
    
    results = []
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n--- Test Case {i} ---")
        try:
            result = await app.process_user_request(user_input)
            results.append(result)
            print(f"✅ Success: {result['successful']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Total requests: {len(results)}")
    successful = sum(1 for r in results if r['successful'])
    print(f"   Successful: {successful}/{len(results)} ({successful/len(results):.1%})")
    
    # Show analytics for each prompt
    print(f"\n📈 Prompt Analytics:")
    for prompt in app.registry.list_prompts():
        analytics = app.registry.get_analytics(prompt.id)
        if analytics and analytics.total_uses > 0:
            print(f"   {prompt.id}: {analytics.success_rate:.1%} success rate ({analytics.total_uses} uses)")


if __name__ == "__main__":
    asyncio.run(main())
