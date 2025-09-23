"""Input preprocessing functionality."""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import ProcessedInput, InputTransformation
from .exceptions import PreprocessingError


class InputPreprocessor:
    """Preprocesses user input to improve prompt effectiveness."""
    
    def __init__(self):
        """Initialize the preprocessor."""
        self.transformations = {
            "intent_normalization": self._normalize_intent,
            "context_enhancement": self._enhance_context,
            "format_standardization": self._standardize_format,
            "noise_removal": self._remove_noise,
            "intent_classification": self._classify_intent,
        }
    
    def preprocess(
        self,
        input_text: str,
        transformations: List[str] = None,
        context: Dict[str, Any] = None
    ) -> ProcessedInput:
        """Preprocess user input.
        
        Args:
            input_text: Original user input
            transformations: List of transformations to apply
            context: Additional context for preprocessing
            
        Returns:
            Processed input with applied transformations
        """
        if transformations is None:
            transformations = ["intent_normalization", "noise_removal"]
        
        processed_text = input_text
        applied_transformations = []
        
        try:
            for transformation in transformations:
                if transformation in self.transformations:
                    processed_text = self.transformations[transformation](
                        processed_text, context or {}
                    )
                    applied_transformations.append(transformation)
            
            return ProcessedInput(
                original_input=input_text,
                processed_input=processed_text,
                transformations_applied=applied_transformations,
                confidence=self._calculate_confidence(input_text, processed_text)
            )
            
        except Exception as e:
            raise PreprocessingError(input_text, str(e))
    
    def _normalize_intent(self, text: str, context: Dict[str, Any]) -> str:
        """Normalize common intent patterns."""
        text = text.lower().strip()
        
        # Common greeting patterns
        greeting_patterns = [
            (r"^(hi|hello|hey)\s*,?\s*(.*)", r"\2"),
            (r"^(hi|hello|hey)\s+(.*)", r"\2"),
        ]
        
        for pattern, replacement in greeting_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Common question patterns
        question_patterns = [
            (r"can you (.*)", r"\1"),
            (r"could you (.*)", r"\1"),
            (r"would you (.*)", r"\1"),
            (r"please (.*)", r"\1"),
            (r"tell me (.*)", r"explain \1"),
            (r"how does (.*) work", r"explain \1"),
            (r"what is (.*)", r"define \1"),
        ]
        
        for pattern, replacement in question_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _enhance_context(self, text: str, context: Dict[str, Any]) -> str:
        """Enhance input with additional context."""
        # Add user context if available
        if "user_level" in context:
            if context["user_level"] == "beginner":
                text = f"For a beginner: {text}"
            elif context["user_level"] == "expert":
                text = f"For an expert: {text}"
        
        # Add domain context
        if "domain" in context:
            text = f"In the context of {context['domain']}: {text}"
        
        # Add conversation history context
        if "conversation_history" in context:
            history = context["conversation_history"]
            if len(history) > 0:
                # Extract key topics from history
                topics = self._extract_topics(history)
                if topics:
                    text = f"Building on our discussion about {', '.join(topics)}: {text}"
        
        return text
    
    def _standardize_format(self, text: str, context: Dict[str, Any]) -> str:
        """Standardize input format."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix common punctuation issues
        text = re.sub(r'\s+([,.!?])', r'\1', text)
        text = re.sub(r'([,.!?])([A-Za-z])', r'\1 \2', text)
        
        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text
    
    def _remove_noise(self, text: str, context: Dict[str, Any]) -> str:
        """Remove noise and irrelevant content."""
        # Remove common filler words
        noise_patterns = [
            r'\b(um|uh|like|you know|basically|literally)\b',
            r'\b(please|thanks|thank you)\b',
            r'\b(can you|could you|would you)\b',
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove extra punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{2,}', '.', text)
        
        return text.strip()
    
    def _classify_intent(self, text: str, context: Dict[str, Any]) -> str:
        """Classify the intent of the input."""
        text_lower = text.lower()
        
        # Intent classification patterns
        if any(word in text_lower for word in ["explain", "how", "what", "why", "when", "where"]):
            intent = "explanation"
        elif any(word in text_lower for word in ["create", "make", "build", "generate", "write"]):
            intent = "creation"
        elif any(word in text_lower for word in ["fix", "solve", "debug", "error", "problem"]):
            intent = "problem_solving"
        elif any(word in text_lower for word in ["review", "check", "analyze", "evaluate"]):
            intent = "analysis"
        elif any(word in text_lower for word in ["compare", "difference", "vs", "versus"]):
            intent = "comparison"
        else:
            intent = "general"
        
        # Add intent prefix
        return f"[{intent}] {text}"
    
    def _extract_topics(self, history: List[str]) -> List[str]:
        """Extract key topics from conversation history."""
        # Simple topic extraction - could be much more sophisticated
        topics = []
        
        # Common technical topics
        tech_topics = ["python", "javascript", "react", "api", "database", "algorithm", "code"]
        
        for message in history[-3:]:  # Last 3 messages
            message_lower = message.lower()
            for topic in tech_topics:
                if topic in message_lower and topic not in topics:
                    topics.append(topic)
        
        return topics[:3]  # Limit to 3 topics
    
    def _calculate_confidence(self, original: str, processed: str) -> float:
        """Calculate confidence in the preprocessing."""
        # Simple confidence calculation based on changes made
        if original == processed:
            return 1.0
        
        # Calculate similarity (simple character-based)
        original_chars = set(original.lower())
        processed_chars = set(processed.lower())
        
        intersection = len(original_chars & processed_chars)
        union = len(original_chars | processed_chars)
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        
        # Adjust confidence based on similarity
        if similarity > 0.8:
            return 0.9
        elif similarity > 0.6:
            return 0.7
        elif similarity > 0.4:
            return 0.5
        else:
            return 0.3
    
    def get_best_transformations(self, input_text: str, prompt_type: str = None) -> List[str]:
        """Get the best transformations for a given input and prompt type."""
        base_transformations = ["intent_normalization", "noise_removal"]
        
        if prompt_type == "code_review":
            return base_transformations + ["format_standardization"]
        elif prompt_type == "customer_support":
            return base_transformations + ["context_enhancement"]
        elif prompt_type == "educational":
            return base_transformations + ["intent_classification", "context_enhancement"]
        else:
            return base_transformations
    
    def preprocess_for_prompt(self, input_text: str, prompt_id: str) -> ProcessedInput:
        """Preprocess input specifically for a given prompt."""
        # Determine prompt type from ID
        prompt_type = self._infer_prompt_type(prompt_id)
        
        # Get appropriate transformations
        transformations = self.get_best_transformations(input_text, prompt_type)
        
        # Create context based on prompt type
        context = self._create_context_for_prompt_type(prompt_type)
        
        return self.preprocess(input_text, transformations, context)
    
    def _infer_prompt_type(self, prompt_id: str) -> str:
        """Infer prompt type from prompt ID."""
        prompt_id_lower = prompt_id.lower()
        
        if any(word in prompt_id_lower for word in ["code", "review", "debug"]):
            return "code_review"
        elif any(word in prompt_id_lower for word in ["customer", "support", "help"]):
            return "customer_support"
        elif any(word in prompt_id_lower for word in ["teach", "explain", "educational"]):
            return "educational"
        elif any(word in prompt_id_lower for word in ["creative", "write", "generate"]):
            return "creative"
        else:
            return "general"
    
    def _create_context_for_prompt_type(self, prompt_type: str) -> Dict[str, Any]:
        """Create context appropriate for the prompt type."""
        context = {}
        
        if prompt_type == "code_review":
            context["domain"] = "software development"
        elif prompt_type == "customer_support":
            context["domain"] = "customer service"
        elif prompt_type == "educational":
            context["domain"] = "education"
        
        return context
