# verify integration with AI providers

"""
AI Integration Continuation: Themes 11-25

Remaining AI strategies for advanced trading intelligence and automation.
"""

import json
from typing import Dict, List, Any
import numpy as np
import pandas as pd
from logging_config import get_logger

logger = get_logger()


# ============ THEME 11: INDICATOR LEVEL ALERTING ============


class IndicatorAlerts:
    """
    Theme 11: Indicator Level Alerting
    
    Identifies critical indicator levels to watch in real-time.
    """
    
    def generate_alerts(self, indicators: Dict, symbol: str = "UNKNOWN") -> List[Dict]:
        """
        Generate alerts for critical indicator levels.
        
        Args:
            indicators: Current market indicators
            symbol: Stock symbol for context
        
        Returns:
            List of active alerts
        """
        alerts = []
        current_price = indicators.get('Current_Price', 100)
        
        # RSI Extremes
        rsi = indicators.get('RSI', 50)
        if rsi > 75:
            alerts.append({
                'indicator': 'RSI',
                'level': rsi,
                'status': 'EXTREME_OVERBOUGHT',
                'watch': 'Watch for reversal',
                'trigger': 'Price breaks below SMA-20'
            })
        elif rsi > 70:
            alerts.append({
                'indicator': 'RSI',
                'level': rsi,
                'status': 'OVERBOUGHT',
                'watch': 'Pullback likely',
                'trigger': 'RSI crosses below 70'
            })
        elif rsi < 25:
            alerts.append({
                'indicator': 'RSI',
                'level': rsi,
                'status': 'EXTREME_OVERSOLD',
                'watch': 'Watch for bounce',
                'trigger': 'Price breaks above SMA-20'
            })
        elif rsi < 30:
            alerts.append({
                'indicator': 'RSI',
                'level': rsi,
                'status': 'OVERSOLD',
                'watch': 'Bounce likely',
                'trigger': 'RSI crosses above 30'
            })
        
        # Volatility Extremes
        hv = indicators.get('HV_30d', 0.20)
        atr = indicators.get('ATR', 0)
        
        if hv > 0.40:
            alerts.append({
                'indicator': 'Volatility (HV 30d)',
                'level': f'{hv:.1%}',
                'status': 'EXTREME_HIGH',
                'watch': 'Expect large swings',
                'trigger': 'Use wider stops'
            })
        
        if hv < 0.12:
            alerts.append({
                'indicator': 'Volatility (HV 30d)',
                'level': f'{hv:.1%}',
                'status': 'VERY_LOW',
                'watch': 'Volatility expansion coming',
                'trigger': 'Prepare for volatility breakout'
            })
        
        # Bollinger Bands
        bb_pct = indicators.get('BB_PercentB', 0.5)
        if bb_pct > 0.95:
            alerts.append({
                'indicator': 'Bollinger Band %B',
                'level': f'{bb_pct:.1%}',
                'status': 'AT_UPPER_BAND',
                'watch': 'Extreme level',
                'trigger': 'Watch for reversal to middle band'
            })
        elif bb_pct < 0.05:
            alerts.append({
                'indicator': 'Bollinger Band %B',
                'level': f'{bb_pct:.1%}',
                'status': 'AT_LOWER_BAND',
                'watch': 'Extreme level',
                'trigger': 'Watch for bounce to middle band'
            })
        
        # MACD Alignment
        macd = indicators.get('MACD_Value', 0)
        signal = indicators.get('MACD_Signal', 0)
        if abs(macd - signal) < 0.01:
            alerts.append({
                'indicator': 'MACD',
                'level': f'{macd:.3f}',
                'status': 'ABOUT_TO_CROSS',
                'watch': 'Momentum change imminent',
                'trigger': f"MACD crosses {'above' if macd > signal else 'below'} signal"
            })
        
        return alerts


# ============ THEME 12: INDICATOR HEALTH SCORING ============


