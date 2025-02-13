import random
import requests
from decimal import Decimal
from django.conf import settings
from .models import ExchangeRateProvider


class CurrencyProviderBase:
    def get_rate(self, source_currency, exchanged_currency, valuation_date):
        """
        Must be implemented by the subclass.
        Should return a Decimal representing the exchange rate.
        """
        raise NotImplementedError


class CurrencyBeaconProvider(CurrencyProviderBase):
    def get_rate(self, source_currency, exchanged_currency, valuation_date):
        """
        Retrieve exchange rate data from the CurrencyBeacon API.
        """
        api_key = settings.CURRENCY_BEACON_API_KEY
        base_url = settings.CURRENCY_BEACON_BASE_URL
        url = f"{base_url}/latest"
        params = {
            'api_key': api_key,
            'base': source_currency.code,
            'symbols': exchanged_currency.code,
            'date': valuation_date.isoformat(),
        }
        print("In Real Call")
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception("CurrencyBeacon API error")
        data = response.json()
        rate = data.get('rates')
        if not rate:
            raise Exception("No rate data returned from CurrencyBeacon")
        return Decimal(rate[exchanged_currency.code])


class MockProvider(CurrencyProviderBase):
    def get_rate(self, source_currency, exchanged_currency, valuation_date):
        """
        Generate random mock data.
        """
        print("In Mock")
        rate = random.uniform(0.5, 1.5)
        return Decimal(f"{rate:.6f}")


# Mapping of provider names to their corresponding classes.
PROVIDER_CLASSES = {
    'CurrencyBeacon': CurrencyBeaconProvider,
    'Mock': MockProvider,
}


def get_exchange_rate_data(source_currency, exchanged_currency, valuation_date, provider_name=None):
    """
    Retrieves exchange rate data using the specified provider (if provided)
    or, if not specified, using all active providers ordered by priority.
    In case one provider fails, fallback to the next one.

    :param source_currency: Currency instance (source)
    :param exchanged_currency: Currency instance (target)
    :param valuation_date: date object
    :param provider_name: Optional string (e.g., 'Mock' or 'CurrencyBeacon')
    :return: Decimal exchange rate
    """
    providers_to_try = []
    if provider_name:
        try:
            config = ExchangeRateProvider.objects.get(name=provider_name, active=True)
            providers_to_try.append((config.priority, provider_name))
        except ExchangeRateProvider.DoesNotExist:
            raise Exception(f"Provider {provider_name} not available or inactive.")
    else:
        configs = ExchangeRateProvider.objects.filter(active=True).order_by('priority')
        providers_to_try = [(config.priority, config.name) for config in configs]

    if not providers_to_try:
        raise Exception("No active providers available.")

    last_exception = None
    for _, pname in providers_to_try:
        provider_class = PROVIDER_CLASSES.get(pname)
        if not provider_class:
            continue
        provider_instance = provider_class()
        try:
            rate = provider_instance.get_rate(source_currency, exchanged_currency, valuation_date)
            if rate:
                return rate
        except Exception as e:
            last_exception = e
            continue
    if last_exception:
        raise last_exception
    raise Exception("Failed to retrieve exchange rate data.")