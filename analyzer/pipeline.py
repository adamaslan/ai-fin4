"""
Analysis pipeline.

Defines the complete analysis workflow with middleware-like composition.
Each step can be skipped or customized. Optionally includes AI-powered
analysis for signal summarization, recommendations, and risk assessment.
"""

from __future__ import annotations

from typing import Optional, List, Any, Dict
from dataclasses import dataclass, field
import pandas as pd
from logging_config import get_logger
from analyzer.core import MultiTimeframeAnalyzer, AnalysisResult
from config import SignalConfig
from data.provider import DataProvider, YFinanceProvider
from exceptions import AnalyzerError

logger = get_logger()


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

    def _step_fetch_data(self) -> StepResult:
        """Execute fetch data step."""
        import time

        step_name = "Fetch Data"
        self._log_step_start(step_name)

        start_time = time.time()

        try:
            data = self.analyzer.fetch_data()

            result = StepResult(
                name=step_name,
                success=True,
                data=data,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"{len(data)} bars fetched",
            )

            self.steps.append(result)
            self._log_step_result(result)
            return result

        except Exception as e:
            result = StepResult(
                name=step_name,
                success=False,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

            self.steps.append(result)
            self._log_step_result(result)
            raise

    def _step_calculate_indicators(self) -> StepResult:
        """Execute indicator calculation step."""
        import time

        step_name = "Calculate Indicators"
        self._log_step_start(step_name)

        start_time = time.time()

        try:
            data = self.analyzer.calculate_indicators()

            result = StepResult(
                name=step_name,
                success=True,
                data=data,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"{len(data.columns)} columns (including indicators)",
            )

            self.steps.append(result)
            self._log_step_result(result)
            return result

        except Exception as e:
            result = StepResult(
                name=step_name,
                success=False,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

            self.steps.append(result)
            self._log_step_result(result)
            raise

    def _step_detect_signals(self) -> StepResult:
        """Execute signal detection step."""
        import time

        step_name = "Detect Signals"
        self._log_step_start(step_name)

        start_time = time.time()

        try:
            signal_result = self.analyzer.detect_signals()

            result = StepResult(
                name=step_name,
                success=True,
                data=signal_result,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"{signal_result.signal_count} signals detected",
            )

            self.steps.append(result)
            self._log_step_result(result)
            return result

        except Exception as e:
            result = StepResult(
                name=step_name,
                success=False,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

            self.steps.append(result)
            self._log_step_result(result)
            raise

    def _step_ai_analysis(self) -> StepResult:
        """Execute AI analysis step."""
        import time

        step_name = "AI Analysis"
        self._log_step_start(step_name)

        start_time = time.time()

        try:
            ai_analyzer = self._get_ai_analyzer()

            if ai_analyzer is None:
                result = StepResult(
                    name=step_name,
                    success=True,
                    data=None,
                    duration_ms=(time.time() - start_time) * 1000,
                    message="AI analyzer not available (skipped)",
                )
                self.steps.append(result)
                self._log_step_result(result)
                return result

            # Get analysis result
            base_result = self.analyzer.result
            if base_result is None:
                raise AnalyzerError("No base result for AI analysis")

            # Convert signals to dicts for AI
            signals_list = [
                {
                    "name": s.name,
                    "category": s.category,
                    "strength": s.strength,
                    "confidence": s.confidence,
                    "description": s.description,
                }
                for s in base_result.signals.signals
            ]

            # Run AI analysis
            self._ai_result = ai_analyzer.analyze(
                signals=signals_list,
                indicators=base_result.indicators,
                data=base_result.data,
                symbol=self.symbol,
            )

            result = StepResult(
                name=step_name,
                success=True,
                data=self._ai_result,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"AI analysis complete (provider: {ai_analyzer.config.primary_provider.value})",
            )

            self.steps.append(result)
            self._log_step_result(result)
            return result

        except Exception as e:
            logger.warning(f"AI analysis failed (non-fatal): {str(e)}")
            result = StepResult(
                name=step_name,
                success=False,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
                message="AI analysis failed (continuing without AI)",
            )

            self.steps.append(result)
            self._log_step_result(result)
            # Don't raise - AI failure is non-fatal
            return result

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
) -> dict:
    """
    Analyze multiple symbols.

    Args:
        symbols: List of stock symbols.
        interval: Timeframe for all (default: '1d').
        enable_ai: Enable AI analysis (default: False).
        show_progress: Show progress output.

    Returns:
        Dictionary mapping symbol to EnhancedAnalysisResult.

    Example:
        >>> results = analyze_multiple(['SPY', 'QQQ', 'IWM'], enable_ai=True)
        >>> for symbol, result in results.items():
        ...     print(f"{symbol}: {result.signals.signal_count} signals")
    """
    results = {}

    for symbol in symbols:
        try:
            logger.info(f"Analyzing {symbol}...")
            results[symbol] = analyze_symbol(
                symbol,
                interval,
                enable_ai=enable_ai,
                show_progress=show_progress,
            )
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {str(e)}")
            results[symbol] = None

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
