"""
Firebase Database Integration for Signal Analyzer.

Provides a dynamic, schema-flexible database for storing:
- Analysis results (signals, indicators, AI output)
- Historical tracking
- Real-time updates

Schema Design:
    - Mirrors JSON export format for consistency
    - Supports dynamic addition of new signals/indicators
    - Optimized for querying by symbol, timestamp, signal type

Firestore Structure:
    analyses/
        {analysis_id}/
            symbol: str
            interval: str
            timestamp: datetime
            bars_analyzed: int
            indicators: map (dynamic)
            signal_summary: map
            ai_analysis: map (optional)

    signals/
        {signal_id}/
            analysis_id: ref
            symbol: str
            timestamp: datetime
            name: str
            category: str
            strength: str
            confidence: float
            description: str
            trading_implication: str

    indicators_history/
        {symbol}/
            {interval}/
                {timestamp}/
                    values: map (all indicator values)

    ai_outputs/
        {analysis_id}/
            signal_summary: str
            trading_recommendation: map
            risk_assessment: map
            volatility_regime: map
            opportunities: array
            alerts: array
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from logging_config import get_logger

logger = get_logger()

# Firebase SDK imports (lazy loaded)
_firestore = None
_firebase_app = None


def _init_firebase():
    """Initialize Firebase (lazy loading)."""
    global _firestore, _firebase_app

    if _firestore is not None:
        return _firestore

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        # Check for credentials
        cred_path = os.environ.get(
            "FIREBASE_CREDENTIALS",
            "firebase-credentials.json"
        )

        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
        else:
            # Try default credentials (for Cloud Run, etc.)
            _firebase_app = firebase_admin.initialize_app()

        _firestore = firestore.client()
        logger.info("Firebase initialized successfully")
        return _firestore

    except ImportError:
        logger.warning(
            "firebase-admin not installed. "
            "Install with: pip install firebase-admin"
        )
        return None
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        return None


# ============ DATA MODELS ============


@dataclass
class SignalDocument:
    """Signal document for Firestore."""

    analysis_id: str
    symbol: str
    timestamp: datetime
    name: str
    category: str
    strength: str
    confidence: float
    description: str
    trading_implication: Optional[str] = None
    value: Optional[float] = None
    indicator_name: Optional[str] = None
    timeframe: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible dict."""
        data = asdict(self)
        # Remove None values for cleaner storage
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class AnalysisDocument:
    """Analysis document for Firestore."""

    symbol: str
    interval: str
    timestamp: datetime
    bars_analyzed: int
    indicators: Dict[str, Any]
    signal_summary: Dict[str, Any]
    ai_enabled: bool = False
    ai_analysis: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible dict."""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


# ============ FIREBASE CLIENT ============


class FirebaseAnalysisDB:
    """
    Firebase client for analysis storage.

    Provides methods for storing and querying analysis results
    with a dynamic, extensible schema.

    Example:
        >>> db = FirebaseAnalysisDB()
        >>> analysis_id = db.store_analysis(result)
        >>> history = db.get_analysis_history('NVDA', limit=10)
    """

    # Collection names
    ANALYSES = "analyses"
    SIGNALS = "signals"
    INDICATORS_HISTORY = "indicators_history"
    AI_OUTPUTS = "ai_outputs"

    def __init__(self):
        """Initialize Firebase client."""
        self.db = _init_firebase()
        if self.db is None:
            logger.warning("Firebase not available - using mock mode")

    @property
    def is_connected(self) -> bool:
        """Check if Firebase is connected."""
        return self.db is not None

    def store_analysis(self, result) -> Optional[str]:
        """
        Store complete analysis result to Firebase.

        Creates documents in multiple collections:
        - analyses: Main analysis document
        - signals: Individual signal documents
        - indicators_history: Historical indicator tracking
        - ai_outputs: AI analysis (if available)

        Args:
            result: EnhancedAnalysisResult from pipeline.

        Returns:
            Analysis document ID, or None if storage failed.
        """
        if not self.is_connected:
            logger.warning("Firebase not connected - skipping storage")
            return None

        try:
            timestamp = datetime.utcnow()
            base = result.base_result

            # 1. Create main analysis document
            analysis_doc = {
                "symbol": result.symbol,
                "interval": base.interval if hasattr(base, 'interval') else "1d",
                "timestamp": timestamp,
                "bars_analyzed": base.bars_analyzed,
                "indicators": self._sanitize_indicators(base.indicators),
                "signal_summary": {
                    "total": base.signals.signal_count,
                    "bullish": base.signals.bullish_count,
                    "bearish": base.signals.bearish_count,
                    "neutral": base.signals.neutral_count,
                },
                "ai_enabled": result.ai_result is not None,
            }

            # Store main document
            analysis_ref = self.db.collection(self.ANALYSES).document()
            analysis_ref.set(analysis_doc)
            analysis_id = analysis_ref.id
            logger.info(f"Stored analysis: {analysis_id}")

            # 2. Store individual signals
            signals_batch = self.db.batch()
            for signal in base.signals.signals:
                signal_doc = SignalDocument(
                    analysis_id=analysis_id,
                    symbol=result.symbol,
                    timestamp=timestamp,
                    name=signal.name,
                    category=signal.category,
                    strength=signal.strength,
                    confidence=signal.confidence,
                    description=signal.description,
                    trading_implication=getattr(signal, 'trading_implication', None),
                    value=getattr(signal, 'value', None),
                    indicator_name=getattr(signal, 'indicator_name', None),
                )
                signal_ref = self.db.collection(self.SIGNALS).document()
                signals_batch.set(signal_ref, signal_doc.to_dict())

            signals_batch.commit()
            logger.info(f"Stored {base.signals.signal_count} signals")

            # 3. Store indicators history
            interval = base.interval if hasattr(base, 'interval') else "1d"
            history_ref = (
                self.db.collection(self.INDICATORS_HISTORY)
                .document(result.symbol)
                .collection(interval)
                .document(timestamp.isoformat())
            )
            history_ref.set({
                "timestamp": timestamp,
                "values": self._sanitize_indicators(base.indicators),
            })

            # 4. Store AI output (if available)
            if result.ai_result:
                ai_doc = self._build_ai_document(result.ai_result)
                self.db.collection(self.AI_OUTPUTS).document(analysis_id).set(ai_doc)
                logger.info("Stored AI analysis")

            return analysis_id

        except Exception as e:
            logger.error(f"Failed to store analysis: {e}")
            return None

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis by ID.

        Args:
            analysis_id: Document ID.

        Returns:
            Analysis document or None.
        """
        if not self.is_connected:
            return None

        try:
            doc = self.db.collection(self.ANALYSES).document(analysis_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id

                # Fetch associated signals
                signals = self.get_signals_for_analysis(analysis_id)
                data['signals'] = signals

                # Fetch AI output
                ai_doc = self.db.collection(self.AI_OUTPUTS).document(analysis_id).get()
                if ai_doc.exists:
                    data['ai_analysis'] = ai_doc.to_dict()

                return data
            return None

        except Exception as e:
            logger.error(f"Failed to get analysis: {e}")
            return None

    def get_analysis_history(
        self,
        symbol: str,
        interval: str = "1d",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get analysis history for a symbol.

        Args:
            symbol: Stock symbol.
            interval: Timeframe.
            limit: Max results.

        Returns:
            List of analysis documents.
        """
        if not self.is_connected:
            return []

        try:
            query = (
                self.db.collection(self.ANALYSES)
                .where("symbol", "==", symbol)
                .where("interval", "==", interval)
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
            )

            results = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)

            return results

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    def get_signals_for_analysis(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Get all signals for an analysis."""
        if not self.is_connected:
            return []

        try:
            query = (
                self.db.collection(self.SIGNALS)
                .where("analysis_id", "==", analysis_id)
            )

            return [doc.to_dict() for doc in query.stream()]

        except Exception as e:
            logger.error(f"Failed to get signals: {e}")
            return []

    def get_signals_by_category(
        self,
        symbol: str,
        category: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get signals by category for a symbol.

        Args:
            symbol: Stock symbol.
            category: Signal category (RSI, MACD, MA_CROSS, etc.).
            limit: Max results.

        Returns:
            List of signal documents.
        """
        if not self.is_connected:
            return []

        try:
            query = (
                self.db.collection(self.SIGNALS)
                .where("symbol", "==", symbol)
                .where("category", "==", category)
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
            )

            return [doc.to_dict() for doc in query.stream()]

        except Exception as e:
            logger.error(f"Failed to get signals by category: {e}")
            return []

    def get_indicator_history(
        self,
        symbol: str,
        interval: str = "1d",
        indicator: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get indicator history for a symbol.

        Args:
            symbol: Stock symbol.
            interval: Timeframe.
            indicator: Specific indicator name (optional).
            limit: Max results.

        Returns:
            List of indicator snapshots.
        """
        if not self.is_connected:
            return []

        try:
            query = (
                self.db.collection(self.INDICATORS_HISTORY)
                .document(symbol)
                .collection(interval)
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
            )

            results = []
            for doc in query.stream():
                data = doc.to_dict()
                if indicator:
                    # Filter to specific indicator
                    value = data.get("values", {}).get(indicator)
                    if value is not None:
                        results.append({
                            "timestamp": data["timestamp"],
                            indicator: value,
                        })
                else:
                    results.append(data)

            return results

        except Exception as e:
            logger.error(f"Failed to get indicator history: {e}")
            return []

    def get_latest_ai_recommendations(
        self,
        symbol: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get latest AI trading recommendations.

        Args:
            symbol: Filter by symbol (optional).
            limit: Max results.

        Returns:
            List of AI recommendation documents.
        """
        if not self.is_connected:
            return []

        try:
            # Get recent analyses with AI enabled
            query = self.db.collection(self.ANALYSES).where("ai_enabled", "==", True)

            if symbol:
                query = query.where("symbol", "==", symbol)

            query = query.order_by("timestamp", direction="DESCENDING").limit(limit)

            results = []
            for doc in query.stream():
                analysis_id = doc.id
                ai_doc = self.db.collection(self.AI_OUTPUTS).document(analysis_id).get()
                if ai_doc.exists:
                    data = doc.to_dict()
                    data['ai_analysis'] = ai_doc.to_dict()
                    data['id'] = analysis_id
                    results.append(data)

            return results

        except Exception as e:
            logger.error(f"Failed to get AI recommendations: {e}")
            return []

    def _sanitize_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize indicator values for Firestore (handle numpy types)."""
        import numpy as np

        sanitized = {}
        for key, value in indicators.items():
            if value is None:
                continue
            elif isinstance(value, (np.integer, np.floating)):
                sanitized[key] = float(value)
            elif isinstance(value, np.ndarray):
                sanitized[key] = value.tolist()
            elif isinstance(value, (int, float, str, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)

        return sanitized

    def _build_ai_document(self, ai_result) -> Dict[str, Any]:
        """Build AI output document."""
        doc = {
            "timestamp": datetime.utcnow(),
        }

        if hasattr(ai_result, 'signal_summary'):
            doc["signal_summary"] = ai_result.signal_summary

        if hasattr(ai_result, 'trading_recommendation'):
            rec = ai_result.trading_recommendation
            if isinstance(rec, dict):
                doc["trading_recommendation"] = self._sanitize_indicators(rec)
            else:
                doc["trading_recommendation"] = str(rec)

        if hasattr(ai_result, 'risk_assessment'):
            doc["risk_assessment"] = ai_result.risk_assessment

        if hasattr(ai_result, 'volatility_regime'):
            doc["volatility_regime"] = ai_result.volatility_regime

        if hasattr(ai_result, 'opportunities'):
            doc["opportunities"] = ai_result.opportunities or []

        if hasattr(ai_result, 'alerts'):
            doc["alerts"] = ai_result.alerts or []

        return doc


# ============ JSON EXPORT (FIREBASE SCHEMA COMPATIBLE) ============


def export_to_firebase_json(result, filepath: str) -> str:
    """
    Export analysis result to JSON in Firebase-compatible format.

    This creates a JSON file that mirrors the Firebase schema,
    useful for local storage or importing into Firebase.

    Args:
        result: EnhancedAnalysisResult from pipeline.
        filepath: Output file path.

    Returns:
        Path to created file.
    """
    import numpy as np

    def sanitize(obj):
        """Recursively sanitize for JSON."""
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(i) for i in obj]
        elif hasattr(obj, '__dict__'):
            return sanitize(obj.__dict__)
        return obj

    timestamp = datetime.utcnow()
    base = result.base_result

    # Build export document (mirrors Firebase schema)
    export = {
        "analysis": {
            "symbol": result.symbol,
            "interval": getattr(base, 'interval', '1d'),
            "timestamp": timestamp.isoformat(),
            "bars_analyzed": base.bars_analyzed,
            "indicators": sanitize(base.indicators),
            "signal_summary": {
                "total": base.signals.signal_count,
                "bullish": base.signals.bullish_count,
                "bearish": base.signals.bearish_count,
                "neutral": base.signals.neutral_count,
            },
        },
        "signals": [
            {
                "name": s.name,
                "category": s.category,
                "strength": s.strength,
                "confidence": s.confidence,
                "description": s.description,
                "trading_implication": getattr(s, 'trading_implication', None),
                "value": sanitize(getattr(s, 'value', None)),
                "indicator_name": getattr(s, 'indicator_name', None),
            }
            for s in base.signals.signals
        ],
    }

    # Add AI analysis if available
    if result.ai_result:
        export["ai_analysis"] = {
            "signal_summary": result.ai_result.signal_summary,
            "trading_recommendation": sanitize(result.ai_result.trading_recommendation),
            "risk_assessment": sanitize(result.ai_result.risk_assessment),
            "volatility_regime": sanitize(result.ai_result.volatility_regime),
            "opportunities": sanitize(result.ai_result.opportunities) if result.ai_result.opportunities else [],
            "alerts": result.ai_result.alerts if result.ai_result.alerts else [],
        }

    # Write to file
    with open(filepath, 'w') as f:
        json.dump(export, f, indent=2, default=str)

    logger.info(f"Exported to {filepath}")
    return filepath


# ============ CONVENIENCE FUNCTIONS ============


def get_firebase_db() -> FirebaseAnalysisDB:
    """Get or create Firebase client singleton."""
    global _firebase_client
    try:
        return _firebase_client
    except NameError:
        _firebase_client = FirebaseAnalysisDB()
        return _firebase_client


def store_analysis(result) -> Optional[str]:
    """Convenience function to store analysis."""
    return get_firebase_db().store_analysis(result)


def get_analysis_history(symbol: str, limit: int = 50) -> List[Dict]:
    """Convenience function to get analysis history."""
    return get_firebase_db().get_analysis_history(symbol, limit=limit)
