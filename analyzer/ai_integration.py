"""
AI Integration for Analysis Pipeline.

Integrates AI-powered analysis from ai1.py and ai2.py into the
analysis pipeline with clean interfaces.

This module wraps the 25 AI themes into a unified AIAnalyzer class
that can be optionally enabled in the AnalysisPipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import pandas as pd
from logging_config import get_logger

# Import AI modules
from ai1 import (
    AIConfig,
    SignalSummarizer,
    ConfluenceAnalyzer,
    ContextAwareFilter,
    TradingRecommender,
    MultiTimeframeSynthesizer,
    StockRecommender,
    RiskAssessment,
    OpportunityIdentifier,
)
from ai2 import (
    IndicatorAlerts,
    IndicatorHealthScorer,
    MissingSignalDetector,
    DivergenceDetector,
    PeriodOptimizer,
    StrategyGenerator,
    PositionSizer,
    EntryExitOptimizer,
    VolatilityRegimeDetector,
    SentimentWeighter,
    AnomalyDetector,
    LearningSystem,
)

logger = get_logger()


# ============ AI ANALYSIS RESULT ============


@dataclass
class AIAnalysisResult:
    """
    Result from AI-powered analysis.

    Contains all AI-generated insights, recommendations, and alerts.
    """

    # Core analysis
    signal_summary: str
    """AI-generated summary of signals (Theme 1)."""

    confluence: Dict[str, Any]
    """Signal confluence analysis (Theme 2)."""

    trading_recommendation: Dict[str, Any]
    """Trading recommendation with entry/exit (Theme 4)."""

    risk_assessment: Dict[str, Any]
    """Risk factors and mitigations (Theme 7)."""

    # Additional insights
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    """Indicator-level alerts (Theme 11)."""

    opportunities: List[Dict[str, Any]] = field(default_factory=list)
    """Identified opportunities (Theme 8)."""

    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    """Detected anomalies (Theme 24)."""

    volatility_regime: Dict[str, Any] = field(default_factory=dict)
    """Current volatility regime (Theme 22)."""

    strategy_suggestion: Dict[str, Any] = field(default_factory=dict)
    """Suggested strategy based on signals (Theme 16)."""

    # Metadata
    ai_available: bool = True
    """Whether AI provider was available."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "signal_summary": self.signal_summary,
            "confluence": self.confluence,
            "trading_recommendation": self.trading_recommendation,
            "risk_assessment": self.risk_assessment,
            "alerts": self.alerts,
            "opportunities": self.opportunities,
            "anomalies": self.anomalies,
            "volatility_regime": self.volatility_regime,
            "strategy_suggestion": self.strategy_suggestion,
            "ai_available": self.ai_available,
        }


# ============ AI ANALYZER ============


