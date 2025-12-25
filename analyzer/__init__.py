"""
Analyzer package.

Provides the core analysis engine and pipeline for multi-timeframe
signal analysis with optional AI-powered insights.

Exports:
    MultiTimeframeAnalyzer: Main analyzer class with DI support.
    AnalysisResult: Dataclass containing analysis results.
    AnalysisPipeline: Complete analysis workflow orchestrator.
    EnhancedAnalysisResult: Analysis result with optional AI insights.
    StepResult: Individual pipeline step result.
    analyze_symbol: Quick single-symbol analysis.
    analyze_multiple: Batch analysis for multiple symbols.
    analyze_with_ai: Convenience function for AI-enabled analysis.

AI Integration:
    AIAnalyzer: Unified AI analysis engine (25 themes).
    AIAnalysisResult: AI-generated insights and recommendations.
    create_ai_analyzer: Factory function for AI analyzer.
"""

from __future__ import annotations

from analyzer.core import MultiTimeframeAnalyzer, AnalysisResult
from analyzer.pipeline import (
    AnalysisPipeline,
    EnhancedAnalysisResult,
    StepResult,
    analyze_symbol,
    analyze_multiple,
    analyze_with_ai,
)

# AI integration (optional import)
try:
    from analyzer.ai_integration import AIAnalyzer, AIAnalysisResult, create_ai_analyzer
    _AI_AVAILABLE = True
except ImportError:
    _AI_AVAILABLE = False
    AIAnalyzer = None
    AIAnalysisResult = None
    create_ai_analyzer = None

__all__ = [
    # Core
    "MultiTimeframeAnalyzer",
    "AnalysisResult",
    # Pipeline
    "AnalysisPipeline",
    "EnhancedAnalysisResult",
    "StepResult",
    # Convenience functions
    "analyze_symbol",
    "analyze_multiple",
    "analyze_with_ai",
    # AI Integration
    "AIAnalyzer",
    "AIAnalysisResult",
    "create_ai_analyzer",
]
