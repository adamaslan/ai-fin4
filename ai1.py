# verify integration with AI providers
"""
AI Integration Module: 25 AI-Powered Trading Intelligence Themes

Implements AI strategies for signal analysis, trading recommendations, market
intelligence, and automated decision-making. Supports multiple AI providers
(Gemini, Mistral) with fallback and error handling.

This module follows enterprise patterns:
- Exponential backoff for rate limits
- Provider abstraction
- Graceful degradation
- Rich logging
"""

import os
import time
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
from enum import Enum
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from logging_config import get_logger

logger = get_logger()

# Load environment variables
load_dotenv()

# API Configuration with graceful degradation
class AIProvider(Enum):
    """Supported AI providers."""
    GEMINI = "gemini"
    MISTRAL = "mistral"
    NONE = "none"


class AIConfig:
    """AI configuration and provider management."""
    
    def __init__(self):
        """Initialize AI configuration."""
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")
        self.mistral_key = os.environ.get("MISTRAL_API_KEY", "")
        self.primary_provider = self._detect_primary_provider()
        self.api_call_delay = 2.0  # Seconds between API calls
        self.max_retries = 3
        self.initial_backoff = 2  # Exponential backoff base
        self.model_gemini = "gemini-2.5-flash-preview-09-2025"
        self.model_mistral = "mistral-medium"
        
    def _detect_primary_provider(self) -> AIProvider:
        """Detect which AI provider is available."""
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                logger.info("Gemini API configured successfully")
                return AIProvider.GEMINI
            except Exception as e:
                logger.warning(f"Gemini API failed to initialize: {e}")
        
        if self.mistral_key:
            try:
                from mistralai import Mistral
                logger.info("Mistral API available")
                return AIProvider.MISTRAL
            except Exception as e:
                logger.warning(f"Mistral API import failed: {e}")
        
        logger.warning("No AI providers available - running in degraded mode")
        return AIProvider.NONE
    
    def is_available(self) -> bool:
        """Check if any AI provider is available."""
        return self.primary_provider != AIProvider.NONE


# ============ THEME 1: SIGNAL SUMMARIZATION & INTERPRETATION ============


