"""
Market data validation.

Validates market data before processing to catch issues early
and provide clear error messages.
"""

import pandas as pd
import numpy as np
from typing import Set, Tuple
from logging_config import get_logger
from exceptions import DataValidationError, InsufficientDataError

logger = get_logger()


# ============ CONSTANTS ============

REQUIRED_COLUMNS: Set[str] = {"Open", "High", "Low", "Close", "Volume"}

MIN_BARS_FOR_ANALYSIS = 50
MIN_BARS_FOR_INDICATORS = {
    "ma_50": 50,
    "ma_200": 200,
    "rsi_14": 14,
    "macd_26": 26,
    "bb_20": 20,
    "atr_14": 14,
    "adx_14": 14,
}


# ============ DATA VALIDATOR ============


class MarketDataValidator:
    """
    Validates market data for integrity and completeness.

    Checks for:
    - Required columns present
    - Valid data types
    - No all-NaN columns
    - Sufficient data points
    - Valid price ranges
    - Non-negative volume
    """

    @staticmethod
    def validate(df: pd.DataFrame, symbol: str = "UNKNOWN") -> pd.DataFrame:
        """
        Validate market data and return cleaned copy.

        Performs all validation checks and raises appropriate exceptions
        if data is invalid. Returns a copy of the validated DataFrame
        with minor cleaning applied.

        Args:
            df: Market data DataFrame from yfinance.
            symbol: Stock symbol (for error messages).

        Returns:
            Validated DataFrame (copy of input with minor cleaning).

        Raises:
            DataValidationError: If validation fails.
            InsufficientDataError: If not enough data points.

        Example:
            >>> ticker = yf.Ticker('SPY')
            >>> data = ticker.history(period='60d', interval='5m')
            >>> validated = MarketDataValidator.validate(data, 'SPY')
        """
        logger.debug(f"Validating {symbol}: {len(df)} bars")

        # Check if dataframe is empty
        MarketDataValidator._check_empty(df, symbol)

        # Check required columns
        MarketDataValidator._check_required_columns(df, symbol)

        # Check data types
        MarketDataValidator._check_data_types(df, symbol)

        # Check for all-NaN columns
        MarketDataValidator._check_all_nan_columns(df, symbol)

        # Check for sufficient data
        MarketDataValidator._check_sufficient_data(df, symbol)

        # Check valid price ranges
        MarketDataValidator._check_valid_prices(df, symbol)

        # Check non-negative volume
        MarketDataValidator._check_valid_volume(df, symbol)

        # Return cleaned copy
        df_clean = df.copy()
        logger.info(f"Data validation passed for {symbol}: {len(df_clean)} bars")
        return df_clean

    @staticmethod
    def _check_empty(df: pd.DataFrame, symbol: str) -> None:
        """
        Check that dataframe is not empty.

        Raises:
            DataValidationError: If dataframe is empty.
        """
        if df.empty:
            raise DataValidationError(
                f"No market data returned for {symbol}",
                reason="empty_dataframe",
            )

    @staticmethod
    def _check_required_columns(df: pd.DataFrame, symbol: str) -> None:
        """
        Check that all required columns are present.

        Raises:
            DataValidationError: If required columns are missing.
        """
        missing = REQUIRED_COLUMNS - set(df.columns)
        
        if missing:
            raise DataValidationError(
                f"Missing required columns: {missing}",
                column=", ".join(sorted(missing)),
                reason="missing_columns",
            )

    @staticmethod
    def _check_data_types(df: pd.DataFrame, symbol: str) -> None:
        """
        Check that column data types are valid.

        Raises:
            DataValidationError: If data types are invalid.
        """
        price_columns = {"Open", "High", "Low", "Close"}
        volume_columns = {"Volume"}
        
        # Check price columns are numeric
        for col in price_columns:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise DataValidationError(
                        f"Column {col} must be numeric",
                        column=col,
                        reason="invalid_dtype",
                    )
        
        # Check volume is numeric
        for col in volume_columns:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise DataValidationError(
                        f"Column {col} must be numeric",
                        column=col,
                        reason="invalid_dtype",
                    )

    @staticmethod
    def _check_all_nan_columns(df: pd.DataFrame, symbol: str) -> None:
        """
        Check that no required columns are entirely NaN.

        Raises:
            DataValidationError: If any required column is all NaN.
        """
        for col in REQUIRED_COLUMNS:
            if col in df.columns:
                if df[col].isna().all():
                    raise DataValidationError(
                        f"Column {col} contains only NaN values",
                        column=col,
                        reason="all_nan",
                    )

    @staticmethod
    def _check_sufficient_data(df: pd.DataFrame, symbol: str) -> None:
        """
        Check that there are enough data points for analysis.

        Raises:
            InsufficientDataError: If data count is below minimum.
        """
        if len(df) < MIN_BARS_FOR_ANALYSIS:
            raise InsufficientDataError(
                f"Insufficient data for analysis",
                required=MIN_BARS_FOR_ANALYSIS,
                actual=len(df),
                indicator="general_analysis",
            )

    @staticmethod
    def _check_valid_prices(df: pd.DataFrame, symbol: str) -> None:
        """
        Check that prices are in valid ranges.

        Validates:
        - All prices are positive
        - High >= Low for each bar
        - Close is between High and Low (mostly)

        Raises:
            DataValidationError: If price validation fails.
        """
        # Check for negative prices
        for col in {"Open", "High", "Low", "Close"}:
            if col in df.columns:
                if (df[col] < 0).any():
                    raise DataValidationError(
                        f"Column {col} contains negative prices",
                        column=col,
                        reason="negative_price",
                    )

        # Check High >= Low
        if "High" in df.columns and "Low" in df.columns:
            invalid = df["High"] < df["Low"]
            if invalid.any():
                invalid_count = invalid.sum()
                raise DataValidationError(
                    f"{invalid_count} bars have High < Low",
                    column="High/Low",
                    reason="invalid_range",
                    value_count=invalid_count,
                )

    @staticmethod
    def _check_valid_volume(df: pd.DataFrame, symbol: str) -> None:
        """
        Check that volume is non-negative.

        Raises:
            DataValidationError: If volume is negative.
        """
        if "Volume" in df.columns:
            if (df["Volume"] < 0).any():
                raise DataValidationError(
                    "Volume contains negative values",
                    column="Volume",
                    reason="negative_volume",
                )

    @staticmethod
    def check_for_indicator(df: pd.DataFrame, indicator_name: str) -> bool:
        """
        Check if dataframe has sufficient bars for an indicator.

        Useful for conditional indicator calculation.

        Args:
            df: Market data DataFrame.
            indicator_name: Name of indicator (e.g., 'ma_200', 'adx_14').

        Returns:
            True if sufficient bars for indicator, False otherwise.
        """
        min_bars = MIN_BARS_FOR_INDICATORS.get(indicator_name, 50)
        return len(df) >= min_bars