class IndicatorHealthScorer:
    """
    Theme 12: Indicator Health Scoring
    
    Evaluates reliability of each indicator based on historical performance.
    """
    
    def __init__(self):
        """Initialize scorer with default reliability scores."""
        # These would be updated from historical performance
        self.detector_accuracy = {
            'MA_CROSS': 0.72,
            'RSI': 0.65,
            'MACD': 0.68,
            'FIBONACCI': 0.78,
            'BOLLINGER': 0.63,
            'VOLUME': 0.75,
            'ADX': 0.70,
            'STOCHASTIC': 0.62
        }
    
    def score_detectors(self, detected_categories: List[str]) -> Dict[str, Any]:
        """
        Score detectors by historical accuracy.
        
        Args:
            detected_categories: Categories of detected signals
        
        Returns:
            Detector scoring
        """
        detector_scores = []
        
        for category in detected_categories:
            accuracy = self.detector_accuracy.get(category, 0.50)
            detector_scores.append({
                'detector': category,
                'historical_accuracy': f'{accuracy:.0%}',
                'reliability': self._reliability_label(accuracy),
                'weight_adjustment': self._weight_adjustment(accuracy)
            })
        
        # Sort by reliability
        detector_scores.sort(key=lambda x: x['historical_accuracy'], reverse=True)
        
        return {
            'detector_scores': detector_scores,
            'most_reliable': detector_scores[0]['detector'] if detector_scores else None,
            'least_reliable': detector_scores[-1]['detector'] if detector_scores else None,
            'average_accuracy': f"{np.mean([float(s['historical_accuracy'].rstrip('%'))/100 for s in detector_scores]):.0%}" if detector_scores else "0%"
        }
    
    def _reliability_label(self, accuracy: float) -> str:
        """Get reliability label."""
        if accuracy > 0.75:
            return 'VERY_RELIABLE'
        elif accuracy > 0.65:
            return 'RELIABLE'
        elif accuracy > 0.55:
            return 'MODERATE'
        else:
            return 'UNRELIABLE'
    
    def _weight_adjustment(self, accuracy: float) -> str:
        """Recommend weight adjustment."""
        if accuracy > 0.75:
            return '+50% weight'
        elif accuracy > 0.65:
            return '+25% weight'
        elif accuracy > 0.55:
            return 'Normal weight'
        else:
            return '-50% weight or skip'


# ============ THEME 13: MISSING SIGNAL DETECTION ============


class MissingSignalDetector:
    """
    Theme 13: Missing Signal Detection
    
    Identifies when expected signals don't appear (anomalies).
    """
    
    def detect_anomalies(self, indicators: Dict, expected_signals: List[str], 
                        actual_signals: List[str]) -> List[Dict]:
        """
        Detect missing or unexpected signals.
        
        Args:
            indicators: Current market indicators
            expected_signals: What we'd normally expect to see
            actual_signals: What we actually see
        
        Returns:
            List of anomalies
        """
        anomalies = []
        
        # Check for missing RSI signal when overbought/oversold
        rsi = indicators.get('RSI', 50)
        if rsi < 30 and 'RSI_OVERSOLD' not in actual_signals:
            anomalies.append({
                'type': 'MISSING_SIGNAL',
                'description': f'RSI at {rsi:.0f} (oversold) but no oversold signal detected',
                'implication': 'Possible unusual demand/supply dynamic',
                'action': 'Investigate - price may be supported by strong buying'
            })
        
        # Check for broken relationships
        macd = indicators.get('MACD_Value', 0)
        signal_line = indicators.get('MACD_Signal', 0)
        price_trend = 'UP' if indicators.get('Current_Price', 100) > indicators.get('SMA_50', 100) else 'DOWN'
        
        if price_trend == 'UP' and macd < signal_line:
            anomalies.append({
                'type': 'DIVERGENCE',
                'description': 'Price up but MACD below signal - hidden divergence',
                'implication': 'Potential loss of bullish momentum',
                'action': 'Watch for bearish reversal'
            })
        
        # Check for silent consolidation
        atm = indicators.get('ATR', 1)
        price = indicators.get('Current_Price', 100)
        atr_pct = (atm / price) * 100
        
        if atr_pct < 0.5 and len(actual_signals) < 3:
            anomalies.append({
                'type': 'SILENT_CONSOLIDATION',
                'description': f'Very low volatility ({atr_pct:.2f}%) with few signals',
                'implication': 'Major move likely coming',
                'action': 'Prepare for volatility expansion and breakout'
            })
        
        return anomalies


# ============ THEME 14-15: DIVERGENCE & PERIOD OPTIMIZATION ============


