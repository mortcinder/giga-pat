"""
Module pour récupérer les prix des cryptomonnaies.

Utilise l'API CoinGecko (gratuite, pas de clé API requise).

Version: v2.1
"""

import logging
import requests
from typing import Dict, Optional


class CryptoPriceAPI:
    """Client pour récupérer les prix crypto via CoinGecko API."""

    # Mapping ticker → CoinGecko ID (étendre au besoin)
    TICKER_TO_COINGECKO_ID = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'USDT': 'tether',
        'USDC': 'usd-coin',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'SOL': 'solana',
        'DOGE': 'dogecoin',
        'DOT': 'polkadot',
        'MATIC': 'matic-network',
        'LTC': 'litecoin',
        'LINK': 'chainlink',
        'AVAX': 'avalanche-2',
        'UNI': 'uniswap',
        'ATOM': 'cosmos',
        'VRO': 'veraone',  # VRO = VeraOne
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}  # Cache simple pour éviter les appels multiples

    def get_btc_price_eur(self) -> Optional[float]:
        """
        Récupère le prix actuel du BTC en EUR.

        Returns:
            Prix en EUR, ou None si erreur
        """
        if 'btc_eur' in self.cache:
            return self.cache['btc_eur']

        try:
            url = f"{self.base_url}/simple/price?ids=bitcoin&vs_currencies=eur"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            price = data.get('bitcoin', {}).get('eur')

            if price:
                self.cache['btc_eur'] = float(price)
                self.logger.info(f"Prix BTC/EUR récupéré: {price} €")
                return float(price)
            else:
                self.logger.error("Prix BTC non trouvé dans la réponse API")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur lors de la récupération du prix BTC: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erreur inattendue: {e}")
            return None

    def convert_btc_to_eur(self, btc_amount: float) -> Optional[float]:
        """
        Convertit un montant BTC en EUR.

        Args:
            btc_amount: Montant en BTC

        Returns:
            Montant en EUR, ou None si erreur
        """
        price = self.get_btc_price_eur()
        if price is None:
            return None

        return btc_amount * price

    def get_crypto_price(self, crypto_id: str, vs_currency: str = "eur") -> Optional[float]:
        """
        Récupère le prix d'une crypto donnée.

        Args:
            crypto_id: ID CoinGecko (bitcoin, ethereum, etc.)
            vs_currency: Devise de référence (eur, usd, etc.)

        Returns:
            Prix dans la devise, ou None si erreur
        """
        cache_key = f"{crypto_id}_{vs_currency}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            url = f"{self.base_url}/simple/price?ids={crypto_id}&vs_currencies={vs_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            price = data.get(crypto_id, {}).get(vs_currency)

            if price:
                self.cache[cache_key] = float(price)
                self.logger.info(f"Prix {crypto_id}/{vs_currency.upper()} récupéré: {price}")
                return float(price)
            else:
                self.logger.error(f"Prix {crypto_id} non trouvé dans la réponse API")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur lors de la récupération du prix {crypto_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erreur inattendue: {e}")
            return None

    def convert_crypto_to_eur(self, ticker: str, amount: float) -> Optional[float]:
        """
        Convertit un montant de crypto en EUR (méthode générique).

        Args:
            ticker: Ticker de la crypto (BTC, ETH, VRO, etc.)
            amount: Quantité de crypto

        Returns:
            Montant en EUR, ou None si ticker inconnu ou erreur API
        """
        # Normaliser le ticker (uppercase)
        ticker = ticker.upper().strip()

        # Chercher l'ID CoinGecko
        coingecko_id = self.TICKER_TO_COINGECKO_ID.get(ticker)

        if not coingecko_id:
            self.logger.warning(f"Ticker crypto inconnu: {ticker} (pas de mapping CoinGecko)")
            return None

        # Récupérer le prix
        price = self.get_crypto_price(coingecko_id, "eur")

        if price is None:
            return None

        return amount * price
