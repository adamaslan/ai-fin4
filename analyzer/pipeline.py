"""
Analysis pipeline.

Defines the complete analysis workflow with middleware-like composition.
Each step can be skipped or customized. Optionally includes AI-powered
analysis for signal summarization, recommendations, and risk assessment.

Design Patterns Applied:
    - Decorator Pattern: @step_handler for consistent step execution
    - Builder Pattern: PipelineBuilder for fluent configuration
    - Strategy Pattern: Pluggable components via dependency injection
    - Template Method: run() defines skeleton, steps are customizable
    - Async/Await: Non-blocking I/O for data fetching (Pattern 18)
"""

from __future__ import annotations

import asyncio
from typing import Optional, List, Any, Dict, Callable, TypeVar, Tuple
from dataclasses import dataclass, field
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import pandas as pd
from logging_config import get_logger
from analyzer.core import MultiTimeframeAnalyzer, AnalysisResult
from config import SignalConfig
from data.provider import DataProvider, YFinanceProvider
from exceptions import AnalyzerError

logger = get_logger()

T = TypeVar('T')


# ============ PIPELINE STEP RESULT ============


@dataclass
class StepResult:
    """Result from a pipeline step."""

    name: str
    """Step name."""

    success: bool
    """Whether step succeeded."""

    data: Any
    """Step output data."""

    error: Optional[str] = None
    """Error message if failed."""

    duration_ms: float = 0.0
    """Step execution time in milliseconds."""

    message: str = ""
    """Additional message."""

    def __str__(self) -> str:
        """Return formatted result."""
        status = "✓" if self.success else "✗"
        return f"{status} {self.name} ({self.duration_ms:.0f}ms)"


# ============ STEP DECORATOR (DRY Pattern) ============


