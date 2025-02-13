from django.db import models

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=20, db_index=True)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return self.code

class CurrencyExchangeRate(models.Model):
    source_currency = models.ForeignKey(
        Currency, related_name="exchange", on_delete=models.CASCADE
    )
    exchanged_currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    valuation_date = models.DateField(db_index=True)
    rate_value = models.DecimalField(max_digits=18, decimal_places=6, db_index=True)

    def __str__(self):
        return f"{self.source_currency} to {self.exchanged_currency} on {self.valuation_date}"

class ExchangeRateProvider(models.Model):
    """
    Model to configure exchange rate providers
    """
    name = models.CharField(max_length=50, unique=True)
    priority = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
