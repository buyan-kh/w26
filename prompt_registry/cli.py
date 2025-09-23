"""Command-line interface for the prompt registry."""

import click
import json
from pathlib import Path
from typing import Optional

from .core import PromptRegistry
from .grading import PromptGrader
from .preprocessing import InputPreprocessor
from .analytics import AnalyticsManager


@click.group()
@click.version_option()
def main():
    """Prompt Registry CLI - Manage and optimize AI prompts."""
    pass


@main.command()
@click.argument('package_path')
@click.option('--name', help='Package name (defaults to directory name)')
def install(package_path: str, name: Optional[str]):
    """Install a prompt package."""
    try:
        registry = PromptRegistry()
        registry.install(package_path, name)
        click.echo(f"✅ Installed package: {name or Path(package_path).name}")
    except Exception as e:
        click.echo(f"❌ Failed to install package: {e}", err=True)


@main.command()
@click.argument('prompt_id')
@click.option('--version', help='Specific version to get')
@click.option('--package', help='Specific package to search in')
@click.option('--output', help='Output file (defaults to stdout)')
def get(prompt_id: str, version: Optional[str], package: Optional[str], output: Optional[str]):
    """Get a prompt by ID."""
    try:
        registry = PromptRegistry()
        prompt = registry.get(prompt_id, version, package)
        
        result = {
            "id": prompt.id,
            "name": prompt.name,
            "version": prompt.version,
            "content": prompt.content,
            "description": prompt.description,
            "tags": prompt.tags,
            "author": prompt.author,
            "usage_count": prompt.usage_count,
            "success_rate": prompt.success_rate
        }
        
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            click.echo(f"✅ Prompt saved to {output}")
        else:
            click.echo(json.dumps(result, indent=2))
            
    except Exception as e:
        click.echo(f"❌ Failed to get prompt: {e}", err=True)


@main.command()
@click.argument('query')
@click.option('--tags', help='Filter by tags (comma-separated)')
@click.option('--limit', default=10, help='Maximum number of results')
def search(query: str, tags: Optional[str], limit: int):
    """Search for prompts."""
    try:
        registry = PromptRegistry()
        tag_list = tags.split(',') if tags else None
        results = registry.search(query, tag_list, limit)
        
        if not results:
            click.echo("No prompts found matching your query.")
            return
        
        click.echo(f"Found {len(results)} prompts:")
        for prompt in results:
            click.echo(f"  • {prompt.id} (v{prompt.version}) - {prompt.name}")
            if prompt.description:
                click.echo(f"    {prompt.description}")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Search failed: {e}", err=True)


@main.command()
@click.option('--package', help='Filter by package name')
def list(package: Optional[str]):
    """List all prompts."""
    try:
        registry = PromptRegistry()
        prompts = registry.list_prompts(package)
        
        if not prompts:
            click.echo("No prompts found.")
            return
        
        click.echo(f"Found {len(prompts)} prompts:")
        for prompt in prompts:
            click.echo(f"  • {prompt.id} (v{prompt.version}) - {prompt.name}")
            if prompt.description:
                click.echo(f"    {prompt.description}")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Failed to list prompts: {e}", err=True)


@main.command()
@click.argument('input_text')
@click.option('--transformations', help='Transformations to apply (comma-separated)')
@click.option('--output', help='Output file (defaults to stdout)')
def preprocess(input_text: str, transformations: Optional[str], output: Optional[str]):
    """Preprocess user input."""
    try:
        preprocessor = InputPreprocessor()
        transformation_list = transformations.split(',') if transformations else None
        result = preprocessor.preprocess(input_text, transformation_list)
        
        if output:
            with open(output, 'w') as f:
                json.dump(result.model_dump(), f, indent=2)
            click.echo(f"✅ Preprocessed input saved to {output}")
        else:
            click.echo(json.dumps(result.model_dump(), indent=2))
            
    except Exception as e:
        click.echo(f"❌ Preprocessing failed: {e}", err=True)


@main.command()
@click.argument('prompt_id')
@click.argument('user_input')
@click.argument('ai_response')
@click.option('--expected', help='Expected outcome')
@click.option('--grader', default='rule_based', help='Grader type (llm or rule_based)')
@click.option('--output', help='Output file (defaults to stdout)')
def grade(prompt_id: str, user_input: str, ai_response: str, expected: Optional[str], grader: str, output: Optional[str]):
    """Grade a prompt execution."""
    try:
        grader_instance = PromptGrader()
        grade = grader_instance.grade_execution(
            prompt_id, user_input, ai_response, expected, grader
        )
        
        if output:
            with open(output, 'w') as f:
                json.dump(grade.model_dump(), f, indent=2)
            click.echo(f"✅ Grade saved to {output}")
        else:
            click.echo(json.dumps(grade.model_dump(), indent=2))
            
    except Exception as e:
        click.echo(f"❌ Grading failed: {e}", err=True)


@main.command()
@click.option('--limit', default=10, help='Maximum number of results')
def analytics(limit: int):
    """Show analytics for all prompts."""
    try:
        registry = PromptRegistry()
        analytics_manager = AnalyticsManager()
        
        # Load existing analytics
        for prompt in registry.list_prompts():
            analytics = registry.get_analytics(prompt.id)
            if analytics:
                analytics_manager.analytics[prompt.id] = analytics
        
        stats = analytics_manager.get_usage_statistics()
        insights = analytics_manager.generate_insights()
        
        click.echo("📊 Prompt Analytics")
        click.echo("=" * 50)
        click.echo(f"Total prompts: {stats['total_prompts']}")
        click.echo(f"Total uses: {stats['total_uses']}")
        click.echo(f"Overall success rate: {stats['overall_success_rate']:.1%}")
        click.echo()
        
        click.echo("💡 Insights:")
        for insight in insights:
            click.echo(f"  • {insight}")
        click.echo()
        
        if stats['top_performers']:
            click.echo("🏆 Top Performers:")
            for performer in stats['top_performers']:
                click.echo(f"  • {performer['prompt_id']}: {performer['success_rate']:.1%} success rate")
            click.echo()
        
        if stats['underperformers']:
            click.echo("⚠️  Underperformers:")
            for underperformer in stats['underperformers']:
                click.echo(f"  • {underperformer['prompt_id']}: {underperformer['success_rate']:.1%} success rate")
            
    except Exception as e:
        click.echo(f"❌ Analytics failed: {e}", err=True)


if __name__ == '__main__':
    main()