def step_handler(
    step_name: str,
    message_fn: Optional[Callable[[Any], str]] = None,
    fatal: bool = True,
):
    """
    Decorator for pipeline steps with consistent timing, logging, and error handling.

    Eliminates duplication across _step_* methods by centralizing:
    - Timing measurement
    - Start/end logging
    - Error handling and StepResult creation

    Args:
        step_name: Human-readable step name.
        message_fn: Optional function to generate success message from result.
        fatal: If True, exceptions propagate. If False, step continues on error.

    Example:
        @step_handler("Fetch Data", message_fn=lambda d: f"{len(d)} bars")
        def _step_fetch_data(self) -> pd.DataFrame:
            return self.analyzer.fetch_data()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., StepResult]:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> StepResult:
            self._log_step_start(step_name)
            start_time = time.time()

            try:
                result_data = func(self, *args, **kwargs)
                duration = (time.time() - start_time) * 1000

                message = ""
                if message_fn and result_data is not None:
                    try:
                        message = message_fn(result_data)
                    except Exception:
                        message = "completed"

                result = StepResult(
                    name=step_name,
                    success=True,
                    data=result_data,
                    duration_ms=duration,
                    message=message,
                )
                self.steps.append(result)
                self._log_step_result(result)
                return result

            except Exception as e:
                duration = (time.time() - start_time) * 1000
                result = StepResult(
                    name=step_name,
                    success=False,
                    data=None,
                    error=str(e),
                    duration_ms=duration,
                    message=f"{step_name} failed" if not fatal else "",
                )
                self.steps.append(result)
                self._log_step_result(result)

                if fatal:
                    raise
                return result

        return wrapper
    return decorator


# ============ ENHANCED ANALYSIS RESULT ============


@dataclass
class EnhancedAnalysisResult:
    """
    Analysis result with optional AI insights.

    Wraps the base AnalysisResult with additional AI-powered analysis.
    """

    base_result: AnalysisResult
    """Core analysis result."""

    ai_result: Optional[Any] = None
    """AI analysis result (AIAnalysisResult if AI enabled)."""

    pipeline_summary: Dict[str, Any] = field(default_factory=dict)
    """Pipeline execution summary."""

    @property
    def symbol(self) -> str:
        """Get symbol from base result."""
        return self.base_result.symbol

    @property
    def signals(self):
        """Get signals from base result."""
        return self.base_result.signals

    @property
    def summary(self) -> str:
        """Get combined summary."""
        base = self.base_result.summary
        if self.ai_result and hasattr(self.ai_result, 'signal_summary'):
            return f"{base}\n\nAI: {self.ai_result.signal_summary[:200]}..."
        return base

    def __str__(self) -> str:
        """Return string representation."""
        return self.summary


# ============ PIPELINE BUILDER (Fluent API) ============


class PipelineBuilder:
    """
    Builder for fluent AnalysisPipeline configuration.

    Enables readable, chainable configuration without remembering
    parameter order or dealing with many constructor arguments.

    Example:
        >>> result = (PipelineBuilder('SPY')
        ...     .interval('1h')
        ...     .with_ai()
        ...     .momentum_focused()
        ...     .run())
    """

    def __init__(self, symbol: str):
        """Initialize builder with required symbol."""
        self._symbol = symbol
        self._interval = "1d"
        self._period: Optional[str] = None
        self._config: Optional[SignalConfig] = None
        self._data_provider: Optional[DataProvider] = None
        self._indicator_factory = "comprehensive"
        self._detector_factory = "comprehensive"
        self._quality_min = 0.3
        self._skip_indicators = False
        self._skip_signals = False
        self._enable_ai = False
        self._enable_progress = True

    # ---- Chainable setters ----

    def interval(self, interval: str) -> "PipelineBuilder":
        """Set analysis interval/timeframe."""
        self._interval = interval
        return self

    def period(self, period: str) -> "PipelineBuilder":
        """Set data period (e.g., '1mo', '3mo', '1y')."""
        self._period = period
        return self

    def config(self, config: SignalConfig) -> "PipelineBuilder":
        """Set custom SignalConfig."""
        self._config = config
        return self

    def provider(self, provider: DataProvider) -> "PipelineBuilder":
        """Set custom data provider."""
        self._data_provider = provider
        return self

    def quality_threshold(self, minimum: float) -> "PipelineBuilder":
        """Set minimum signal quality (0.0 - 1.0)."""
        self._quality_min = max(0.0, min(1.0, minimum))
        return self

    def with_ai(self, enabled: bool = True) -> "PipelineBuilder":
        """Enable AI-powered analysis."""
        self._enable_ai = enabled
        return self

    def silent(self) -> "PipelineBuilder":
        """Disable progress output."""
        self._enable_progress = False
        return self

    def skip_indicators(self) -> "PipelineBuilder":
        """Skip indicator calculation step."""
        self._skip_indicators = True
        return self

    def skip_signals(self) -> "PipelineBuilder":
        """Skip signal detection step."""
        self._skip_signals = True
        return self

    # ---- Preset configurations ----

    def momentum_focused(self) -> "PipelineBuilder":
        """Use momentum-focused indicators and detectors."""
        self._indicator_factory = "momentum"
        self._detector_factory = "basic"
        return self

    def trend_focused(self) -> "PipelineBuilder":
        """Use trend-focused indicators and detectors."""
        self._indicator_factory = "trend"
        self._detector_factory = "trend"
        return self

    def intraday(self) -> "PipelineBuilder":
        """Configure for intraday trading."""
        self._indicator_factory = "intraday"
        self._detector_factory = "intraday"
        if self._interval == "1d":
            self._interval = "5m"
        return self

    def swing(self) -> "PipelineBuilder":
        """Configure for swing trading."""
        self._indicator_factory = "swing"
        self._detector_factory = "swing"
        return self

    def comprehensive(self) -> "PipelineBuilder":
        """Use all available indicators and detectors."""
        self._indicator_factory = "comprehensive"
        self._detector_factory = "comprehensive"
        return self

    # ---- Terminal operations ----

    def build(self) -> "AnalysisPipeline":
        """Build the configured AnalysisPipeline."""
        return AnalysisPipeline(
            symbol=self._symbol,
            interval=self._interval,
            period=self._period,
            config=self._config,
            data_provider=self._data_provider,
            indicator_factory=self._indicator_factory,
            detector_factory=self._detector_factory,
            quality_min=self._quality_min,
            skip_indicators=self._skip_indicators,
            skip_signals=self._skip_signals,
            enable_ai=self._enable_ai,
            enable_progress=self._enable_progress,
        )

    def run(self) -> EnhancedAnalysisResult:
        """Build and execute the pipeline (sync)."""
        return self.build().run()

    async def run_async(self) -> EnhancedAnalysisResult:
        """Build and execute the pipeline (async)."""
        return await self.build().run_async()


# ============ ANALYSIS PIPELINE ============


class AnalysisPipeline:
    """
    Complete market analysis pipeline with optional AI.

    Composes analysis steps into a workflow:
    1. Fetch data
    2. Calculate indicators
    3. Detect signals
    4. AI Analysis (optional)

    Each step can be customized, skipped, or wrapped with middleware.

    Example:
        >>> pipeline = AnalysisPipeline(
        ...     symbol='SPY',
        ...     interval='1h',
        ...     enable_ai=True,
        ... )
        >>> result = pipeline.run()
        >>> print(result.summary)
        >>> if result.ai_result:
        ...     print(result.ai_result.trading_recommendation)
    """

    def __init__(
        self,
        symbol: str,
        interval: str = "1d",
        period: Optional[str] = None,
        config: Optional[SignalConfig] = None,
        data_provider: Optional[DataProvider] = None,
        indicator_factory: str = "comprehensive",
        detector_factory: str = "comprehensive",
        quality_min: float = 0.3,
        skip_indicators: bool = False,
        skip_signals: bool = False,
        enable_ai: bool = False,
        enable_progress: bool = True,
    ):
        """
        Initialize analysis pipeline.

        Args:
            symbol: Stock symbol.
            interval: Timeframe (default: '1d').
            period: Data period (default: auto).
            config: Custom SignalConfig.
            data_provider: Custom data provider.
            indicator_factory: Indicator suite name.
            detector_factory: Detector suite name.
            quality_min: Minimum signal quality.
            skip_indicators: Skip indicator calculation.
            skip_signals: Skip signal detection.
            enable_ai: Enable AI-powered analysis (default: False).
            enable_progress: Show progress during execution.
        """
        self.symbol = symbol
        self.interval = interval
        self.enable_progress = enable_progress
        self.enable_ai = enable_ai

        # Create analyzer with all options
        self.analyzer = MultiTimeframeAnalyzer(
            symbol=symbol,
            interval=interval,
            period=period,
            config=config,
            data_provider=data_provider or YFinanceProvider(),
            indicator_factory=indicator_factory,
            detector_factory=detector_factory,
            quality_min=quality_min,
        )

        self.skip_indicators = skip_indicators
        self.skip_signals = skip_signals

        # AI analyzer (lazy loaded)
        self._ai_analyzer = None

        # Execution history
        self.steps: List[StepResult] = []

        # Results
        self._ai_result = None

    def _get_ai_analyzer(self):
        """Lazy load AI analyzer."""
        if self._ai_analyzer is None and self.enable_ai:
            try:
                from analyzer.ai_integration import create_ai_analyzer
                self._ai_analyzer = create_ai_analyzer()
            except ImportError as e:
                logger.warning(f"AI integration not available: {e}")
                self._ai_analyzer = None
            except Exception as e:
                logger.warning(f"Failed to initialize AI analyzer: {e}")
                self._ai_analyzer = None
        return self._ai_analyzer

    def run(self) -> EnhancedAnalysisResult:
        """
        Execute complete analysis pipeline.

        Returns:
            EnhancedAnalysisResult with all analysis data and optional AI insights.

        Raises:
            AnalyzerError: If any step fails (unless configured to continue).
        """
        logger.info(f"Starting analysis pipeline: {self.symbol} [{self.interval}]")
        if self.enable_ai:
            logger.info("AI analysis enabled")

        try:
            # Step 1: Fetch data
            self._step_fetch_data()

            # Step 2: Calculate indicators (optional)
            if not self.skip_indicators:
                self._step_calculate_indicators()

            # Step 3: Detect signals (optional)
            if not self.skip_signals:
                self._step_detect_signals()

            # Step 4: AI Analysis (optional)
            if self.enable_ai:
                self._step_ai_analysis()

            # Complete
            base_result = self.analyzer.result
            if base_result is None:
                raise AnalyzerError("No result generated")

            # Build enhanced result
            enhanced = EnhancedAnalysisResult(
                base_result=base_result,
                ai_result=self._ai_result,
                pipeline_summary=self.get_summary(),
            )

            self._log_summary(base_result)
            return enhanced

        except AnalyzerError:
            raise
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise AnalyzerError(f"Pipeline error: {str(e)}") from e

    async def run_async(self) -> EnhancedAnalysisResult:
        """
        Execute analysis pipeline asynchronously.

        Uses async data fetching for non-blocking I/O, then runs
        CPU-bound indicator/signal calculations synchronously.

        Returns:
            EnhancedAnalysisResult with all analysis data.

        Example:
            >>> pipeline = AnalysisPipeline('SPY', interval='1h')
            >>> result = await pipeline.run_async()
        """
        logger.info(f"Starting async pipeline: {self.symbol} [{self.interval}]")

        try:
            # Step 1: Async data fetch (I/O-bound)
            await self._step_fetch_data_async()

            # Steps 2-4: Run sync (CPU-bound work)
            if not self.skip_indicators:
                self._step_calculate_indicators()

            if not self.skip_signals:
                self._step_detect_signals()

            if self.enable_ai:
                self._step_ai_analysis()

            # Build result
            base_result = self.analyzer.result
            if base_result is None:
                raise AnalyzerError("No result generated")

            enhanced = EnhancedAnalysisResult(
                base_result=base_result,
                ai_result=self._ai_result,
                pipeline_summary=self.get_summary(),
            )

            self._log_summary(base_result)
            return enhanced

        except AnalyzerError:
            raise
        except Exception as e:
            logger.error(f"Async pipeline failed: {str(e)}")
            raise AnalyzerError(f"Pipeline error: {str(e)}") from e

    async def _step_fetch_data_async(self) -> StepResult:
        """Execute async fetch data step."""
        step_name = "Fetch Data (async)"
        self._log_step_start(step_name)
        start_time = time.time()

        try:
            # Use provider's async method
            data = await self.analyzer.data_provider.fetch_async(
                symbol=self.analyzer.symbol,
                interval=self.analyzer.interval,
                period=self.analyzer.period,
            )

            # Store in analyzer and validate
            self.analyzer._data = self.analyzer.validator.process(data)

            duration = (time.time() - start_time) * 1000
            result = StepResult(
                name=step_name,
                success=True,
                data=self.analyzer._data,
                duration_ms=duration,
                message=f"{len(self.analyzer._data)} bars fetched",
            )
            self.steps.append(result)
            self._log_step_result(result)
            return result

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = StepResult(
                name=step_name,
                success=False,
                data=None,
                error=str(e),
                duration_ms=duration,
            )
            self.steps.append(result)
            self._log_step_result(result)
            raise

    @step_handler("Fetch Data", message_fn=lambda d: f"{len(d)} bars fetched")
    def _step_fetch_data(self) -> pd.DataFrame:
        """Execute fetch data step."""
        return self.analyzer.fetch_data()

    @step_handler("Calculate Indicators", message_fn=lambda d: f"{len(d.columns)} columns")
    def _step_calculate_indicators(self) -> pd.DataFrame:
        """Execute indicator calculation step."""
        return self.analyzer.calculate_indicators()

    @step_handler("Detect Signals", message_fn=lambda r: f"{r.signal_count} signals detected")
    def _step_detect_signals(self):
        """Execute signal detection step."""
        return self.analyzer.detect_signals()

    @step_handler("AI Analysis", fatal=False)
    def _step_ai_analysis(self):
        """
        Execute AI analysis step.

        Non-fatal: continues pipeline even if AI fails.
        """
        ai_analyzer = self._get_ai_analyzer()

        if ai_analyzer is None:
            return None  # Will show as success with no data

        # Guard clause: need base result
        base_result = self.analyzer.result
        if base_result is None:
            raise AnalyzerError("No base result for AI analysis")

        # Convert signals to dicts for AI (Law of Demeter)
        signals_list = self._signals_to_dicts(base_result.signals.signals)

        # Run AI analysis
        self._ai_result = ai_analyzer.analyze(
            signals=signals_list,
            indicators=base_result.indicators,
            data=base_result.data,
            symbol=self.symbol,
        )

        return self._ai_result

    def _signals_to_dicts(self, signals) -> List[Dict[str, Any]]:
        """Convert signal objects to dictionaries for AI analysis."""
        return [
            {
                "name": s.name,
                "category": s.category,
                "strength": s.strength,
                "confidence": s.confidence,
                "description": s.description,
            }
            for s in signals
        ]

    def _log_step_start(self, step_name: str) -> None:
        """Log step start."""
        if self.enable_progress:
            logger.info(f"→ {step_name}...")

    def _log_step_result(self, result: StepResult) -> None:
        """Log step result."""
        if self.enable_progress:
            logger.info(f"  {result}")

    def _log_summary(self, result: AnalysisResult) -> None:
        """Log pipeline summary."""
        logger.info(f"Pipeline complete: {result}")
        logger.info("Steps:")
        for step in self.steps:
            status = "✓" if step.success else "✗"
            logger.info(f"  {status} {step.name} ({step.duration_ms:.0f}ms)")

    def get_summary(self) -> dict:
        """
        Get pipeline execution summary.

        Returns:
            Dictionary with execution stats.
        """
        successful = sum(1 for s in self.steps if s.success)
        total_time = sum(s.duration_ms for s in self.steps)

        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "steps_total": len(self.steps),
            "steps_successful": successful,
            "steps_failed": len(self.steps) - successful,
            "total_time_ms": total_time,
            "ai_enabled": self.enable_ai,
            "ai_available": self._ai_analyzer is not None if self.enable_ai else False,
            "steps": [
                {
                    "name": s.name,
                    "success": s.success,
                    "duration_ms": s.duration_ms,
                    "error": s.error,
                }
                for s in self.steps
            ],
        }

    def __str__(self) -> str:
        """Return string representation."""
        ai_str = " +AI" if self.enable_ai else ""
        return f"AnalysisPipeline({self.symbol}[{self.interval}]{ai_str})"


# ============ CONVENIENCE FUNCTIONS ============


def analyze_symbol(
    symbol: str,
    interval: str = "1d",
    period: Optional[str] = None,
    enable_ai: bool = False,
    show_progress: bool = True,
) -> EnhancedAnalysisResult:
    """
    Quick analysis of a symbol.

    Args:
        symbol: Stock symbol.
        interval: Timeframe (default: '1d').
        period: Data period (default: auto).
        enable_ai: Enable AI analysis (default: False).
        show_progress: Show progress output.

    Returns:
        EnhancedAnalysisResult with all analysis.

    Example:
        >>> result = analyze_symbol('SPY', interval='1h', enable_ai=True)
        >>> print(result.summary)
        >>> if result.ai_result:
        ...     print(result.ai_result.trading_recommendation)
    """
    pipeline = AnalysisPipeline(
        symbol=symbol,
        interval=interval,
        period=period,
        enable_ai=enable_ai,
        enable_progress=show_progress,
    )
    return pipeline.run()


def analyze_multiple(
    symbols: List[str],
    interval: str = "1d",
    enable_ai: bool = False,
    show_progress: bool = True,
    max_workers: int = 4,
    parallel: bool = True,
) -> Dict[str, Optional[EnhancedAnalysisResult]]:
    """
    Analyze multiple symbols with optional parallel execution.

    Uses ThreadPoolExecutor for concurrent I/O-bound data fetching,
    significantly reducing total execution time for multiple symbols.

    Args:
        symbols: List of stock symbols.
        interval: Timeframe for all (default: '1d').
        enable_ai: Enable AI analysis (default: False).
        show_progress: Show progress output.
        max_workers: Maximum concurrent analyses (default: 4).
        parallel: Use parallel execution (default: True).

    Returns:
        Dictionary mapping symbol to EnhancedAnalysisResult (or None on error).

    Example:
        >>> results = analyze_multiple(['SPY', 'QQQ', 'IWM'], parallel=True)
        >>> for symbol, result in results.items():
        ...     if result:
        ...         print(f"{symbol}: {result.signals.signal_count} signals")
    """
    if not symbols:
        return {}

    # Guard: single symbol doesn't need parallelization
    if len(symbols) == 1 or not parallel:
        return _analyze_sequential(symbols, interval, enable_ai, show_progress)

    return _analyze_parallel(symbols, interval, enable_ai, show_progress, max_workers)


def _analyze_sequential(
    symbols: List[str],
    interval: str,
    enable_ai: bool,
    show_progress: bool,
) -> Dict[str, Optional[EnhancedAnalysisResult]]:
    """Analyze symbols sequentially (fallback mode)."""
    results = {}
    for symbol in symbols:
        try:
            logger.info(f"Analyzing {symbol}...")
            results[symbol] = analyze_symbol(
                symbol, interval, enable_ai=enable_ai, show_progress=show_progress
            )
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {str(e)}")
            results[symbol] = None
    return results


def _analyze_parallel(
    symbols: List[str],
    interval: str,
    enable_ai: bool,
    show_progress: bool,
    max_workers: int,
) -> Dict[str, Optional[EnhancedAnalysisResult]]:
    """Analyze symbols in parallel using ThreadPoolExecutor."""
    results: Dict[str, Optional[EnhancedAnalysisResult]] = {}

    def _analyze_one(symbol: str) -> tuple[str, Optional[EnhancedAnalysisResult]]:
        """Worker function for parallel execution."""
        try:
            result = analyze_symbol(
                symbol, interval, enable_ai=enable_ai, show_progress=False
            )
            return (symbol, result)
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {str(e)}")
            return (symbol, None)

    logger.info(f"Starting parallel analysis of {len(symbols)} symbols (workers: {max_workers})")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_analyze_one, s): s for s in symbols}

        for future in as_completed(futures):
            symbol, result = future.result()
            results[symbol] = result
            if show_progress:
                status = "✓" if result else "✗"
                logger.info(f"  {status} {symbol}")

    duration = time.time() - start_time
    success_count = sum(1 for r in results.values() if r is not None)
    logger.info(
        f"Parallel analysis complete: {success_count}/{len(symbols)} "
        f"in {duration:.1f}s"
    )

    return results


def analyze_with_ai(
    symbol: str,
    interval: str = "1d",
    period: Optional[str] = None,
) -> EnhancedAnalysisResult:
    """
    Convenience function for AI-enabled analysis.

    Args:
        symbol: Stock symbol.
        interval: Timeframe.
        period: Data period.

    Returns:
        EnhancedAnalysisResult with AI insights.
    """
    return analyze_symbol(symbol, interval, period, enable_ai=True)


def quick_analyze(
    symbol: str,
    interval: str = "1d",
) -> Dict[str, Any]:
    """
    Fast, minimal analysis returning essential data only.

    Optimized for speed - skips optional processing and returns
    a simplified dictionary instead of full result objects.

    Args:
        symbol: Stock symbol.
        interval: Timeframe.

    Returns:
        Dictionary with signal count, direction, and key indicators.

    Example:
        >>> info = quick_analyze('SPY')
        >>> print(f"Direction: {info['direction']}, Signals: {info['signal_count']}")
    """
    try:
        result = (
            PipelineBuilder(symbol)
            .interval(interval)
            .silent()
            .run()
        )

        # Extract essential info
        signals = result.base_result.signals
        indicators = result.base_result.indicators

        # Determine overall direction
        if signals.bullish_count > signals.bearish_count:
            direction = "BULLISH"
        elif signals.bearish_count > signals.bullish_count:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        return {
            "symbol": symbol,
            "interval": interval,
            "direction": direction,
            "signal_count": signals.signal_count,
            "bullish": signals.bullish_count,
            "bearish": signals.bearish_count,
            "price": indicators.get("Current_Price"),
            "rsi": indicators.get("RSI"),
            "success": True,
        }

    except Exception as e:
        logger.error(f"Quick analysis failed for {symbol}: {str(e)}")
        return {
            "symbol": symbol,
            "interval": interval,
            "direction": "UNKNOWN",
            "signal_count": 0,
            "success": False,
            "error": str(e),
        }


# ============ ANALYSIS CACHE ============


class AnalysisCache:
    """
    Simple in-memory cache for analysis results.

    Useful for avoiding repeated API calls when analyzing
    the same symbol/interval combination multiple times.

    Example:
        >>> cache = AnalysisCache(ttl_seconds=300)  # 5 min TTL
        >>> result = cache.get_or_analyze('SPY', '1h')
        >>> result2 = cache.get_or_analyze('SPY', '1h')  # Returns cached
    """

    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cached entries (default: 5 min).
            max_size: Maximum number of cached entries.
        """
        self._cache: Dict[str, tuple[float, EnhancedAnalysisResult]] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size

    def _cache_key(self, symbol: str, interval: str, enable_ai: bool) -> str:
        """Generate cache key."""
        return f"{symbol.upper()}:{interval}:{'ai' if enable_ai else 'basic'}"

    def get(
        self, symbol: str, interval: str, enable_ai: bool = False
    ) -> Optional[EnhancedAnalysisResult]:
        """Get cached result if valid."""
        key = self._cache_key(symbol, interval, enable_ai)
        if key not in self._cache:
            return None

        timestamp, result = self._cache[key]
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None

        return result

    def set(
        self,
        symbol: str,
        interval: str,
        result: EnhancedAnalysisResult,
        enable_ai: bool = False,
    ) -> None:
        """Cache a result."""
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]

        key = self._cache_key(symbol, interval, enable_ai)
        self._cache[key] = (time.time(), result)

    def get_or_analyze(
        self,
        symbol: str,
        interval: str = "1d",
        enable_ai: bool = False,
    ) -> EnhancedAnalysisResult:
        """Get from cache or run analysis."""
        cached = self.get(symbol, interval, enable_ai)
        if cached is not None:
            logger.debug(f"Cache hit: {symbol}[{interval}]")
            return cached

        result = analyze_symbol(symbol, interval, enable_ai=enable_ai)
        self.set(symbol, interval, result, enable_ai)
        return result

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "entries": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl,
        }


