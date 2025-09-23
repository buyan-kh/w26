"""Core prompt registry functionality."""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .models import Prompt, PromptPackage, PromptAnalytics
from .exceptions import PromptNotFoundError, InvalidPromptError, PromptInstallationError


class PromptRegistry:
    """Main prompt registry class."""
    
    def __init__(self, registry_path: str = None):
        """Initialize the prompt registry.
        
        Args:
            registry_path: Path to the registry directory. Defaults to ~/.prompt-registry
        """
        if registry_path is None:
            registry_path = os.path.expanduser("~/.prompt-registry")
        
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.registry_path / "packages").mkdir(exist_ok=True)
        (self.registry_path / "analytics").mkdir(exist_ok=True)
        (self.registry_path / "cache").mkdir(exist_ok=True)
        
        self._packages: Dict[str, PromptPackage] = {}
        self._analytics: Dict[str, PromptAnalytics] = {}
        self._load_packages()
    
    def install(self, package_path: str, package_name: str = None) -> None:
        """Install a prompt package from a local path or URL.
        
        Args:
            package_path: Path to the package directory or URL
            package_name: Optional name for the package
        """
        try:
            package_path = Path(package_path)
            
            if not package_path.exists():
                raise PromptInstallationError(package_path, "Package path does not exist")
            
            # Load package metadata
            package_file = package_path / "prompt-registry.json"
            if not package_file.exists():
                raise PromptInstallationError(package_path, "No prompt-registry.json found")
            
            with open(package_file, 'r') as f:
                package_data = json.load(f)
            
            # Load prompts
            prompts = []
            prompts_dir = package_path / "prompts"
            if prompts_dir.exists():
                for prompt_file in prompts_dir.glob("**/*.yaml"):
                    with open(prompt_file, 'r') as f:
                        prompt_data = yaml.safe_load(f)
                        prompts.append(Prompt(**prompt_data))
            
            # Create package
            package = PromptPackage(
                name=package_name or package_data.get("name", package_path.name),
                version=package_data.get("version", "1.0.0"),
                description=package_data.get("description"),
                author=package_data.get("author"),
                license=package_data.get("license"),
                repository=package_data.get("repository"),
                prompts=prompts,
                dependencies=package_data.get("dependencies", [])
            )
            
            # Save to registry
            self._packages[package.name] = package
            self._save_package(package)
            
        except Exception as e:
            raise PromptInstallationError(package_path, str(e))
    
    def get(self, prompt_id: str, version: str = None, package_name: str = None) -> Prompt:
        """Get a prompt by ID.
        
        Args:
            prompt_id: ID of the prompt
            version: Specific version (defaults to latest)
            package_name: Specific package to search in
            
        Returns:
            The requested prompt
            
        Raises:
            PromptNotFoundError: If prompt is not found
        """
        if package_name:
            if package_name not in self._packages:
                raise PromptNotFoundError(prompt_id, version)
            
            package = self._packages[package_name]
            if version:
                prompt = package.get_prompt(prompt_id, version)
            else:
                prompt = package.get_latest_prompt(prompt_id)
            
            if prompt:
                return prompt
            else:
                raise PromptNotFoundError(prompt_id, version)
        
        # Search all packages
        for package in self._packages.values():
            if version:
                prompt = package.get_prompt(prompt_id, version)
            else:
                prompt = package.get_latest_prompt(prompt_id)
            
            if prompt:
                return prompt
        
        raise PromptNotFoundError(prompt_id, version)
    
    def search(self, query: str, tags: List[str] = None, limit: int = 10) -> List[Prompt]:
        """Search for prompts.
        
        Args:
            query: Search query
            tags: Filter by tags
            limit: Maximum number of results
            
        Returns:
            List of matching prompts
        """
        results = []
        
        for package in self._packages.values():
            for prompt in package.prompts:
                # Simple text search for now
                if query.lower() in prompt.name.lower() or query.lower() in prompt.content.lower():
                    if tags is None or any(tag in prompt.tags for tag in tags):
                        results.append(prompt)
        
        # Sort by usage count and success rate
        results.sort(key=lambda p: (p.usage_count or 0, p.success_rate or 0), reverse=True)
        
        return results[:limit]
    
    def list_packages(self) -> List[PromptPackage]:
        """List all installed packages."""
        return list(self._packages.values())
    
    def list_prompts(self, package_name: str = None) -> List[Prompt]:
        """List all prompts.
        
        Args:
            package_name: Optional package to filter by
            
        Returns:
            List of prompts
        """
        prompts = []
        
        if package_name:
            if package_name in self._packages:
                prompts.extend(self._packages[package_name].prompts)
        else:
            for package in self._packages.values():
                prompts.extend(package.prompts)
        
        return prompts
    
    def get_analytics(self, prompt_id: str) -> Optional[PromptAnalytics]:
        """Get analytics for a prompt."""
        return self._analytics.get(prompt_id)
    
    def update_analytics(self, prompt_id: str, analytics: PromptAnalytics) -> None:
        """Update analytics for a prompt."""
        self._analytics[prompt_id] = analytics
        self._save_analytics(analytics)
    
    def increment_usage(self, prompt_id: str) -> None:
        """Increment usage count for a prompt."""
        try:
            prompt = self.get(prompt_id)
            prompt.usage_count += 1
            prompt.updated_at = datetime.now()
            
            # Update in package
            for package in self._packages.values():
                for p in package.prompts:
                    if p.id == prompt_id:
                        p.usage_count = prompt.usage_count
                        p.updated_at = prompt.updated_at
                        break
            
            self._save_package(package)
            
        except PromptNotFoundError:
            pass  # Ignore if prompt not found
    
    def _load_packages(self) -> None:
        """Load all packages from the registry."""
        packages_dir = self.registry_path / "packages"
        
        for package_file in packages_dir.glob("*.json"):
            try:
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                
                # Convert prompt data back to Prompt objects
                prompts = [Prompt(**p) for p in package_data.get("prompts", [])]
                package_data["prompts"] = prompts
                
                package = PromptPackage(**package_data)
                self._packages[package.name] = package
                
            except Exception as e:
                print(f"Warning: Failed to load package {package_file}: {e}")
        
        # Load analytics
        analytics_dir = self.registry_path / "analytics"
        for analytics_file in analytics_dir.glob("*.json"):
            try:
                with open(analytics_file, 'r') as f:
                    analytics_data = json.load(f)
                
                analytics = PromptAnalytics(**analytics_data)
                self._analytics[analytics.prompt_id] = analytics
                
            except Exception as e:
                print(f"Warning: Failed to load analytics {analytics_file}: {e}")
    
    def _save_package(self, package: PromptPackage) -> None:
        """Save a package to the registry."""
        package_file = self.registry_path / "packages" / f"{package.name}.json"
        
        with open(package_file, 'w') as f:
            json.dump(package.model_dump(), f, indent=2, default=str)
    
    def _save_analytics(self, analytics: PromptAnalytics) -> None:
        """Save analytics to the registry."""
        analytics_file = self.registry_path / "analytics" / f"{analytics.prompt_id}.json"
        
        with open(analytics_file, 'w') as f:
            json.dump(analytics.model_dump(), f, indent=2, default=str)
