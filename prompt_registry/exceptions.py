"""Custom exceptions for the prompt registry."""


class PromptRegistryError(Exception):
    """Base exception for prompt registry errors."""
    pass


class PromptNotFoundError(PromptRegistryError):
    """Raised when a requested prompt is not found."""
    
    def __init__(self, prompt_id: str, version: str = None):
        self.prompt_id = prompt_id
        self.version = version
        message = f"Prompt '{prompt_id}' not found"
        if version:
            message += f" (version {version})"
        super().__init__(message)


class InvalidPromptError(PromptRegistryError):
    """Raised when a prompt is invalid or malformed."""
    
    def __init__(self, prompt_id: str, reason: str):
        self.prompt_id = prompt_id
        self.reason = reason
        super().__init__(f"Invalid prompt '{prompt_id}': {reason}")


class PromptInstallationError(PromptRegistryError):
    """Raised when prompt installation fails."""
    
    def __init__(self, package_name: str, reason: str):
        self.package_name = package_name
        self.reason = reason
        super().__init__(f"Failed to install prompt package '{package_name}': {reason}")


class PromptGradingError(PromptRegistryError):
    """Raised when prompt grading fails."""
    
    def __init__(self, prompt_id: str, reason: str):
        self.prompt_id = prompt_id
        self.reason = reason
        super().__init__(f"Failed to grade prompt '{prompt_id}': {reason}")


class PreprocessingError(PromptRegistryError):
    """Raised when input preprocessing fails."""
    
    def __init__(self, input_text: str, reason: str):
        self.input_text = input_text
        self.reason = reason
        super().__init__(f"Failed to preprocess input: {reason}")
