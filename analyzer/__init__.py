"""
Analyzer package.

Provides the core analysis engine and pipeline for multi-timeframe
signal analysis with optional AI-powered insights.

Core Classes:
    MultiTimeframeAnalyzer: Main analyzer class with DI support.
    AnalysisResult: Immutable dataclass containing analysis results.
    AnalysisPipeline: Complete analysis workflow orchestrator.
    EnhancedAnalysisResult: Analysis result with optional AI insights.
    PipelineBuilder: Fluent builder for pipeline configuration.
    AnalysisCache: In-memory cache for repeated analysis.
    StepResult: Individual pipeline step result.

Sync Functions:
    analyze_symbol: Quick single-symbol analysis.
    analyze_multiple: Parallel batch analysis (ThreadPoolExecutor).
    analyze_with_ai: AI-enabled analysis shortcut.
    quick_analyze: Fast, minimal analysis returning dict.
    get_cache: Get or create global cache instance.

Async Functions (Pattern 18):
    analyze_symbol_async: Non-blocking single-symbol analysis.
    analyze_multiple_async: Concurrent batch analysis (asyncio.gather).
    analyze_with_ai_async: Async AI-enabled analysis.
    run_async: Helper to run async from sync context.

AI Integration:
    AIAnalyzer: Unified AI analysis engine (25 themes).
    AIAnalysisResult: AI-generated insights and recommendations.
    create_ai_analyzer: Factory function for AI analyzer.

Example:
    # Basic usage
    >>> from analyzer import analyze_symbol
    >>> result = analyze_symbol('SPY', interval='1h')
    >>> print(result.summary)

    # Fluent builder
    >>> from analyzer import PipelineBuilder
    >>> result = (PipelineBuilder('AAPL')
    ...     .interval('1h')
    ...     .with_ai()
    ...     .momentum_focused()
    ...     .run())

    # Parallel analysis (sync)
    >>> from analyzer import analyze_multiple
    >>> results = analyze_multiple(['SPY', 'QQQ', 'IWM'], parallel=True)

    # Async analysis
    >>> from analyzer import analyze_multiple_async, run_async
    >>> results = run_async(analyze_multiple_async(['SPY', 'QQQ', 'IWM']))
    >>> # Or in async context:
    >>> results = await analyze_multiple_async(['SPY', 'QQQ'])
"""

from __future__ import annotations

from analyzer.core import MultiTimeframeAnalyzer, AnalysisResult
from analyzer.pipeline import (
    AnalysisPipeline,
    EnhancedAnalysisResult,
    PipelineBuilder,
    AnalysisCache,
    StepResult,
    # Sync functions
    analyze_symbol,
    analyze_multiple,
    analyze_with_ai,
    quick_analyze,
    get_cache,
    # Async functions
    analyze_symbol_async,
    analyze_multiple_async,
    analyze_with_ai_async,
    run_async,
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
    "PipelineBuilder",
    "AnalysisCache",
    "StepResult",
    # Sync functions
    "analyze_symbol",
    "analyze_multiple",
    "analyze_with_ai",
    "quick_analyze",
    "get_cache",
    # Async functions
    "analyze_symbol_async",
    "analyze_multiple_async",
    "analyze_with_ai_async",
    "run_async",
    # AI Integration
    "AIAnalyzer",
    "AIAnalysisResult",
    "create_ai_analyzer",
]
