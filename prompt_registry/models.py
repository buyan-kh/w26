"""Data models for the prompt registry."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import semantic_version


class Prompt(BaseModel):
    """Represents a single prompt."""
    
    id: str = Field(..., description="Unique identifier for the prompt")
    name: str = Field(..., description="Human-readable name")
    content: str = Field(..., description="The actual prompt text")
    version: str = Field(default="1.0.0", description="Semantic version")
    description: Optional[str] = Field(None, description="Description of what this prompt does")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    author: Optional[str] = Field(None, description="Author of the prompt")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Performance metrics
    usage_count: int = Field(default=0, description="Number of times this prompt has been used")
    success_rate: Optional[float] = Field(None, description="Success rate (0.0 to 1.0)")
    average_score: Optional[float] = Field(None, description="Average performance score")
    
    def __str__(self) -> str:
        return f"Prompt(id='{self.id}', name='{self.name}', version='{self.version}')"


class PromptPackage(BaseModel):
    """Represents a collection of prompts."""
    
    name: str = Field(..., description="Package name")
    version: str = Field(default="1.0.0", description="Package version")
    description: Optional[str] = Field(None, description="Package description")
    author: Optional[str] = Field(None, description="Package author")
    license: Optional[str] = Field(None, description="Package license")
    repository: Optional[str] = Field(None, description="Source repository URL")
    
    prompts: List[Prompt] = Field(default_factory=list, description="Prompts in this package")
    dependencies: List[str] = Field(default_factory=list, description="Package dependencies")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def get_prompt(self, prompt_id: str, version: str = None) -> Optional[Prompt]:
        """Get a specific prompt from this package."""
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                if version is None or prompt.version == version:
                    return prompt
        return None
    
    def get_latest_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get the latest version of a prompt."""
        matching_prompts = [p for p in self.prompts if p.id == prompt_id]
        if not matching_prompts:
            return None
        
        # Sort by version and return the latest
        matching_prompts.sort(key=lambda p: semantic_version.Version(p.version), reverse=True)
        return matching_prompts[0]


class PromptGrade(BaseModel):
    """Represents a grade for a prompt execution."""
    
    prompt_id: str = Field(..., description="ID of the graded prompt")
    user_input: str = Field(..., description="Original user input")
    ai_response: str = Field(..., description="AI's response")
    
    # Grading scores (0-10 scale)
    overall_score: float = Field(..., ge=0, le=10, description="Overall score")
    accuracy: float = Field(..., ge=0, le=10, description="Accuracy score")
    helpfulness: float = Field(..., ge=0, le=10, description="Helpfulness score")
    completeness: float = Field(..., ge=0, le=10, description="Completeness score")
    clarity: float = Field(..., ge=0, le=10, description="Clarity score")
    
    reasoning: str = Field(..., description="Explanation of the grade")
    grader_type: str = Field(default="llm", description="Type of grader used")
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def is_successful(self) -> bool:
        """Whether this execution was considered successful (score >= 7)."""
        return self.overall_score >= 7.0


class PromptAnalytics(BaseModel):
    """Analytics data for a prompt."""
    
    prompt_id: str = Field(..., description="ID of the prompt")
    
    # Usage statistics
    total_uses: int = Field(default=0, description="Total number of uses")
    successful_uses: int = Field(default=0, description="Number of successful uses")
    failed_uses: int = Field(default=0, description="Number of failed uses")
    
    # Performance metrics
    success_rate: float = Field(default=0.0, description="Success rate (0.0 to 1.0)")
    average_score: float = Field(default=0.0, description="Average performance score")
    average_response_time: Optional[float] = Field(None, description="Average response time in seconds")
    average_token_usage: Optional[int] = Field(None, description="Average token usage")
    
    # Common issues
    common_failures: List[str] = Field(default_factory=list, description="Common failure reasons")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Suggested improvements")
    
    # Time series data
    usage_over_time: Dict[str, int] = Field(default_factory=dict, description="Usage count by date")
    performance_over_time: Dict[str, float] = Field(default_factory=dict, description="Performance by date")
    
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def update_from_grade(self, grade: PromptGrade) -> None:
        """Update analytics from a new grade."""
        self.total_uses += 1
        if grade.is_successful:
            self.successful_uses += 1
        else:
            self.failed_uses += 1
        
        # Update success rate
        self.success_rate = self.successful_uses / self.total_uses if self.total_uses > 0 else 0.0
        
        # Update average score (running average)
        if self.total_uses == 1:
            self.average_score = grade.overall_score
        else:
            self.average_score = (self.average_score * (self.total_uses - 1) + grade.overall_score) / self.total_uses
        
        self.last_updated = datetime.now()


class InputTransformation(BaseModel):
    """Represents a transformation to apply to user input."""
    
    name: str = Field(..., description="Name of the transformation")
    type: str = Field(..., description="Type of transformation")
    config: Dict[str, Any] = Field(default_factory=dict, description="Transformation configuration")
    
    def apply(self, input_text: str) -> str:
        """Apply this transformation to the input text."""
        # This would be implemented by specific transformation classes
        return input_text


class ProcessedInput(BaseModel):
    """Represents processed user input."""
    
    original_input: str = Field(..., description="Original user input")
    processed_input: str = Field(..., description="Processed input")
    transformations_applied: List[str] = Field(default_factory=list, description="Transformations that were applied")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the processing")
    
    def __str__(self) -> str:
        return f"ProcessedInput(original='{self.original_input[:50]}...', processed='{self.processed_input[:50]}...')"
