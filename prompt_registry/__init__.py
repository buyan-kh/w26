"""
Prompt Registry - A comprehensive prompt management system.

This package provides tools for managing, versioning, and optimizing AI prompts
with MCP server integration, automatic grading, and input preprocessing.
"""

from .core import PromptRegistry, Prompt, PromptPackage
from .grading import PromptGrader, PromptGrade
from .preprocessing import InputPreprocessor
from .analytics import PromptAnalytics
from .exceptions import PromptRegistryError, PromptNotFoundError, InvalidPromptError

__version__ = "0.1.0"
__all__ = [
    "PromptRegistry",
    "Prompt", 
    "PromptPackage",
    "PromptGrader",
    "PromptGrade",
    "InputPreprocessor",
    "PromptAnalytics",
    "PromptRegistryError",
    "PromptNotFoundError", 
    "InvalidPromptError",
]
