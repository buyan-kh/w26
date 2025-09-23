"""Prompt grading functionality."""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from .models import PromptGrade, PromptAnalytics
from .exceptions import PromptGradingError


class PromptGrader:
    """Grades prompt executions for quality and success."""
    
    def __init__(self, llm_client=None):
        """Initialize the grader.
        
        Args:
            llm_client: LLM client for automatic grading (optional)
        """
        self.llm_client = llm_client
    
    def grade_execution(
        self,
        prompt_id: str,
        user_input: str,
        ai_response: str,
        expected_outcome: str = None,
        grader_type: str = "llm"
    ) -> PromptGrade:
        """Grade a prompt execution.
        
        Args:
            prompt_id: ID of the prompt that was used
            user_input: Original user input
            ai_response: AI's response
            expected_outcome: Expected outcome (optional)
            grader_type: Type of grader to use
            
        Returns:
            Grade for the execution
            
        Raises:
            PromptGradingError: If grading fails
        """
        try:
            if grader_type == "llm" and self.llm_client:
                return self._grade_with_llm(prompt_id, user_input, ai_response, expected_outcome)
            elif grader_type == "rule_based":
                return self._grade_with_rules(prompt_id, user_input, ai_response, expected_outcome)
            else:
                raise PromptGradingError(prompt_id, f"Unknown grader type: {grader_type}")
                
        except Exception as e:
            raise PromptGradingError(prompt_id, str(e))
    
    def _grade_with_llm(
        self,
        prompt_id: str,
        user_input: str,
        ai_response: str,
        expected_outcome: str = None
    ) -> PromptGrade:
        """Grade using an LLM."""
        grading_prompt = f"""
        Rate this AI response on a scale of 1-10 for each criterion:
        
        User asked: "{user_input}"
        AI responded: "{ai_response}"
        Expected outcome: "{expected_outcome or 'N/A'}"
        
        Criteria:
        - Accuracy (1-10): Is the response factually correct and accurate?
        - Helpfulness (1-10): Does the response help the user achieve their goal?
        - Completeness (1-10): Does the response fully address the user's question?
        - Clarity (1-10): Is the response clear and easy to understand?
        
        Consider the context and provide an overall score.
        
        Return JSON only:
        {{
            "overall_score": <number>,
            "accuracy": <number>,
            "helpfulness": <number>,
            "completeness": <number>,
            "clarity": <number>,
            "reasoning": "<explanation>"
        }}
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": grading_prompt}],
                temperature=0.1
            )
            
            grade_data = json.loads(response.choices[0].message.content)
            
            return PromptGrade(
                prompt_id=prompt_id,
                user_input=user_input,
                ai_response=ai_response,
                overall_score=float(grade_data["overall_score"]),
                accuracy=float(grade_data["accuracy"]),
                helpfulness=float(grade_data["helpfulness"]),
                completeness=float(grade_data["completeness"]),
                clarity=float(grade_data["clarity"]),
                reasoning=grade_data["reasoning"],
                grader_type="llm"
            )
            
        except Exception as e:
            raise PromptGradingError(prompt_id, f"LLM grading failed: {str(e)}")
    
    def _grade_with_rules(
        self,
        prompt_id: str,
        user_input: str,
        ai_response: str,
        expected_outcome: str = None
    ) -> PromptGrade:
        """Grade using rule-based criteria."""
        scores = {
            "accuracy": self._score_accuracy(user_input, ai_response),
            "helpfulness": self._score_helpfulness(user_input, ai_response),
            "completeness": self._score_completeness(user_input, ai_response),
            "clarity": self._score_clarity(ai_response)
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        return PromptGrade(
            prompt_id=prompt_id,
            user_input=user_input,
            ai_response=ai_response,
            overall_score=overall_score,
            accuracy=scores["accuracy"],
            helpfulness=scores["helpfulness"],
            completeness=scores["completeness"],
            clarity=scores["clarity"],
            reasoning="Rule-based grading",
            grader_type="rule_based"
        )
    
    def _score_accuracy(self, user_input: str, ai_response: str) -> float:
        """Score accuracy based on simple heuristics."""
        # Simple heuristics - could be much more sophisticated
        score = 5.0  # Base score
        
        # Check for common error indicators
        error_indicators = ["i don't know", "i can't", "i'm not sure", "i don't have access"]
        if any(indicator in ai_response.lower() for indicator in error_indicators):
            score -= 2.0
        
        # Check for specific answers
        if len(ai_response) > 50:  # Substantial response
            score += 1.0
        
        return max(1.0, min(10.0, score))
    
    def _score_helpfulness(self, user_input: str, ai_response: str) -> float:
        """Score helpfulness based on response quality."""
        score = 5.0  # Base score
        
        # Check if response addresses the input
        if len(ai_response) > len(user_input) * 0.5:  # Substantial response
            score += 2.0
        
        # Check for actionable content
        action_words = ["here's", "you can", "try", "use", "follow", "steps"]
        if any(word in ai_response.lower() for word in action_words):
            score += 1.0
        
        return max(1.0, min(10.0, score))
    
    def _score_completeness(self, user_input: str, ai_response: str) -> float:
        """Score completeness based on response thoroughness."""
        score = 5.0  # Base score
        
        # Check response length relative to input
        if len(ai_response) > len(user_input) * 2:  # Detailed response
            score += 2.0
        
        # Check for multiple points or steps
        if ai_response.count('\n') > 2 or ai_response.count('.') > 3:
            score += 1.0
        
        return max(1.0, min(10.0, score))
    
    def _score_clarity(self, ai_response: str) -> float:
        """Score clarity based on response structure."""
        score = 5.0  # Base score
        
        # Check for good structure
        if ai_response.count('\n') > 0:  # Has line breaks
            score += 1.0
        
        # Check for clear sentences
        sentences = ai_response.split('.')
        if len(sentences) > 1:
            avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
            if 10 < avg_sentence_length < 50:  # Good sentence length
                score += 1.0
        
        return max(1.0, min(10.0, score))
    
    def analyze_common_failures(self, grades: list[PromptGrade]) -> list[str]:
        """Analyze common failure patterns from grades."""
        failures = []
        
        # Find low-scoring grades
        low_grades = [g for g in grades if g.overall_score < 7.0]
        
        if not low_grades:
            return ["No common failures identified"]
        
        # Analyze patterns
        accuracy_issues = sum(1 for g in low_grades if g.accuracy < 6.0)
        helpfulness_issues = sum(1 for g in low_grades if g.helpfulness < 6.0)
        completeness_issues = sum(1 for g in low_grades if g.completeness < 6.0)
        clarity_issues = sum(1 for g in low_grades if g.clarity < 6.0)
        
        if accuracy_issues > len(low_grades) * 0.5:
            failures.append("Accuracy issues - responses often incorrect or misleading")
        
        if helpfulness_issues > len(low_grades) * 0.5:
            failures.append("Helpfulness issues - responses don't help users achieve goals")
        
        if completeness_issues > len(low_grades) * 0.5:
            failures.append("Completeness issues - responses don't fully address questions")
        
        if clarity_issues > len(low_grades) * 0.5:
            failures.append("Clarity issues - responses are unclear or hard to understand")
        
        return failures if failures else ["No specific failure patterns identified"]
    
    def generate_improvement_suggestions(self, grades: list[PromptGrade]) -> list[str]:
        """Generate improvement suggestions based on grades."""
        suggestions = []
        
        if not grades:
            return ["No data available for suggestions"]
        
        # Calculate average scores
        avg_accuracy = sum(g.accuracy for g in grades) / len(grades)
        avg_helpfulness = sum(g.helpfulness for g in grades) / len(grades)
        avg_completeness = sum(g.completeness for g in grades) / len(grades)
        avg_clarity = sum(g.clarity for g in grades) / len(grades)
        
        # Generate suggestions based on lowest scores
        if avg_accuracy < 7.0:
            suggestions.append("Improve accuracy by adding more specific examples and fact-checking")
        
        if avg_helpfulness < 7.0:
            suggestions.append("Make responses more actionable and goal-oriented")
        
        if avg_completeness < 7.0:
            suggestions.append("Provide more comprehensive answers that cover all aspects of the question")
        
        if avg_clarity < 7.0:
            suggestions.append("Improve clarity by using simpler language and better structure")
        
        return suggestions if suggestions else ["Prompts are performing well overall"]