class DivergenceDetector:
    """
    Theme 14: Indicator Divergence Highlighting
    
    Surfaces hidden divergences automatically.
    """
    
    def detect_divergences(self, price_history: pd.DataFrame, 
                          indicators_history: pd.DataFrame) -> List[Dict]:
        """
        Detect price/indicator divergences.
        
        Args:
            price_history: Historical price data
            indicators_history: Historical indicators
        
        Returns:
            List of divergences
        """
        divergences = []
        
        if len(price_history) < 30:
            return divergences  # Need enough history
        
        # Get last 30 bars
        prices = price_history['Close'].tail(30)
        rsi_vals = indicators_history.get('RSI', pd.Series()).tail(30)
        
        # Find price highs/lows
        price_high_idx = prices.idxmax()
        price_high = prices.max()
        
        # Find RSI divergence
        if len(rsi_vals) > 0:
            rsi_at_high = rsi_vals[price_high_idx]
            
            # Look back for previous high
            if len(prices) > 10:
                prev_high_idx = prices.iloc[:-1].idxmax()
                prev_high = prices[prev_high_idx]
                rsi_at_prev = rsi_vals[prev_high_idx]
                
                if price_high > prev_high and rsi_at_high < rsi_at_prev:
                    divergences.append({
                        'type': 'BEARISH_DIVERGENCE',
                        'description': 'Price made new high but RSI lower - weakening momentum',
                        'strength': 'HIGH',
                        'action': 'Watch for bearish reversal'
                    })
        
        return divergences


class PeriodOptimizer:
    """
    Theme 15: Optimal Period Suggestions
    
    Recommends indicator periods based on market regime.
    """
    
    def suggest_periods(self, indicators: Dict, current_period_config: Dict) -> Dict[str, Any]:
        """
        Suggest optimal indicator periods.
        
        Args:
            indicators: Current market indicators
            current_period_config: Current period settings
        
        Returns:
            Optimization suggestions
        """
        hv = indicators.get('HV_30d', 0.20)
        
        suggestions = {}
        
        # RSI period optimization
        if hv < 0.15:  # Low volatility
            suggestions['RSI'] = {
                'current': current_period_config.get('RSI_period', 14),
                'suggested': 10,
                'reason': 'Lower period for faster signals in low volatility'
            }
        elif hv > 0.30:  # High volatility
            suggestions['RSI'] = {
                'current': current_period_config.get('RSI_period', 14),
                'suggested': 21,
                'reason': 'Longer period to reduce false signals in high volatility'
            }
        
        # SMA period optimization
        trend_strength = abs(indicators.get('Current_Price', 100) - indicators.get('SMA_50', 100)) / indicators.get('Current_Price', 1) * 100
        
        if trend_strength > 3:  # Strong trend
            suggestions['SMA'] = {
                'current': current_period_config.get('SMA_period', 50),
                'suggested': 100,
                'reason': 'Longer MA to ride strong trends'
            }
        elif trend_strength < 1:  # Weak trend
            suggestions['SMA'] = {
                'current': current_period_config.get('SMA_period', 50),
                'suggested': 20,
                'reason': 'Shorter MA to react faster to changes'
            }
        
        return {
            'market_regime': 'high_volatility' if hv > 0.25 else 'normal' if hv > 0.15 else 'low_volatility',
            'optimization_suggestions': suggestions if suggestions else {'message': 'Current periods are optimal'}
        }


# ============ THEME 16: STRATEGY GENERATION ============