class AIAnalyzer:
    """
    Unified AI analysis engine.

    Combines all 25 AI themes into a single analyzer that can be
    plugged into the analysis pipeline.

    Example:
        >>> ai = AIAnalyzer()
        >>> if ai.is_available:
        ...     result = ai.analyze(signals, indicators, data)
        ...     print(result.signal_summary)
    """

    def __init__(self):
        """Initialize AI analyzer with all components."""
        self.config = AIConfig()

        # Core analyzers (Themes 1-10)
        self.summarizer = SignalSummarizer(self.config)
        self.confluence = ConfluenceAnalyzer(self.config)
        self.context_filter = ContextAwareFilter(self.config)
        self.recommender = TradingRecommender(self.config)
        self.mtf_synthesizer = MultiTimeframeSynthesizer()
        self.stock_recommender = StockRecommender(self.config)
        self.risk_assessor = RiskAssessment()
        self.opportunity_finder = OpportunityIdentifier()

        # Advanced analyzers (Themes 11-25)
        self.alert_generator = IndicatorAlerts()
        self.health_scorer = IndicatorHealthScorer()
        self.missing_detector = MissingSignalDetector()
        self.divergence_detector = DivergenceDetector()
        self.period_optimizer = PeriodOptimizer()
        self.strategy_generator = StrategyGenerator()
        self.position_sizer = PositionSizer()
        self.entry_optimizer = EntryExitOptimizer()
        self.volatility_detector = VolatilityRegimeDetector()
        self.sentiment_weighter = SentimentWeighter()
        self.anomaly_detector = AnomalyDetector()
        self.learning_system = LearningSystem()

        logger.info(f"AIAnalyzer initialized (provider: {self.config.primary_provider.value})")

    @property
    def is_available(self) -> bool:
        """Check if AI provider is available."""
        return self.config.is_available()

    def analyze(
        self,
        signals: List[Dict[str, Any]],
        indicators: Dict[str, Any],
        data: Optional[pd.DataFrame] = None,
        symbol: str = "UNKNOWN",
    ) -> AIAnalysisResult:
        """
        Perform complete AI analysis.

        Args:
            signals: List of detected signals (as dicts).
            indicators: Current indicator values.
            data: Optional price history DataFrame.
            symbol: Stock symbol for context.

        Returns:
            AIAnalysisResult with all AI insights.
        """
        logger.info(f"Running AI analysis for {symbol}")

        # Theme 1: Signal Summary
        summary = self._safe_call(
            lambda: self.summarizer.summarize(signals, indicators),
            default="AI summary unavailable",
            name="SignalSummarizer"
        )

        # Theme 2: Confluence Analysis
        confluence = self._safe_call(
            lambda: self.confluence.analyze_confluence(signals),
            default={"confluence_count": 0, "confluences": []},
            name="ConfluenceAnalyzer"
        )

        # Theme 3: Context-Aware Filtering
        filtered_signals = self._safe_call(
            lambda: self.context_filter.filter_by_regime(signals, indicators),
            default=signals,
            name="ContextAwareFilter"
        )

        # Theme 4: Trading Recommendation
        recommendation = self._safe_call(
            lambda: self.recommender.generate_recommendation(filtered_signals, indicators),
            default={"recommendation": "HOLD", "reason": "AI unavailable"},
            name="TradingRecommender"
        )

        # Theme 7: Risk Assessment
        risk = self._safe_call(
            lambda: self.risk_assessor.assess(signals, indicators),
            default={"overall_risk_level": "UNKNOWN", "identified_risks": []},
            name="RiskAssessment"
        )

        # Theme 8: Opportunity Identification
        opportunities = self._safe_call(
            lambda: self.opportunity_finder.identify(signals, indicators),
            default=[],
            name="OpportunityIdentifier"
        )

        # Theme 11: Indicator Alerts
        alerts = self._safe_call(
            lambda: self.alert_generator.generate_alerts(indicators, symbol),
            default=[],
            name="IndicatorAlerts"
        )

        # Theme 16: Strategy Generation
        signal_categories = [s.get("category", "") for s in signals]
        strategy = self._safe_call(
            lambda: self.strategy_generator.generate_strategy(signal_categories),
            default={"message": "No strategy matched"},
            name="StrategyGenerator"
        )

        # Theme 22: Volatility Regime
        hv = indicators.get("HV_30d", 0.20)
        atr = indicators.get("ATR", 0)
        price = indicators.get("Current_Price", 100)
        atr_pct = (atr / price * 100) if price else 0

        volatility = self._safe_call(
            lambda: self.volatility_detector.detect_regime(hv, atr_pct),
            default={"regime": "UNKNOWN"},
            name="VolatilityRegimeDetector"
        )

        # Theme 24: Anomaly Detection
        anomalies = self._safe_call(
            lambda: self.anomaly_detector.detect_anomalies(indicators, data),
            default=[],
            name="AnomalyDetector"
        )

        return AIAnalysisResult(
            signal_summary=summary,
            confluence=confluence,
            trading_recommendation=recommendation,
            risk_assessment=risk,
            alerts=alerts,
            opportunities=opportunities,
            anomalies=anomalies,
            volatility_regime=volatility,
            strategy_suggestion=strategy,
            ai_available=self.is_available,
        )

    def _safe_call(self, func, default, name: str):
        """Safely call a function with error handling."""
        try:
            return func()
        except Exception as e:
            logger.warning(f"{name} failed: {str(e)}")
            return default

    def analyze_quick(
        self,
        signals: List[Dict[str, Any]],
        indicators: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Quick AI analysis with essential insights only.

        Faster than full analyze() - only runs core themes.

        Args:
            signals: Detected signals.
            indicators: Current indicators.

        Returns:
            Dict with summary, recommendation, and risk.
        """
        summary = self._safe_call(
            lambda: self.summarizer.summarize(signals, indicators),
            default="Summary unavailable",
            name="SignalSummarizer"
        )

        recommendation = self._safe_call(
            lambda: self.recommender.generate_recommendation(signals, indicators),
            default={"recommendation": "HOLD"},
            name="TradingRecommender"
        )

        risk = self._safe_call(
            lambda: self.risk_assessor.assess(signals, indicators),
            default={"overall_risk_level": "UNKNOWN"},
            name="RiskAssessment"
        )

        return {
            "summary": summary,
            "recommendation": recommendation,
            "risk": risk,
        }


# ============ CONVENIENCE FUNCTION ============


def create_ai_analyzer() -> Optional[AIAnalyzer]:
    """
    Create an AIAnalyzer if AI is available.

    Returns:
        AIAnalyzer instance or None if no AI provider configured.
    """
    try:
        analyzer = AIAnalyzer()
        if analyzer.is_available:
            return analyzer
        logger.info("AI analyzer created but no provider available")
        return analyzer  # Return anyway, will use fallbacks
    except Exception as e:
        logger.warning(f"Failed to create AI analyzer: {str(e)}")
        return None