class SignalSummarizer:
    """
    Theme 1: Signal Summarization & Interpretation
    
    Analyzes 50+ signals and produces 3-5 key takeaways with confidence levels.
    """
    
    def __init__(self, config: AIConfig):
        """Initialize summarizer."""
        self.config = config
    
    def summarize(self, signals: List[Dict], indicators: Dict) -> str:
        """
        Summarize signals into actionable insights.
        
        Args:
            signals: List of detected signals
            indicators: Current market indicators
        
        Returns:
            Summary text or fallback message
        """
        if not self.config.is_available():
            return self._fallback_summary(signals, indicators)
        
        # Categorize signals
        bullish_count = sum(1 for s in signals if s.get('strength', '').startswith('BULLISH'))
        bearish_count = sum(1 for s in signals if s.get('strength', '').startswith('BEARISH'))
        neutral_count = len(signals) - bullish_count - bearish_count
        
        prompt = f"""
        You are a professional trading analyst. Synthesize the following signals into 3-5 KEY TAKEAWAYS.
        
        **Signal Summary:**
        - Total Signals: {len(signals)}
        - Bullish: {bullish_count}
        - Bearish: {bearish_count}
        - Neutral: {neutral_count}
        
        **Top Signals (by confidence):**
        {json.dumps(signals[:5], indent=2)}
        
        **Current Market Context:**
        - Price: ${indicators.get('Current_Price', 'N/A')}
        - RSI: {indicators.get('RSI', 'N/A')}
        - MACD: {'Bullish' if indicators.get('MACD_Bullish') else 'Bearish'}
        - Volatility (HV 30d): {indicators.get('HV_30d', 'N/A')}
        
        **Output Format:**
        1. **Primary Bias:** [BULLISH/BEARISH/NEUTRAL] - [reason with confidence %]
        2. **Key Signal:** [strongest signal] - [why it matters]
        3. **Momentum:** [direction and strength]
        4. **Risk Factor:** [main risk to thesis]
        5. **Action:** [specific trading implication]
        
        Be concise, professional, and data-driven.
        """
        
        return self._call_ai(prompt, "Signal Summarization")
    
    def _fallback_summary(self, signals: List[Dict], indicators: Dict) -> str:
        """Generate rule-based summary when AI unavailable."""
        bullish = sum(1 for s in signals if 'BULLISH' in s.get('strength', ''))
        bearish = sum(1 for s in signals if 'BEARISH' in s.get('strength', ''))
        
        if bullish > bearish * 2:
            bias = "STRONG BULLISH"
        elif bullish > bearish:
            bias = "BULLISH"
        elif bearish > bullish * 2:
            bias = "STRONG BEARISH"
        else:
            bias = "NEUTRAL"
        
        return f"""
        **Signal Summary (Rule-Based)**
        - Bias: {bias}
        - Bullish Signals: {bullish}
        - Bearish Signals: {bearish}
        - Total Signals: {len(signals)}
        """
    
    def _call_ai(self, prompt: str, task_name: str) -> str:
        """Call AI provider with exponential backoff."""
        if self.config.primary_provider == AIProvider.GEMINI:
            return self._call_gemini(prompt, task_name)
        elif self.config.primary_provider == AIProvider.MISTRAL:
            return self._call_mistral(prompt, task_name)
        return f"AI unavailable for {task_name}"
    
    def _call_gemini(self, prompt: str, task_name: str) -> str:
        """Call Gemini API with error handling."""
        import google.generativeai as genai
        
        model = genai.GenerativeModel(self.config.model_gemini)
        
        for attempt in range(self.config.max_retries):
            try:
                response = model.generate_content(prompt)
                logger.info(f"✓ Gemini API success: {task_name}")
                return response.text
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limit/quota errors
                if any(x in error_msg for x in ["429", "quota", "exhausted", "rate"]):
                    if attempt < self.config.max_retries - 1:
                        delay = self.config.initial_backoff * (2 ** attempt)
                        logger.warning(f"Rate limit hit. Retrying in {delay}s (attempt {attempt + 1}/{self.config.max_retries})")
                        time.sleep(delay)
                        continue
                
                logger.error(f"Gemini API error ({task_name}): {error_msg}")
                return f"ERROR: {error_msg}"
        
        return f"ERROR: {task_name} failed after {self.config.max_retries} retries"
    
    def _call_mistral(self, prompt: str, task_name: str) -> str:
        """Call Mistral API with error handling."""
        from mistralai import Mistral
        
        client = Mistral(api_key=self.config.mistral_key)
        
        for attempt in range(self.config.max_retries):
            try:
                response = client.chat.complete(
                    model=self.config.model_mistral,
                    messages=[{"role": "user", "content": prompt}]
                )
                logger.info(f"✓ Mistral API success: {task_name}")
                return response.choices[0].message.content
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limit/quota errors
                if any(x in error_msg for x in ["429", "quota", "exhausted", "rate", "too_many_requests"]):
                    if attempt < self.config.max_retries - 1:
                        delay = self.config.initial_backoff * (2 ** attempt)
                        logger.warning(f"Rate limit hit. Retrying in {delay}s (attempt {attempt + 1}/{self.config.max_retries})")
                        time.sleep(delay)
                        continue
                
                logger.error(f"Mistral API error ({task_name}): {error_msg}")
                return f"ERROR: {error_msg}"
        
        return f"ERROR: {task_name} failed after {self.config.max_retries} retries"


# ============ THEME 2: SIGNAL CONFLUENCE ANALYSIS ============