class StrategyGenerator:
    """
    Theme 16: Strategy Generation
    
    Creates trading strategies from winning signal combinations.
    """
    
    def __init__(self):
        """Initialize with known winning combinations."""
        self.winning_patterns = {
            'golden_cross_rsi': {
                'signals': ['MA_CROSS_BULLISH', 'RSI_OVERSOLD_BOUNCE'],
                'win_rate': 0.78,
                'description': 'SMA crossover + RSI bounce',
                'timeframe': '1h-1d',
                'entry': 'On RSI divergence confirmation',
                'stop': '2xATR below entry',
                'target': '3xATR above entry'
            },
            'fibonacci_volume': {
                'signals': ['FIBONACCI_LEVEL', 'VOLUME_CONFIRMATION'],
                'win_rate': 0.82,
                'description': 'Fibonacci level with volume confirmation',
                'timeframe': '15m-1h',
                'entry': 'Price touches Fib level on high volume',
                'stop': 'Below next Fib level',
                'target': 'Next Fib extension'
            },
            'macd_confluence': {
                'signals': ['MACD_CROSS', 'MA_CROSS', 'RSI_EXTREME'],
                'win_rate': 0.75,
                'description': 'Triple signal confluence',
                'timeframe': '4h-1d',
                'entry': 'All three signals confirm',
                'stop': '1.5xATR below entry',
                'target': '4xATR above entry'
            }
        }
    
    def generate_strategy(self, detected_signals: List[str], 
                         win_rate_threshold: float = 0.70) -> Dict[str, Any]:
        """
        Generate strategy from signals.
        
        Args:
            detected_signals: Signals that triggered
            win_rate_threshold: Minimum acceptable win rate
        
        Returns:
            Generated strategy
        """
        matching_strategies = []
        
        for strat_name, strat_data in self.winning_patterns.items():
            # Check how many signals match
            matched = sum(1 for sig in strat_data['signals'] if sig in detected_signals)
            match_pct = matched / len(strat_data['signals'])
            
            if match_pct >= 0.5 and strat_data['win_rate'] >= win_rate_threshold:
                matching_strategies.append({
                    'name': strat_name,
                    'matched_signals': matched,
                    'match_percentage': f'{match_pct:.0%}',
                    **strat_data
                })
        
        if matching_strategies:
            # Sort by win rate
            matching_strategies.sort(key=lambda x: x['win_rate'], reverse=True)
            return {
                'recommended_strategy': matching_strategies[0],
                'alternative_strategies': matching_strategies[1:],
                'confidence': matching_strategies[0]['win_rate']
            }
        else:
            return {
                'message': 'No high-confidence strategies matched current signals',
                'recommendation': 'Wait for more signal confirmation'
            }


# ============ THEME 17-25: ADVANCED FEATURES ============


class PositionSizer:
    """Theme 17: Position Sizing Intelligence"""
    
    def calculate_size(self, account_size: float, risk_pct: float,
                      stop_loss_pct: float, win_rate: float = 0.55) -> Dict[str, Any]:
        """Calculate optimal position size."""
        risk_amount = account_size * (risk_pct / 100)
        position_size = risk_amount / (stop_loss_pct / 100)
        
        # Kelly Criterion adjustment
        kelly_fraction = (win_rate * 2 - 1) / 2  # Simplified Kelly
        kelly_adjusted_size = position_size * max(0.5, min(1.5, kelly_fraction))  # Clamp between 0.5-1.5x
        
        return {
            'position_size': round(position_size, 2),
            'kelly_adjusted': round(kelly_adjusted_size, 2),
            'risk_amount': round(risk_amount, 2),
            'allocation_pct': round((position_size / account_size) * 100, 2),
            'recommended_size': round(kelly_adjusted_size, 2)
        }


class EntryExitOptimizer:
    """Theme 18: Entry/Exit Optimization"""
    
    def optimize(self, current_price: float, support: float,
                resistance: float, atr: float) -> Dict[str, Any]:
        """Optimize entry and exit points."""
        return {
            'aggressive_entry': round(current_price + (atr * 0.5), 2),
            'conservative_entry': round(support + (atr * 0.2), 2),
            'breakeven_stop': round(current_price - (atr * 0.5), 2),
            'tight_stop': round(support - (atr * 0.1), 2),
            'target_1': round(resistance - (atr * 0.2), 2),
            'target_2': round(resistance + (atr * 0.5), 2),
            'risk_reward_1_to_2': round((resistance - (atr * 0.2) - current_price) / atr, 2)
        }


class VolatilityRegimeDetector:
    """Theme 22: Volatility Regime Detection"""
    
    def detect_regime(self, hv: float, atr_pct: float) -> Dict[str, Any]:
        """Detect volatility regime."""
        if hv > 0.35 or atr_pct > 3:
            regime = 'EXTREME_VOLATILITY'
            action = 'Widen stops, reduce size, avoid breakouts'
        elif hv > 0.25 or atr_pct > 2.5:
            regime = 'HIGH_VOLATILITY'
            action = 'Use wider stops, be cautious with tight setups'
        elif hv < 0.10 or atr_pct < 0.8:
            regime = 'LOW_VOLATILITY'
            action = 'Volatility compression - watch for breakout'
        else:
            regime = 'NORMAL_VOLATILITY'
            action = 'Standard risk management applies'
        
        return {
            'regime': regime,
            'hv_30d': f'{hv:.1%}',
            'atr_pct': f'{atr_pct:.2f}%',
            'recommended_action': action
        }


