"""
Tests pour le CryptoPriceAPI (v2.1)

Ce module teste les fonctionnalités de récupération de prix crypto :
- Récupération prix BTC/EUR
- Conversion BTC → EUR
- Récupération prix crypto générique
- Gestion du cache
- Gestion des erreurs

Version: v2.1
Auteur: Claude Code
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.crypto_price_api import CryptoPriceAPI


class TestCryptoPriceAPI:
    """Tests du CryptoPriceAPI."""

    def test_init(self):
        """Test l'initialisation de l'API."""
        api = CryptoPriceAPI()

        assert api.base_url == "https://api.coingecko.com/api/v3"
        assert api.cache == {}
        assert hasattr(api, 'logger')

    @patch('tools.crypto_price_api.requests.get')
    def test_get_btc_price_eur_success(self, mock_get):
        """Test récupération réussie du prix BTC/EUR."""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.json.return_value = {'bitcoin': {'eur': 45000.50}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()
        price = api.get_btc_price_eur()

        assert price == 45000.50
        assert api.cache['btc_eur'] == 45000.50
        mock_get.assert_called_once()

    @patch('tools.crypto_price_api.requests.get')
    def test_get_btc_price_eur_uses_cache(self, mock_get):
        """Test que le prix est récupéré du cache lors du 2ème appel."""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.json.return_value = {'bitcoin': {'eur': 45000.50}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()

        # Premier appel
        price1 = api.get_btc_price_eur()
        # Deuxième appel (devrait utiliser le cache)
        price2 = api.get_btc_price_eur()

        assert price1 == price2
        # L'API ne devrait être appelée qu'une fois
        assert mock_get.call_count == 1

    @patch('tools.crypto_price_api.requests.get')
    def test_get_btc_price_eur_api_error(self, mock_get):
        """Test gestion erreur réseau."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        api = CryptoPriceAPI()
        price = api.get_btc_price_eur()

        assert price is None

    @patch('tools.crypto_price_api.requests.get')
    def test_get_btc_price_eur_invalid_response(self, mock_get):
        """Test gestion réponse API invalide."""
        # Mock de réponse sans prix
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()
        price = api.get_btc_price_eur()

        assert price is None

    @patch('tools.crypto_price_api.requests.get')
    def test_get_btc_price_eur_http_error(self, mock_get):
        """Test gestion erreur HTTP (404, 500, etc.)."""
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()
        price = api.get_btc_price_eur()

        assert price is None

    @patch('tools.crypto_price_api.requests.get')
    def test_convert_btc_to_eur_success(self, mock_get):
        """Test conversion BTC → EUR."""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.json.return_value = {'bitcoin': {'eur': 50000.0}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()
        eur_amount = api.convert_btc_to_eur(2.5)

        assert eur_amount == 125000.0  # 2.5 BTC * 50000 EUR

    @patch('tools.crypto_price_api.requests.get')
    def test_convert_btc_to_eur_api_error(self, mock_get):
        """Test conversion quand l'API échoue."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        api = CryptoPriceAPI()
        eur_amount = api.convert_btc_to_eur(2.5)

        assert eur_amount is None

    @patch('tools.crypto_price_api.requests.get')
    def test_convert_btc_to_eur_zero(self, mock_get):
        """Test conversion de 0 BTC."""
        mock_response = Mock()
        mock_response.json.return_value = {'bitcoin': {'eur': 50000.0}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()
        eur_amount = api.convert_btc_to_eur(0)

        assert eur_amount == 0.0

    @patch('tools.crypto_price_api.requests.get')
    def test_get_crypto_price_ethereum(self, mock_get):
        """Test récupération prix Ethereum."""
        mock_response = Mock()
        mock_response.json.return_value = {'ethereum': {'eur': 3500.75}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()
        price = api.get_crypto_price('ethereum', 'eur')

        assert price == 3500.75
        assert api.cache['ethereum_eur'] == 3500.75

    @patch('tools.crypto_price_api.requests.get')
    def test_get_crypto_price_usd(self, mock_get):
        """Test récupération prix en USD."""
        mock_response = Mock()
        mock_response.json.return_value = {'bitcoin': {'usd': 55000.0}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()
        price = api.get_crypto_price('bitcoin', 'usd')

        assert price == 55000.0
        assert api.cache['bitcoin_usd'] == 55000.0

    @patch('tools.crypto_price_api.requests.get')
    def test_get_crypto_price_uses_cache(self, mock_get):
        """Test que get_crypto_price utilise le cache."""
        mock_response = Mock()
        mock_response.json.return_value = {'ethereum': {'eur': 3500.0}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()

        # Premier appel
        price1 = api.get_crypto_price('ethereum', 'eur')
        # Deuxième appel (devrait utiliser le cache)
        price2 = api.get_crypto_price('ethereum', 'eur')

        assert price1 == price2
        # L'API ne devrait être appelée qu'une fois
        assert mock_get.call_count == 1

    @patch('tools.crypto_price_api.requests.get')
    def test_get_crypto_price_different_currencies_separate_cache(self, mock_get):
        """Test que différentes devises utilisent des entrées de cache séparées."""
        mock_responses = [
            Mock(json=lambda: {'bitcoin': {'eur': 45000.0}}, raise_for_status=Mock()),
            Mock(json=lambda: {'bitcoin': {'usd': 55000.0}}, raise_for_status=Mock())
        ]
        mock_get.side_effect = mock_responses

        api = CryptoPriceAPI()

        price_eur = api.get_crypto_price('bitcoin', 'eur')
        price_usd = api.get_crypto_price('bitcoin', 'usd')

        assert price_eur == 45000.0
        assert price_usd == 55000.0
        assert 'bitcoin_eur' in api.cache
        assert 'bitcoin_usd' in api.cache
        # Deux appels API distincts
        assert mock_get.call_count == 2

    @patch('tools.crypto_price_api.requests.get')
    def test_get_crypto_price_invalid_crypto_id(self, mock_get):
        """Test avec un ID crypto invalide."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()
        price = api.get_crypto_price('invalid_coin', 'eur')

        assert price is None

    @patch('tools.crypto_price_api.requests.get')
    def test_get_crypto_price_timeout(self, mock_get):
        """Test gestion timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        api = CryptoPriceAPI()
        price = api.get_crypto_price('bitcoin', 'eur')

        assert price is None

    @patch('tools.crypto_price_api.requests.get')
    def test_cache_isolation_between_methods(self, mock_get):
        """Test que le cache est partagé entre les méthodes."""
        mock_response = Mock()
        mock_response.json.return_value = {'bitcoin': {'eur': 50000.0}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api = CryptoPriceAPI()

        # Utiliser get_crypto_price pour mettre en cache
        price1 = api.get_crypto_price('bitcoin', 'eur')

        # Modifier le cache pour 'btc_eur' (clé utilisée par get_btc_price_eur)
        api.cache['btc_eur'] = 50000.0

        # get_btc_price_eur devrait utiliser le cache
        price2 = api.get_btc_price_eur()

        assert price2 == 50000.0
        # Un seul appel API (pour get_crypto_price)
        assert mock_get.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
