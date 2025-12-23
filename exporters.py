# verify file names
"""
Export functionality for analysis results.

Provides JSON, Markdown, and CSV export options with full customization.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import json
import csv
import pandas as pd
from analyzer.core import AnalysisResult
from signals.base import Signal
from logging_config import get_logger

logger = get_logger()


# ============ EXPORT RESULT ============


class ExportResult:
    """Result from an export operation."""

    def __init__(self, filepath: Path, format: str, bytes_written: int):
        """
        Initialize export result.

        Args:
            filepath: Path where file was written.
            format: Export format (json, markdown, csv).
            bytes_written: Number of bytes written.
        """
        self.filepath = filepath
        self.format = format
        self.bytes_written = bytes_written
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        """Return formatted result."""
        return f"{self.format.upper()} → {self.filepath} ({self.bytes_written} bytes)"


# ============ EXPORTER BASE CLASS ============


class Exporter(ABC):
    """Abstract base class for result exporters."""

    @abstractmethod
    def export(self, result: AnalysisResult, filepath: Path) -> ExportResult:
        """
        Export analysis result to file.

        Args:
            result: Analysis result to export.
            filepath: Path to write file.

        Returns:
            ExportResult with details.

        Raises:
            Exception: If export fails.
        """
        pass


# ============ JSON EXPORTER ============


class JSONExporter(Exporter):
    """
    Exports analysis results to JSON format.

    Includes all data: metadata, indicators, signals, statistics.
    """

    def export(self, result: AnalysisResult, filepath: Path) -> ExportResult:
        """
        Export to JSON.

        Args:
            result: Analysis result.
            filepath: Output path.

        Returns:
            ExportResult.
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": {
                "symbol": result.symbol,
                "interval": result.config.interval,
                "interval_name": result.config.name,
                "timestamp": datetime.now().isoformat(),
                "bars_analyzed": len(result.data),
                "date_range": {
                    "start": result.data.index[0].isoformat(),
                    "end": result.data.index[-1].isoformat(),
                },
            },
            "configuration": result.config.to_dict(),
            "current_price": {
                "open": float(result.data.iloc[-1]["Open"]),
                "high": float(result.data.iloc[-1]["High"]),
                "low": float(result.data.iloc[-1]["Low"]),
                "close": float(result.data.iloc[-1]["Close"]),
                "volume": int(result.data.iloc[-1]["Volume"]),
            },
            "signals": {
                "total": result.signals.signal_count,
                "bullish": result.signals.bullish_count,
                "bearish": result.signals.bearish_count,
                "neutral": result.signals.neutral_count,
                "by_category": {
                    cat: len(sigs)
                    for cat, sigs in result.signals.by_category.items()
                },
                "list": [s.to_dict() for s in result.signals.signals],
            },
            "indicators": self._extract_indicators(result.data),
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        bytes_written = filepath.stat().st_size
        logger.info(f"Exported JSON: {filepath}")

        return ExportResult(filepath, "json", bytes_written)

    @staticmethod
    def _extract_indicators(data: pd.DataFrame) -> dict:
        """Extract indicator columns from data."""
        indicators = {}

        # Get latest values for all indicator columns
        for col in data.columns:
            if col not in ["Open", "High", "Low", "Close", "Volume"]:
                try:
                    value = float(data.iloc[-1][col])
                    indicators[col] = value
                except (ValueError, TypeError):
                    pass

        return indicators


# ============ MARKDOWN EXPORTER ============


