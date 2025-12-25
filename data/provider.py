"""
Market data provider with caching, retry logic, and async support.

Handles data fetching, caching, retries, and period validation.
Supports both synchronous and asynchronous operations (Pattern 18).

Design Patterns:
    - Async/Await: Non-blocking I/O for data fetching
    - Template Method: fetch() defines algorithm, subclasses implement details
    - Strategy: Swappable provider implementations
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import pandas as pd
from logging_config import get_logger
from exceptions import DataFetchError, SymbolError

logger = get_logger()


# ============ DATA PROVIDER INTERFACE ============


class DataProvider(ABC):
    """
    Abstract base class for market data providers.

    All data providers must implement this interface.
    Supports both sync and async operations.
    """

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        interval: str,
        period: str,
    ) -> pd.DataFrame:
        """
        Fetch market data (synchronous).

        Args:
            symbol: Stock symbol (e.g., 'SPY').
            interval: Timeframe (e.g., '1d', '1h', '5m').
            period: Data period (e.g., '1y', '60d', 'max').

        Returns:
            Market data DataFrame with OHLCV columns.

        Raises:
            DataFetchError: If fetch fails.
            SymbolError: If symbol is invalid/unavailable.
        """
        pass

    async def fetch_async(
        self,
        symbol: str,
        interval: str,
        period: str,
    ) -> pd.DataFrame:
        """
        Fetch market data (asynchronous).

        Default implementation wraps sync fetch() in asyncio.to_thread().
        Override for true async implementations.

        Args:
            symbol: Stock symbol (e.g., 'SPY').
            interval: Timeframe (e.g., '1d', '1h', '5m').
            period: Data period (e.g., '1y', '60d', 'max').

        Returns:
            Market data DataFrame with OHLCV columns.
        """
        return await asyncio.to_thread(self.fetch, symbol, interval, period)

    async def fetch_multiple_async(
        self,
        symbols: List[str],
        interval: str,
        period: str,
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols concurrently.

        Uses asyncio.gather() for parallel fetching.

        Args:
            symbols: List of stock symbols.
            interval: Timeframe for all symbols.
            period: Data period for all symbols.

        Returns:
            Dict mapping symbol to DataFrame (or None if failed).
        """
        async def fetch_one(symbol: str) -> Tuple[str, Optional[pd.DataFrame]]:
            try:
                data = await self.fetch_async(symbol, interval, period)
                return (symbol, data)
            except Exception as e:
                logger.error(f"Async fetch failed for {symbol}: {e}")
                return (symbol, None)

        results = await asyncio.gather(*[fetch_one(s) for s in symbols])
        return dict(results)


# ============ YFINANCE DATA PROVIDER ============