# ============ DATA CLEANER ============


class MarketDataCleaner:
    """
    Cleans market data for analysis.

    Handles common data quality issues without losing information:
    - Forward-fill small gaps
    - Remove duplicates
    - Sort by time
    """

    @staticmethod
    def clean(df: pd.DataFrame, symbol: str = "UNKNOWN") -> pd.DataFrame:
        """
        Clean market data for analysis.

        Performs non-destructive cleaning:
        - Removes duplicate timestamps
        - Sorts by timestamp
        - Forward-fills small gaps (max 2 periods)
        - Ensures numeric columns have no inf values

        Args:
            df: Raw market data.
            symbol: Stock symbol (for logging).

        Returns:
            Cleaned DataFrame.

        Example:
            >>> data = yf.Ticker('SPY').history(period='1d', interval='1m')
            >>> cleaned = MarketDataCleaner.clean(data, 'SPY')
        """
        df_clean = df.copy()
        initial_rows = len(df_clean)

        # Remove duplicate timestamps
        df_clean = df_clean[~df_clean.index.duplicated(keep='first')]

        # Sort by timestamp
        df_clean = df_clean.sort_index()

        # Forward-fill small gaps (max 2 periods)
        for col in df_clean.columns:
            if pd.api.types.is_numeric_dtype(df_clean[col]):
                df_clean[col] = df_clean[col].fillna(method='ffill', limit=2)

        # Replace inf with NaN
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan)

        rows_removed = initial_rows - len(df_clean)
        if rows_removed > 0:
            logger.info(f"Cleaning {symbol}: removed {rows_removed} duplicate rows")

        return df_clean


# ============ DATA VALIDATION PIPELINE ============


class DataValidationPipeline:
    """
    Complete pipeline for validating market data.

    Combines validation and cleaning into a single operation.
    """

    @staticmethod
    def process(df: pd.DataFrame, symbol: str = "UNKNOWN") -> pd.DataFrame:
        """
        Process market data through validation and cleaning pipeline.

        Args:
            df: Raw market data from yfinance.
            symbol: Stock symbol (for logging and errors).

        Returns:
            Validated and cleaned DataFrame ready for analysis.

        Raises:
            DataValidationError: If validation fails.
            InsufficientDataError: If not enough data.

        Example:
            >>> data = yf.Ticker('SPY').history(period='1d', interval='5m')
            >>> validated = DataValidationPipeline.process(data, 'SPY')
            >>> # Now safe to use for analysis
        """
        logger.debug(f"Processing data for {symbol}")

        # Step 1: Clean
        df_clean = MarketDataCleaner.clean(df, symbol)

        # Step 2: Validate
        df_validated = MarketDataValidator.validate(df_clean, symbol)

        logger.info(f"Data pipeline complete for {symbol}: {len(df_validated)} bars")

        return df_validated