class SentimentWeighter:
    """Theme 23: Sentiment-Based Signal Weighting"""
    
    def weight_by_sentiment(self, signals: List[Dict],
                          vix: float = 20,
                          put_call_ratio: float = 1.0) -> List[Dict]:
        """Adjust signal weights by market sentiment."""
        weighted = []
        
        # Calculate sentiment score (-1 to +1, higher = more bullish)
        sentiment = 1 - (vix / 50)  # VIX normalization
        if put_call_ratio > 1.2:
            sentiment -= 0.2  # Bearish bias
        elif put_call_ratio < 0.8:
            sentiment += 0.2  # Bullish bias
        
        for signal in signals:
            sig_copy = signal.copy()
            original_conf = sig_copy.get('confidence', 0.5)
            
            # Adjust based on sentiment
            if sentiment < -0.3:  # Very fearful
                if 'BULLISH' in signal.get('strength', ''):
                    sig_copy['confidence'] = min(1.0, original_conf * 1.3)  # Boost bullish
                    sig_copy['sentiment_boost'] = '+30%'
            elif sentiment > 0.3:  # Very greedy
                if 'BEARISH' in signal.get('strength', ''):
                    sig_copy['confidence'] = min(1.0, original_conf * 1.3)  # Boost bearish
                    sig_copy['sentiment_boost'] = '+30%'
            
            weighted.append(sig_copy)
        
        return weighted


class AnomalyDetector:
    """Theme 24: Anomaly & Black Swan Detection"""
    
    def detect_anomalies(self, indicators: Dict,
                        price_history: pd.DataFrame = None) -> List[Dict]:
        """Detect unusual market conditions."""
        anomalies = []
        
        rsi = indicators.get('RSI', 50)
        hv = indicators.get('HV_30d', 0.20)
        
        # RSI at extremes with price making new highs/lows
        if rsi > 80:
            anomalies.append({
                'type': 'EXTREME_RSI_HIGH',
                'severity': 'CRITICAL',
                'description': 'RSI at historic extreme',
                'action': 'Possible gap move or structural break'
            })
        
        # Volatility spike
        if hv > 0.5:
            anomalies.append({
                'type': 'VOLATILITY_EXPLOSION',
                'severity': 'CRITICAL',
                'description': 'Volatility at extreme levels',
                'action': 'Market panic or major event'
            })
        
        return anomalies


class LearningSystem:
    """Theme 25: AI-Powered Learning System"""
    
    def __init__(self):
        """Initialize learning system."""
        self.performance_history = []
        self.signal_accuracy = {}
    
    def learn_from_outcome(self, signal: Dict, outcome: str, pnl: float):
        """Learn from completed trades."""
        category = signal.get('category', 'UNKNOWN')
        
        # Update accuracy tracking
        if category not in self.signal_accuracy:
            self.signal_accuracy[category] = {'wins': 0, 'losses': 0, 'total_pnl': 0}
        
        if outcome == 'WIN':
            self.signal_accuracy[category]['wins'] += 1
        else:
            self.signal_accuracy[category]['losses'] += 1
        
        self.signal_accuracy[category]['total_pnl'] += pnl
        self.performance_history.append({
            'signal': signal,
            'outcome': outcome,
            'pnl': pnl,
            'timestamp': pd.Timestamp.now()
        })
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning history."""
        if not self.signal_accuracy:
            return {'message': 'No learning data yet'}
        
        insights = {}
        for category, stats in self.signal_accuracy.items():
            total = stats['wins'] + stats['losses']
            if total > 0:
                win_rate = stats['wins'] / total
                insights[category] = {
                    'win_rate': f'{win_rate:.0%}',
                    'total_trades': total,
                    'total_pnl': round(stats['total_pnl'], 2),
                    'avg_pnl': round(stats['total_pnl'] / total, 2),
                    'recommendation': 'INCREASE_WEIGHT' if win_rate > 0.65 else 'REDUCE_WEIGHT' if win_rate < 0.45 else 'MAINTAIN'
                }
        
        return insights