# Global cache instance (optional convenience)
_global_cache: Optional[AnalysisCache] = None


def get_cache(ttl_seconds: int = 300) -> AnalysisCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = AnalysisCache(ttl_seconds=ttl_seconds)
    return _global_cache


# ============ ASYNC CONVENIENCE FUNCTIONS ============


async def analyze_symbol_async(
    symbol: str,
    interval: str = "1d",
    period: Optional[str] = None,
    enable_ai: bool = False,
) -> EnhancedAnalysisResult:
    """
    Async analysis of a single symbol.

    Uses non-blocking I/O for data fetching.

    Args:
        symbol: Stock symbol.
        interval: Timeframe (default: '1d').
        period: Data period (default: auto).
        enable_ai: Enable AI analysis.

    Returns:
        EnhancedAnalysisResult with analysis data.

    Example:
        >>> result = await analyze_symbol_async('SPY', interval='1h')
        >>> print(result.summary)
    """
    pipeline = AnalysisPipeline(
        symbol=symbol,
        interval=interval,
        period=period,
        enable_ai=enable_ai,
        enable_progress=False,
    )
    return await pipeline.run_async()


async def analyze_multiple_async(
    symbols: List[str],
    interval: str = "1d",
    enable_ai: bool = False,
) -> Dict[str, Optional[EnhancedAnalysisResult]]:
    """
    Analyze multiple symbols concurrently using asyncio.

    More efficient than ThreadPoolExecutor for I/O-bound operations.
    All symbols are fetched and analyzed concurrently.

    Args:
        symbols: List of stock symbols.
        interval: Timeframe for all symbols.
        enable_ai: Enable AI analysis.

    Returns:
        Dict mapping symbol to EnhancedAnalysisResult (or None on error).

    Example:
        >>> results = await analyze_multiple_async(['SPY', 'QQQ', 'IWM'])
        >>> for symbol, result in results.items():
        ...     if result:
        ...         print(f"{symbol}: {result.signals.signal_count} signals")
    """
    if not symbols:
        return {}

    async def analyze_one(symbol: str) -> Tuple[str, Optional[EnhancedAnalysisResult]]:
        try:
            result = await analyze_symbol_async(symbol, interval, enable_ai=enable_ai)
            return (symbol, result)
        except Exception as e:
            logger.error(f"Async analysis failed for {symbol}: {e}")
            return (symbol, None)

    logger.info(f"Starting async analysis of {len(symbols)} symbols")
    start_time = time.time()

    results = await asyncio.gather(*[analyze_one(s) for s in symbols])
    result_dict = dict(results)

    duration = time.time() - start_time
    success_count = sum(1 for r in result_dict.values() if r is not None)
    logger.info(f"Async analysis complete: {success_count}/{len(symbols)} in {duration:.1f}s")

    return result_dict