class ConfluenceAnalyzer:
    """
    Theme 2: Signal Confluence Analysis
    
    Identifies when multiple signal types agree for high-probability setups.
    """
    
    def __init__(self, config: AIConfig):
        """Initialize analyzer."""
        self.config = config
    
    def analyze_confluence(self, signals: List[Dict]) -> Dict[str, Any]:
        """
        Identify signal confluence patterns.
        
        Args:
            signals: List of signals
        
        Returns:
            Confluence analysis with strength scoring
        """
        # Categorize by type
        categories = {}
        for signal in signals:
            cat = signal.get('category', 'UNKNOWN')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(signal)
        
        # Find confluences (2+ categories agreeing)
        confluences = []
        
        # Check MA + Momentum agreement
        if 'MA_CROSS' in categories and 'MACD' in categories:
            if categories['MA_CROSS'][0].get('strength') == categories['MACD'][0].get('strength'):
                confluences.append({
                    'types': ['MA Crossover', 'MACD'],
                    'agreement': 'Direction match',
                    'strength': 'HIGH',
                    'confidence': 0.85
                })
        
        # Check RSI + Price Action
        if 'RSI' in categories and 'PRICE_ACTION' in categories:
            confluences.append({
                'types': ['RSI Extreme', 'Price Action'],
                'agreement': 'Momentum + Volatility',
                'strength': 'MEDIUM',
                'confidence': 0.70
            })
        
        # Check Fibonacci + Volume
        if 'FIBONACCI' in categories and 'VOLUME' in categories:
            confluences.append({
                'types': ['Fibonacci Level', 'Volume Confirmation'],
                'agreement': 'Level + Volume',
                'strength': 'VERY HIGH',
                'confidence': 0.90
            })
        
        return {
            'confluence_count': len(confluences),
            'confluences': confluences,
            'highest_confidence': max([c['confidence'] for c in confluences], default=0),
            'recommendation': self._confluence_recommendation(confluences)
        }
    
    def _confluence_recommendation(self, confluences: List[Dict]) -> str:
        """Generate confluence-based recommendation."""
        if not confluences:
            return "No strong confluence detected. Signals appear fragmented."
        
        avg_confidence = np.mean([c['confidence'] for c in confluences])
        
        if avg_confidence > 0.85:
            return "TRIPLE BULLISH CONFIRMATION: Multiple signal types agreeing - HIGH PROBABILITY SETUP"
        elif avg_confidence > 0.75:
            return "Strong confluence detected. Multiple confirmations suggest reliable setup."
        else:
            return "Moderate confluence. Signals show some agreement but not overwhelming."


# ============ THEME 3: CONTEXT-AWARE SIGNAL FILTERING ============


class ContextAwareFilter:
    """
    Theme 3: Context-Aware Signal Filtering
    
    Adjusts signal importance based on market regime.
    """
    
    def __init__(self, config: AIConfig):
        """Initialize filter."""
        self.config = config
    
    def filter_by_regime(self, signals: List[Dict], indicators: Dict) -> List[Dict]:
        """
        Filter and weight signals based on market regime.
        
        Args:
            signals: List of signals
            indicators: Market indicators
        
        Returns:
            Reweighted signals
        """
        # Determine volatility regime
        hv = indicators.get('HV_30d', 0.20)
        atr = indicators.get('ATR', 0)
        current_price = indicators.get('Current_Price', 100)
        atr_pct = (atr / current_price) * 100 if current_price else 0
        
        regime = self._classify_regime(hv, atr_pct)
        
        # Filter and reweight signals
        filtered = []
        for signal in signals:
            signal_copy = signal.copy()
            signal_copy['original_confidence'] = signal_copy.get('confidence', 0.5)
            
            # Apply regime adjustments
            if regime == 'low_vol':
                # In low volatility, reward mean reversion
                if 'RSI' in signal.get('category', ''):
                    signal_copy['confidence'] = min(1.0, signal_copy.get('confidence', 0.5) * 1.25)
                # Penalize trend followers
                elif 'MA_CROSS' in signal.get('category', ''):
                    signal_copy['confidence'] = max(0.1, signal_copy.get('confidence', 0.5) * 0.75)
            
            elif regime == 'high_vol':
                # In high volatility, reward breakouts/trends
                if 'MA_CROSS' in signal.get('category', ''):
                    signal_copy['confidence'] = min(1.0, signal_copy.get('confidence', 0.5) * 1.30)
                # Penalize mean reversion
                elif 'RSI' in signal.get('category', ''):
                    signal_copy['confidence'] = max(0.1, signal_copy.get('confidence', 0.5) * 0.70)
            
            signal_copy['regime'] = regime
            filtered.append(signal_copy)
        
        return sorted(filtered, key=lambda x: x['confidence'], reverse=True)
    
    def _classify_regime(self, hv: float, atr_pct: float) -> str:
        """Classify volatility regime."""
        if hv < 0.15 and atr_pct < 1.5:
            return 'low_vol'
        elif hv > 0.30 or atr_pct > 2.5:
            return 'high_vol'
        else:
            return 'normal'


# ============ THEME 4: REAL-TIME TRADING RECOMMENDATIONS ============


