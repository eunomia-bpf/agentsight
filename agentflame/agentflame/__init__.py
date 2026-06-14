"""AgentFlame local session tagging and visualization library."""

from .analysis import AnalysisConfig, run_analysis
from .session_history import discover_sessions
from .tagging import LlamaCppTagger, TaggingError

__all__ = [
    "AnalysisConfig",
    "LlamaCppTagger",
    "TaggingError",
    "discover_sessions",
    "run_analysis",
]