async def analyze_with_ai_async(
    symbol: str,
    interval: str = "1d",
    period: Optional[str] = None,
) -> EnhancedAnalysisResult:
    """
    Async AI-enabled analysis.

    Args:
        symbol: Stock symbol.
        interval: Timeframe.
        period: Data period.

    Returns:
        EnhancedAnalysisResult with AI insights.
    """
    return await analyze_symbol_async(symbol, interval, period, enable_ai=True)


def run_async(coro):
    """
    Helper to run async code from a synchronous context.

    This function is ONLY for use in synchronous code. If you are already
    in an async context, use `await` directly instead.

    Args:
        coro: Coroutine to run.

    Returns:
        Result of the coroutine.

    Raises:
        RuntimeError: If called from within an async context (running event loop).

    Example:
        # Correct: from sync context
        >>> result = run_async(analyze_symbol_async('SPY'))

        # Incorrect: from async context - use await instead
        >>> async def my_func():
        ...     result = await analyze_symbol_async('SPY')  # Correct
        ...     # result = run_async(analyze_symbol_async('SPY'))  # Wrong!
    """
    try:
        asyncio.get_running_loop()
        # If we get here, there's already a running loop - raise error
        raise RuntimeError(
            "run_async() cannot be called from an async context. "
            "Use 'await' directly instead: await analyze_symbol_async(...)"
        )
    except RuntimeError as e:
        # Check if this is our error or the "no running loop" error
        if "cannot be called from an async context" in str(e):
            raise
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)