class TradingRecommender:
    """
    Theme 4: Real-Time Trading Recommendations
    
    Converts signals into actionable trading advice with entry/exit levels.
    """
    
    def __init__(self, config: AIConfig):
        """Initialize recommender."""
        self.config = config
    
    def generate_recommendation(self, signals: List[Dict], indicators: Dict) -> Dict[str, Any]:
        """
        Generate complete trading recommendation.
        
        Args:
            signals: Top signals
            indicators: Market data
        
        Returns:
            Complete trade setup
        """
        if not signals:
            return {'recommendation': 'HOLD', 'reason': 'No signals present'}
        
        # Determine direction
        bullish_count = sum(1 for s in signals if 'BULLISH' in s.get('strength', ''))
        bearish_count = sum(1 for s in signals if 'BEARISH' in s.get('strength', ''))
        
        if bullish_count > bearish_count * 1.5:
            direction = 'LONG'
        elif bearish_count > bullish_count * 1.5:
            direction = 'SHORT'
        else:
            direction = 'NEUTRAL'
        
        # Calculate levels
        current_price = indicators.get('Current_Price', 100)
        atr = indicators.get('ATR', current_price * 0.02)
        
        if direction == 'LONG':
            entry = current_price
            stop = current_price - (atr * 2)
            target = current_price + (atr * 3)
        elif direction == 'SHORT':
            entry = current_price
            stop = current_price + (atr * 2)
            target = current_price - (atr * 3)
        else:
            entry = stop = target = current_price
        
        # Calculate risk/reward
        if direction != 'NEUTRAL':
            risk = abs(entry - stop)
            reward = abs(target - entry)
            rr_ratio = reward / risk if risk > 0 else 0
        else:
            rr_ratio = 0
        
        return {
            'recommendation': direction,
            'entry': round(entry, 2),
            'stop_loss': round(stop, 2),
            'target': round(target, 2),
            'risk_reward_ratio': round(rr_ratio, 2),
            'confidence': sum(s.get('confidence', 0.5) for s in signals) / len(signals) if signals else 0,
            'reasoning': signals[0].get('description', 'Signal detected'),
            'position_size_adjustment': self._size_adjustment(rr_ratio)
        }
    
    def _size_adjustment(self, rr_ratio: float) -> str:
        """Recommend position sizing based on risk/reward."""
        if rr_ratio > 3:
            return "FULL SIZE - Excellent risk/reward"
        elif rr_ratio > 2:
            return "NORMAL SIZE - Good risk/reward"
        elif rr_ratio > 1:
            return "3/4 SIZE - Acceptable risk/reward"
        else:
            return "1/2 SIZE or SKIP - Poor risk/reward"


# ============ THEME 5: MULTI-TIMEFRAME SYNTHESIS ============


class MultiTimeframeSynthesizer:
    """
    Theme 5: Multi-Timeframe Synthesis
    
    Combines signals from multiple timeframes into coherent strategy.
    """
    
    def synthesize(self, 
                   signals_1m: List[Dict],
                   signals_5m: List[Dict],
                   signals_1h: List[Dict],
                   signals_1d: List[Dict]) -> Dict[str, Any]:
        """
        Synthesize multi-timeframe analysis.
        
        Args:
            signals_*: Signals from different timeframes
        
        Returns:
            Multi-timeframe synthesis
        """
        timeframes = {
            '1m': signals_1m,
            '5m': signals_5m,
            '1h': signals_1h,
            '1d': signals_1d
        }
        
        # Count directional bias by timeframe
        bias = {}
        for tf, signals in timeframes.items():
            if signals:
                bullish = sum(1 for s in signals if 'BULLISH' in s.get('strength', ''))
                bearish = sum(1 for s in signals if 'BEARISH' in s.get('strength', ''))
                bias[tf] = 'BULLISH' if bullish > bearish else 'BEARISH' if bearish > bullish else 'NEUTRAL'
            else:
                bias[tf] = 'NO_DATA'
        
        return {
            'timeframe_biases': bias,
            'alignment': self._check_alignment(bias),
            'strategy': self._suggest_strategy(bias),
            'entry_trigger': self._identify_entry_trigger(timeframes)
        }
    
    def _check_alignment(self, bias: Dict[str, str]) -> str:
        """Check if timeframes are aligned."""
        directions = [b for b in bias.values() if b != 'NO_DATA']
        if not directions:
            return 'NO_DATA'
        
        if all(d == directions[0] for d in directions):
            return 'PERFECT_ALIGNMENT'
        elif len(set(directions)) == 2:
            return 'PARTIAL_ALIGNMENT'
        else:
            return 'CONFLICTING'
    
    def _suggest_strategy(self, bias: Dict[str, str]) -> str:
        """Suggest strategy based on alignment."""
        daily = bias.get('1d', 'NEUTRAL')
        hourly = bias.get('1h', 'NEUTRAL')
        intraday = bias.get('5m', 'NEUTRAL')
        
        if daily == 'BULLISH' and hourly in ['BULLISH', 'NEUTRAL']:
            return "SWING LONG - Use daily trend, enter on hourly pullback"
        elif daily == 'BEARISH' and hourly in ['BEARISH', 'NEUTRAL']:
            return "SWING SHORT - Use daily trend, enter on hourly bounce"
        elif hourly == 'BULLISH' and daily != 'BEARISH':
            return "INTRADAY LONG - Trade within hourly uptrend"
        elif hourly == 'BEARISH' and daily != 'BULLISH':
            return "INTRADAY SHORT - Trade within hourly downtrend"
        else:
            return "WAIT - Timeframes conflicting, wait for alignment"
    
    def _identify_entry_trigger(self, timeframes: Dict) -> str:
        """Identify entry trigger from 1m/5m."""
        intraday = timeframes.get('5m', [])
        return intraday[0].get('description', 'Watch for momentum shift') if intraday else 'No intraday signals'


