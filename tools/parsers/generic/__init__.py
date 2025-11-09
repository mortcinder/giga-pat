"""
Parsers génériques pour formats standards (CSV, PDF tables, JSON)
"""

from .csv_flexible import GenericCSVParser

__all__ = [
    'GenericCSVParser',
]
