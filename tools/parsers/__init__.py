"""
Module de parsers pluggables pour différents formats de documents financiers
Architecture v2.0 - Strategy Pattern
"""

from .registry import ParserRegistry

__all__ = ['ParserRegistry']