class MarkdownExporter(Exporter):
    """
    Exports analysis results to Markdown format.

    Creates a human-readable report with sections for signals,
    indicators, and recommendations.
    """

    def export(self, result: AnalysisResult, filepath: Path) -> ExportResult:
        """
        Export to Markdown.

        Args:
            result: Analysis result.
            filepath: Output path.

        Returns:
            ExportResult.
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        content = self._generate_report(result)

        with open(filepath, "w") as f:
            f.write(content)

        bytes_written = filepath.stat().st_size
        logger.info(f"Exported Markdown: {filepath}")

        return ExportResult(filepath, "markdown", bytes_written)

    def _generate_report(self, result: AnalysisResult) -> str:
        """Generate markdown report."""
        lines = []

        # Header
        lines.append(f"# Market Analysis Report: {result.symbol}")
        lines.append("")
        lines.append(f"**Timeframe:** {result.config.name} ({result.config.interval})")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Current Price
        lines.append("## Current Price")
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| Open | ${result.data.iloc[-1]['Open']:.2f} |")
        lines.append(f"| High | ${result.data.iloc[-1]['High']:.2f} |")
        lines.append(f"| Low | ${result.data.iloc[-1]['Low']:.2f} |")
        lines.append(f"| Close | ${result.data.iloc[-1]['Close']:.2f} |")
        lines.append(f"| Volume | {int(result.data.iloc[-1]['Volume']):,} |")
        lines.append("")

        # Signal Summary
        lines.append("## Signal Summary")
        lines.append(f"- **Total Signals:** {result.signals.signal_count}")
        lines.append(f"- **Bullish:** {result.signals.bullish_count} ⬆️")
        lines.append(f"- **Bearish:** {result.signals.bearish_count} ⬇️")
        lines.append(f"- **Neutral:** {result.signals.neutral_count} ➡️")
        lines.append("")

        # Signals by Category
        if result.signals.by_category:
            lines.append("## Signals by Category")
            for category, sigs in sorted(result.signals.by_category.items()):
                lines.append(f"### {category}")
                for sig in sigs[:5]:  # Show top 5
                    strength_emoji = "🟢" if sig.is_bullish() else "🔴" if sig.is_bearish() else "⚪"
                    lines.append(f"- {strength_emoji} **{sig.name}**")
                    lines.append(f"  - {sig.description}")
                    if sig.trading_implication:
                        lines.append(f"  - *Action:* {sig.trading_implication}")
                    lines.append(f"  - *Confidence:* {sig.confidence:.0%}")
                lines.append("")

        # Key Indicators
        lines.append("## Key Indicators")
        indicators = self._get_key_indicators(result.data)
        for ind_name, value in indicators.items():
            lines.append(f"- **{ind_name}:** {value:.2f}")
        lines.append("")

        # Recommendations
        lines.append("## Trading Recommendations")
        recommendations = self._generate_recommendations(result)
        for rec in recommendations:
            lines.append(f"- {rec}")
        lines.append("")

        # Data Info
        lines.append("## Analysis Details")
        lines.append(f"- **Bars Analyzed:** {len(result.data)}")
        lines.append(f"- **Period:** {result.data.index[0]} to {result.data.index[-1]}")
        lines.append(f"- **Configuration:** {result.config.name}")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _get_key_indicators(data: pd.DataFrame) -> dict:
        """Extract key indicators from latest bar."""
        indicators = {}

        # Get specific indicators if available
        for col in ["RSI_14", "MACD", "ATR_14", "ADX_14"]:
            if col in data.columns:
                try:
                    value = float(data.iloc[-1][col])
                    indicators[col] = value
                except (ValueError, TypeError):
                    pass

        return indicators

    @staticmethod
    def _generate_recommendations(result: AnalysisResult) -> List[str]:
        """Generate trading recommendations based on signals."""
        recs = []

        bullish_count = result.signals.bullish_count
        bearish_count = result.signals.bearish_count

        if bullish_count > bearish_count * 2:
            recs.append("🟢 **Strong Bullish Bias:** Consider long positions")
        elif bullish_count > bearish_count:
            recs.append("🟢 **Bullish Bias:** Watch for entry opportunities")
        elif bearish_count > bullish_count * 2:
            recs.append("🔴 **Strong Bearish Bias:** Consider short positions or reduce longs")
        elif bearish_count > bullish_count:
            recs.append("🔴 **Bearish Bias:** Exercise caution on new long entries")
        else:
            recs.append("⚪ **Neutral:** No clear directional bias")

        if "FIBONACCI" in result.signals.by_category:
            recs.append("📊 Key Fibonacci levels identified - watch for support/resistance")

        if "MACD" in result.signals.by_category:
            recs.append("📈 MACD signals present - monitor for momentum changes")

        recs.append("⚠️ Always use proper risk management and stop losses")

        return recs


# ============ CSV EXPORTER ============


class CSVExporter(Exporter):
    """
    Exports signals to CSV format.

    Creates spreadsheet-friendly output with one signal per row.
    """

    def export(self, result: AnalysisResult, filepath: Path) -> ExportResult:
        """
        Export to CSV.

        Args:
            result: Analysis result.
            filepath: Output path.

        Returns:
            ExportResult.
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        rows = []

        for signal in result.signals.signals:
            rows.append({
                "timestamp": signal.timestamp.isoformat(),
                "symbol": result.symbol,
                "interval": result.config.interval,
                "signal_name": signal.name,
                "category": signal.category,
                "strength": signal.strength,
                "description": signal.description,
                "value": signal.value,
                "confidence": signal.confidence,
                "indicator": signal.indicator_name or "",
                "trading_action": signal.trading_implication or "",
                "details": json.dumps(signal.details) if signal.details else "",
            })

        df = pd.DataFrame(rows)

        df.to_csv(filepath, index=False)

        bytes_written = filepath.stat().st_size
        logger.info(f"Exported CSV: {filepath} ({len(rows)} signals)")

        return ExportResult(filepath, "csv", bytes_written)


