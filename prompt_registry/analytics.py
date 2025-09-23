"""Analytics functionality for prompt performance tracking."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .models import PromptAnalytics, PromptGrade


class PromptAnalytics:
    """Analytics tracker for prompt performance."""
    
    def __init__(self, prompt_id: str):
        """Initialize analytics for a prompt.
        
        Args:
            prompt_id: ID of the prompt to track
        """
        self.prompt_id = prompt_id
        self.total_uses = 0
        self.successful_uses = 0
        self.failed_uses = 0
        self.success_rate = 0.0
        self.average_score = 0.0
        self.average_response_time = None
        self.average_token_usage = None
        self.common_failures = []
        self.improvement_suggestions = []
        self.usage_over_time = defaultdict(int)
        self.performance_over_time = defaultdict(float)
        self.last_updated = datetime.now()
    
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
            self.average_score = (
                (self.average_score * (self.total_uses - 1) + grade.overall_score) 
                / self.total_uses
            )
        
        # Update time series data
        today = datetime.now().date().isoformat()
        self.usage_over_time[today] += 1
        
        # Update performance over time (7-day rolling average)
        self._update_performance_over_time(grade.overall_score)
        
        self.last_updated = datetime.now()
    
    def _update_performance_over_time(self, score: float) -> None:
        """Update performance over time with rolling average."""
        today = datetime.now().date()
        
        # Calculate 7-day rolling average
        scores = []
        for i in range(7):
            date = (today - timedelta(days=i)).isoformat()
            if date in self.performance_over_time:
                scores.append(self.performance_over_time[date])
        
        scores.append(score)
        rolling_avg = sum(scores) / len(scores)
        
        self.performance_over_time[today.isoformat()] = rolling_avg
    
    def get_performance_trend(self, days: int = 7) -> Dict[str, float]:
        """Get performance trend over the last N days."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        trend = {}
        for i in range(days):
            date = (start_date + timedelta(days=i)).isoformat()
            if date in self.performance_over_time:
                trend[date] = self.performance_over_time[date]
        
        return trend
    
    def get_usage_trend(self, days: int = 7) -> Dict[str, int]:
        """Get usage trend over the last N days."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        trend = {}
        for i in range(days):
            date = (start_date + timedelta(days=i)).isoformat()
            trend[date] = self.usage_over_time.get(date, 0)
        
        return trend
    
    def is_performing_well(self, threshold: float = 0.7) -> bool:
        """Check if the prompt is performing well."""
        return self.success_rate >= threshold and self.average_score >= 7.0
    
    def needs_improvement(self, threshold: float = 0.5) -> bool:
        """Check if the prompt needs improvement."""
        return self.success_rate < threshold or self.average_score < 6.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the analytics."""
        return {
            "prompt_id": self.prompt_id,
            "total_uses": self.total_uses,
            "success_rate": self.success_rate,
            "average_score": self.average_score,
            "is_performing_well": self.is_performing_well(),
            "needs_improvement": self.needs_improvement(),
            "last_updated": self.last_updated.isoformat(),
            "performance_trend": self.get_performance_trend(),
            "usage_trend": self.get_usage_trend()
        }


class AnalyticsManager:
    """Manages analytics for multiple prompts."""
    
    def __init__(self):
        """Initialize the analytics manager."""
        self.analytics: Dict[str, PromptAnalytics] = {}
    
    def get_analytics(self, prompt_id: str) -> PromptAnalytics:
        """Get analytics for a prompt."""
        if prompt_id not in self.analytics:
            self.analytics[prompt_id] = PromptAnalytics(prompt_id)
        return self.analytics[prompt_id]
    
    def update_analytics(self, prompt_id: str, grade: PromptGrade) -> None:
        """Update analytics for a prompt."""
        analytics = self.get_analytics(prompt_id)
        analytics.update_from_grade(grade)
    
    def get_top_performers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing prompts."""
        performers = []
        
        for analytics in self.analytics.values():
            if analytics.total_uses >= 5:  # Minimum usage threshold
                performers.append({
                    "prompt_id": analytics.prompt_id,
                    "success_rate": analytics.success_rate,
                    "average_score": analytics.average_score,
                    "total_uses": analytics.total_uses
                })
        
        # Sort by success rate and average score
        performers.sort(key=lambda x: (x["success_rate"], x["average_score"]), reverse=True)
        
        return performers[:limit]
    
    def get_underperformers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get underperforming prompts that need improvement."""
        underperformers = []
        
        for analytics in self.analytics.values():
            if analytics.needs_improvement() and analytics.total_uses >= 3:
                underperformers.append({
                    "prompt_id": analytics.prompt_id,
                    "success_rate": analytics.success_rate,
                    "average_score": analytics.average_score,
                    "total_uses": analytics.total_uses,
                    "improvement_needed": True
                })
        
        # Sort by worst performance first
        underperformers.sort(key=lambda x: (x["success_rate"], x["average_score"]))
        
        return underperformers[:limit]
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get overall usage statistics."""
        total_prompts = len(self.analytics)
        total_uses = sum(a.total_uses for a in self.analytics.values())
        total_successful = sum(a.successful_uses for a in self.analytics.values())
        
        overall_success_rate = total_successful / total_uses if total_uses > 0 else 0.0
        
        return {
            "total_prompts": total_prompts,
            "total_uses": total_uses,
            "overall_success_rate": overall_success_rate,
            "top_performers": self.get_top_performers(5),
            "underperformers": self.get_underperformers(5)
        }
    
    def generate_insights(self) -> List[str]:
        """Generate insights from the analytics data."""
        insights = []
        
        stats = self.get_usage_statistics()
        
        # Overall performance insight
        if stats["overall_success_rate"] > 0.8:
            insights.append("Overall prompt performance is excellent!")
        elif stats["overall_success_rate"] > 0.6:
            insights.append("Overall prompt performance is good with room for improvement.")
        else:
            insights.append("Overall prompt performance needs significant improvement.")
        
        # Top performers insight
        top_performers = stats["top_performers"]
        if top_performers:
            best_prompt = top_performers[0]
            insights.append(f"Best performing prompt: {best_prompt['prompt_id']} (success rate: {best_prompt['success_rate']:.1%})")
        
        # Underperformers insight
        underperformers = stats["underperformers"]
        if underperformers:
            worst_prompt = underperformers[0]
            insights.append(f"Prompt needing most improvement: {worst_prompt['prompt_id']} (success rate: {worst_prompt['success_rate']:.1%})")
        
        # Usage insights
        if stats["total_uses"] > 100:
            insights.append("High usage volume detected - consider optimizing for performance.")
        
        return insights