class YFinanceProvider(DataProvider):
    """
    Market data provider using yfinance.

    Provides access to stock data via Yahoo Finance with
    optional caching and retry logic.
    """

    # Maximum retries for failed requests
    MAX_RETRIES = 3

    # Timeout for yfinance requests
    TIMEOUT = 10

    def __init__(self, use_cache: bool = True, cache_ttl_minutes: int = 60):
        """
        Initialize YFinance provider.

        Args:
            use_cache: Enable response caching (default: True).
            cache_ttl_minutes: Cache lifetime in minutes (default: 60).

        Raises:
            ImportError: If yfinance not installed.
        """
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            raise ImportError(
                "yfinance is required. Install with: pip install yfinance"
            )

        self.use_cache = use_cache
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}

        logger.debug(f"Initialized YFinanceProvider (cache={use_cache})")

    def fetch(
        self,
        symbol: str,
        interval: str,
        period: str,
    ) -> pd.DataFrame:
        """
        Fetch market data from Yahoo Finance.

        Args:
            symbol: Stock symbol.
            interval: Timeframe.
            period: Data period.

        Returns:
            Market data DataFrame.

        Raises:
            SymbolError: If symbol invalid.
            DataFetchError: If fetch fails.
        """
        # Validate inputs
        self._validate_inputs(symbol, interval, period)

        # Check cache
        if self.use_cache:
            cached = self._get_cached(symbol, interval, period)
            if cached is not None:
                logger.debug(f"Cache hit: {symbol} [{interval}] {period}")
                return cached

        # Fetch with retries
        data = self._fetch_with_retry(symbol, interval, period)

        # Cache result
        if self.use_cache:
            self._cache_result(symbol, interval, period, data)

        return data

    def _validate_inputs(self, symbol: str, interval: str, period: str) -> None:
        """
        Validate input parameters.

        Args:
            symbol: Stock symbol.
            interval: Timeframe.
            period: Data period.

        Raises:
            SymbolError: If symbol invalid.
            DataFetchError: If parameters invalid.
        """
        if not symbol or not isinstance(symbol, str) or len(symbol) > 10:
            raise SymbolError(
                f"Invalid symbol format: {symbol}",
                symbol=symbol or "UNKNOWN",
            )

        valid_intervals = ["1m", "2m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]
        if interval not in valid_intervals:
            raise DataFetchError(
                f"Invalid interval: {interval}",
                interval=interval,
                reason="Must be one of: " + ", ".join(valid_intervals),
            )

        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"]
        period_variants = valid_periods + ["60d", "90d", "7d"]
        if period not in period_variants:
            logger.warning(f"Unusual period: {period}, attempting anyway")

    def _fetch_with_retry(
        self,
        symbol: str,
        interval: str,
        period: str,
    ) -> pd.DataFrame:
        """
        Fetch data with automatic retry logic.

        Args:
            symbol: Stock symbol.
            interval: Timeframe.
            period: Data period.

        Returns:
            Market data DataFrame.

        Raises:
            DataFetchError: If all retries fail.
            SymbolError: If symbol is invalid.
        """
        last_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"Fetching {symbol} [{interval}] {period} (attempt {attempt}/{self.MAX_RETRIES})"
                )

                ticker = self.yf.Ticker(symbol, session=None)
                data = ticker.history(
                    period=period,
                    interval=interval,
                    timeout=self.TIMEOUT,
                )

                if data.empty:
                    raise DataFetchError(
                        f"No data returned for {symbol}",
                        symbol=symbol,
                        interval=interval,
                        period=period,
                    )

                logger.info(
                    f"Fetched {symbol}: {len(data)} bars "
                    f"({data.index[0]} to {data.index[-1]})"
                )

                return data

            except Exception as e:
                error_msg = str(e)
                last_error = e

                # Check if symbol is invalid
                if "No data found" in error_msg or "Invalid" in error_msg:
                    raise SymbolError(
                        f"Symbol not found or invalid: {symbol}",
                        symbol=symbol,
                    ) from e

                # Retry on network/timeout errors
                if attempt < self.MAX_RETRIES:
                    logger.warning(
                        f"Fetch failed (attempt {attempt}): {error_msg}, retrying..."
                    )
                else:
                    logger.error(f"Fetch failed after {self.MAX_RETRIES} attempts")

        # All retries exhausted
        raise DataFetchError(
            f"Failed to fetch {symbol} after {self.MAX_RETRIES} attempts",
            symbol=symbol,
            reason=f"Last error: {last_error}",
        ) from last_error

    def _get_cached(
        self, symbol: str, interval: str, period: str
    ) -> Optional[pd.DataFrame]:
        """
        Get data from cache if available and fresh.

        Args:
            symbol: Stock symbol.
            interval: Timeframe.
            period: Data period.

        Returns:
            Cached DataFrame or None if not cached/stale.
        """
        cache_key = self._make_cache_key(symbol, interval, period)

        if cache_key not in self.cache:
            return None

        data, cached_at = self.cache[cache_key]
        age = datetime.now() - cached_at

        if age > self.cache_ttl:
            logger.debug(f"Cache expired for {cache_key}")
            del self.cache[cache_key]
            return None

        return data

    def _cache_result(
        self,
        symbol: str,
        interval: str,
        period: str,
        data: pd.DataFrame,
    ) -> None:
        """
        Cache fetch result.

        Args:
            symbol: Stock symbol.
            interval: Timeframe.
            period: Data period.
            data: Market data to cache.
        """
        cache_key = self._make_cache_key(symbol, interval, period)
        self.cache[cache_key] = (data, datetime.now())
        logger.debug(f"Cached: {cache_key}")

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cache.

        Args:
            symbol: Clear only this symbol, or all if None.
        """
        if symbol:
            prefix = symbol.upper()
            removed = [k for k in self.cache.keys() if k.startswith(prefix)]
            for k in removed:
                del self.cache[k]
            logger.info(f"Cleared cache for {symbol}: {len(removed)} entries")
        else:
            self.cache.clear()
            logger.info("Cleared all cache")

    @staticmethod
    def _make_cache_key(symbol: str, interval: str, period: str) -> str:
        """
        Create cache key.

        Args:
            symbol: Stock symbol.
            interval: Timeframe.
            period: Data period.

        Returns:
            Cache key string.
        """
        return f"{symbol.upper()}_{interval}_{period}"

    def __str__(self) -> str:
        """Return string representation."""
        return f"YFinanceProvider(cache={self.use_cache})"


# ============ MOCK DATA PROVIDER (FOR TESTING) ============


class MockDataProvider(DataProvider):
    """
    Mock data provider for testing.

    Returns synthetic OHLCV data without network calls.
    """

    def __init__(self, seed: int = 42):
        """
        Initialize mock provider.

        Args:
            seed: Random seed for reproducibility.
        """
        import numpy as np
        np.random.seed(seed)
        self.seed = seed
        logger.debug(f"Initialized MockDataProvider (seed={seed})")

    def fetch(
        self,
        symbol: str,
        interval: str,
        period: str,
    ) -> pd.DataFrame:
        """
        Generate synthetic market data.

        Args:
            symbol: Stock symbol.
            interval: Timeframe.
            period: Data period.

        Returns:
            Synthetic OHLCV DataFrame.
        """
        import numpy as np

        # Determine number of bars
        bars = self._period_to_bars(period, interval)

        # Generate synthetic prices (random walk)
        returns = np.random.normal(0.0005, 0.02, bars)
        close = 100 * np.exp(np.cumsum(returns))

        # Generate OHLCV
        dates = pd.date_range(end=pd.Timestamp.now(), periods=bars, freq=interval)

        df = pd.DataFrame(
            {
                "Open": close * (1 + np.random.uniform(-0.01, 0.01, bars)),
                "High": close * (1 + np.random.uniform(0, 0.02, bars)),
                "Low": close * (1 - np.random.uniform(0, 0.02, bars)),
                "Close": close,
                "Volume": np.random.randint(1000000, 5000000, bars),
            },
            index=dates,
        )

        logger.debug(f"Generated synthetic data: {symbol} {len(df)} bars")
        return df

    @staticmethod
    def _period_to_bars(period: str, interval: str) -> int:
        """Convert period string to bar count."""
        period_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 21,
            "3mo": 63,
            "6mo": 126,
            "1y": 252,
            "60d": 60,
            "7d": 7,
            "max": 252,
        }
        base_bars = period_map.get(period, 252)

        # Adjust for interval
        if interval == "1m":
            return base_bars * 390  # ~390 minutes per trading day
        elif interval == "5m":
            return base_bars * 78
        elif interval == "15m":
            return base_bars * 26
        elif interval == "1h":
            return base_bars * 6.5
        else:
            return base_bars

    def __str__(self) -> str:
        """Return string representation."""
        return f"MockDataProvider(seed={self.seed})"