# ============ MULTI-EXPORTER ============


class MultiExporter:
    """
    Exports results in multiple formats at once.

    Simplifies exporting to JSON, Markdown, and CSV in one call.
    """

    def __init__(self, output_dir: str = "analysis_results"):
        """
        Initialize multi-exporter.

        Args:
            output_dir: Base directory for exports.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export_all(
        self,
        result: AnalysisResult,
        formats: List[str] = None,
        prefix: str = "",
    ) -> dict:
        """
        Export to multiple formats.

        Args:
            result: Analysis result.
            formats: List of formats ('json', 'markdown', 'csv').
                     Default: all formats.
            prefix: Optional filename prefix.

        Returns:
            Dictionary mapping format to ExportResult.
        """
        if formats is None:
            formats = ["json", "markdown", "csv"]

        results = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for fmt in formats:
            try:
                filename = f"{prefix}{result.symbol}_{result.config.interval}_{timestamp}"

                if fmt.lower() == "json":
                    filepath = self.output_dir / f"{filename}.json"
                    results[fmt] = JSONExporter().export(result, filepath)

                elif fmt.lower() == "markdown":
                    filepath = self.output_dir / f"{filename}.md"
                    results[fmt] = MarkdownExporter().export(result, filepath)

                elif fmt.lower() == "csv":
                    filepath = self.output_dir / f"{filename}.csv"
                    results[fmt] = CSVExporter().export(result, filepath)

                else:
                    logger.warning(f"Unknown format: {fmt}")

            except Exception as e:
                logger.error(f"Export to {fmt} failed: {str(e)}")
                results[fmt] = None

        return results

    def export_json(self, result: AnalysisResult, filepath: Optional[Path] = None) -> ExportResult:
        """Quick JSON export."""
        if filepath is None:
            filepath = self.output_dir / f"{result.symbol}_{result.config.interval}.json"
        return JSONExporter().export(result, filepath)

    def export_markdown(self, result: AnalysisResult, filepath: Optional[Path] = None) -> ExportResult:
        """Quick Markdown export."""
        if filepath is None:
            filepath = self.output_dir / f"{result.symbol}_{result.config.interval}.md"
        return MarkdownExporter().export(result, filepath)

    def export_csv(self, result: AnalysisResult, filepath: Optional[Path] = None) -> ExportResult:
        """Quick CSV export."""
        if filepath is None:
            filepath = self.output_dir / f"{result.symbol}_{result.config.interval}.csv"
        return CSVExporter().export(result, filepath)