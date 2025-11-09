"""
Parsers pour les documents du Crédit Agricole
Supporte PEA, PEA-PME, Assurance-vie au format PDF
"""

from .pea_v2025 import CreditAgricolePEA2025Parser
from .av_v2_lignes import CreditAgricoleAV2LignesParser

__all__ = [
    'CreditAgricolePEA2025Parser',
    'CreditAgricoleAV2LignesParser',
]