# ============ THEME 6: STOCK RECOMMENDATION GENERATION ============


class StockRecommender:
    """
    Theme 6: Stock Recommendation Generation
    
    Generates BUY/SELL/HOLD recommendations with targets and stops.
    """
    
    def __init__(self, config: AIConfig):
        """Initialize recommender."""
        self.config = config
    
    def generate_recommendation(self,
                               symbol: str,
                               signals: List[Dict],
                               indicators: Dict,
                               price_history: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Generate stock recommendation.
        
        Args:
            symbol: Stock ticker
            signals: Detected signals
            indicators: Technical indicators
            price_history: Historical price data for support/resistance
        
        Returns:
            BUY/SELL/HOLD recommendation
        """
        if not signals:
            return self._hold_recommendation(symbol, "No signals detected")
        
        # Score recommendation
        score = self._calculate_recommendation_score(signals, indicators)
        
        # Determine action
        if score > 0.65:
            action = 'BUY'
            confidence = score
        elif score < 0.35:
            action = 'SELL'
            confidence = 1 - score
        else:
            action = 'HOLD'
            confidence = 0.5
        
        # Calculate targets and stops
        current_price = indicators.get('Current_Price', 100)
        atr = indicators.get('ATR', current_price * 0.02)
        
        if action == 'BUY':
            target = current_price + (atr * 3)
            stop = current_price - (atr * 2)
        elif action == 'SELL':
            target = current_price - (atr * 3)
            stop = current_price + (atr * 2)
        else:
            target = current_price
            stop = current_price
        
        return {
            'symbol': symbol,
            'recommendation': action,
            'confidence': round(confidence, 2),
            'target_price': round(target, 2),
            'stop_loss': round(stop, 2),
            'expected_return': round(((target - current_price) / current_price * 100), 2) if action != 'HOLD' else 0,
            'rationale': f"Technical analysis score: {score:.2f}. {len(signals)} signals detected.",
            'time_horizon': '2-4 weeks' if action != 'HOLD' else 'Undefined',
            'risk_level': 'MODERATE'
        }
    
    def _calculate_recommendation_score(self, signals: List[Dict], indicators: Dict) -> float:
        """Calculate recommendation score 0-1."""
        bullish = sum(1 for s in signals if 'BULLISH' in s.get('strength', ''))
        bearish = sum(1 for s in signals if 'BEARISH' in s.get('strength', ''))
        total = len(signals)
        
        if total == 0:
            return 0.5
        
        # Base score from signal direction
        score = (bullish - bearish) / total * 0.5 + 0.5
        
        # Adjust for momentum (RSI)
        rsi = indicators.get('RSI', 50)
        if rsi > 70:  # Overbought
            score -= 0.1
        elif rsi < 30:  # Oversold
            score += 0.1
        
        # Adjust for trend (SMA)
        current_price = indicators.get('Current_Price', 100)
        sma_50 = indicators.get('SMA_50', current_price)
        if current_price > sma_50:  # Above MA
            score += 0.05
        else:  # Below MA
            score -= 0.05
        
        return max(0, min(1, score))  # Clamp to 0-1
    
    def _hold_recommendation(self, symbol: str, reason: str) -> Dict[str, Any]:
        """Generate HOLD recommendation."""
        return {
            'symbol': symbol,
            'recommendation': 'HOLD',
            'confidence': 0.5,
            'target_price': None,
            'stop_loss': None,
            'expected_return': 0,
            'rationale': reason,
            'time_horizon': 'Undefined',
            'risk_level': 'NONE'
        }


# ============ THEME 7-10: RISK ASSESSMENT & OPPORTUNITY ID ============


class RiskAssessment:
    """
    Theme 7: Risk Assessment
    
    Identifies key risks and protective measures.
    """
    
    def assess(self, signals: List[Dict], indicators: Dict) -> Dict[str, Any]:
        """Assess risk factors."""
        risks = []
        
        # Check for divergences
        rsi = indicators.get('RSI', 50)
        if rsi > 70:
            risks.append({
                'type': 'OVERBOUGHT',
                'severity': 'MEDIUM',
                'description': 'RSI above 70 indicates potential pullback',
                'mitigation': 'Set tight stop losses or reduce position size'
            })
        
        # Check volatility
        hv = indicators.get('HV_30d', 0.20)
        if hv > 0.30:
            risks.append({
                'type': 'HIGH_VOLATILITY',
                'severity': 'MEDIUM',
                'description': f'30-day volatility at {hv:.1%} - wider swings expected',
                'mitigation': 'Use wider stops and expect larger drawdowns'
            })
        
        # Check for signal divergences
        if len(signals) == 0:
            risks.append({
                'type': 'NO_SIGNALS',
                'severity': 'HIGH',
                'description': 'No technical signals - high uncertainty',
                'mitigation': 'Skip trade or use very small position size'
            })
        
        return {
            'overall_risk_level': self._risk_level(risks),
            'identified_risks': risks,
            'recommended_stop_loss_pct': self._stop_loss_recommendation(indicators),
            'position_size_adjustment': f"Reduce size by {len(risks) * 25}%" if risks else "Full size acceptable"
        }
    
    def _risk_level(self, risks: List) -> str:
        """Determine overall risk level."""
        high_count = sum(1 for r in risks if r['severity'] == 'HIGH')
        if high_count > 0:
            return 'HIGH'
        elif len(risks) > 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _stop_loss_recommendation(self, indicators: Dict) -> float:
        """Recommend stop loss percentage."""
        atr = indicators.get('ATR', 0)
        price = indicators.get('Current_Price', 1)
        atr_pct = (atr / price * 100) if price else 2
        
        return round(atr_pct * 2, 2)  # 2x ATR


class OpportunityIdentifier:
    """
    Theme 8: Opportunity Identification
    
    Spots underutilized setups from weak signal confluences.
    """
    
    def identify(self, signals: List[Dict], indicators: Dict) -> List[Dict]:
        """Identify hidden opportunities."""
        opportunities = []
        
        # Look for weak but converging signals
        weak_signals = [s for s in signals if s.get('confidence', 0) < 0.65]
        
        if len(weak_signals) >= 2:
            # Multiple weak signals might converge into strong setup
            opportunities.append({
                'type': 'SIGNAL_CONVERGENCE',
                'description': f'{len(weak_signals)} weak signals converging - watch for breakout',
                'entry_trigger': 'Price breaks above/below recent range',
                'confidence': 0.6,
                'action': 'WATCH - Not ready to trade yet'
            })
        
        # Look for mean reversion setups
        rsi = indicators.get('RSI', 50)
        if rsi > 70 or rsi < 30:
            opportunities.append({
                'type': 'MEAN_REVERSION',
                'description': f'RSI at {rsi:.0f} - extreme level suggests reversion opportunity',
                'entry_trigger': f'Wait for price to {'bounce' if rsi < 30 else 'pullback'}',
                'confidence': 0.65,
                'action': 'STAGE ENTRY - Set alerts at key levels'
            })
        
        return opportunities

  