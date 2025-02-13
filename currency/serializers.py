from rest_framework import serializers
from .models import Currency, CurrencyExchangeRate

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'

class CurrencyExchangeRateSerializer(serializers.ModelSerializer):
    source_currency = serializers.SlugRelatedField(slug_field='code', queryset=Currency.objects.all())
    exchanged_currency = serializers.SlugRelatedField(slug_field='code', queryset=Currency.objects.all())

    class Meta:
        model = CurrencyExchangeRate
        fields = '__all__'