"""
Data package.

Provides data fetching and validation for market data.

Exports:
    DataProvider: Abstract base class for data providers.
    YFinanceProvider: Yahoo Finance implementation with caching.
    MockDataProvider: Mock provider for testing.
    MarketDataValidator: Validates market data integrity.
    MarketDataCleaner: Cleans and normalizes market data.
    DataValidationPipeline: Complete validation workflow.
"""

from __future__ import annotations

from data.provider import DataProvider, YFinanceProvider, MockDataProvider
from data.validator import MarketDataValidator, MarketDataCleaner, DataValidationPipeline

__all__ = [
    # Providers
    "DataProvider",
    "YFinanceProvider",
    "MockDataProvider",
    # Validation
    "MarketDataValidator",
    "MarketDataCleaner",
    "DataValidationPipeline",
]
