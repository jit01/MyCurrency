from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django import forms
from .models import Currency, CurrencyExchangeRate, ExchangeRateProvider
from .providers import get_exchange_rate_data
from datetime import date

# Register models in Django Admin
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol')

@admin.register(CurrencyExchangeRate)
class CurrencyExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('source_currency', 'exchanged_currency', 'valuation_date', 'rate_value')

@admin.register(ExchangeRateProvider)
class ExchangeRateProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'active')

# Currency Converter Form
class CurrencyConverterForm(forms.Form):
    source_currency = forms.ModelChoiceField(
        queryset=Currency.objects.all(),
        label="Source Currency"
    )
    target_currencies = forms.ModelMultipleChoiceField(
        queryset=Currency.objects.all(),
        label="Target Currencies"
    )
    amount = forms.DecimalField(decimal_places=2, max_digits=18, label="Amount")

# Custom Admin View
class MyAdminSite(admin.AdminSite):
    site_header = 'MyCurrency Administration'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('currency-converter/', self.admin_view(self.currency_converter_view), name='currency_converter'),
        ]
        return custom_urls + urls

    def currency_converter_view(self, request):
        result = None
        if request.method == 'POST':
            form = CurrencyConverterForm(request.POST)
            if form.is_valid():
                source_currency = form.cleaned_data['source_currency']
                target_currencies = form.cleaned_data['target_currencies']
                amount = form.cleaned_data['amount']
                result = {}

                valuation_date = date.today()  # Use today's date for the exchange rate

                for target in target_currencies:
                    try:
                        rate = get_exchange_rate_data(source_currency, target, valuation_date)
                        converted = amount * rate
                        result[target.code] = {
                            'rate': rate,
                            'converted_amount': converted
                        }
                    except Exception as e:
                        result[target.code] = {
                            'error': str(e)
                        }
        else:
            form = CurrencyConverterForm()

        context = {
            'form': form,
            'result': result,
        }
        return render(request, 'admin/currency_converter.html', context)

# Replace default Django admin with custom admin
admin_site = MyAdminSite(name='myadmin')

admin_site.register(Currency, CurrencyAdmin)
admin_site.register(CurrencyExchangeRate, CurrencyExchangeRateAdmin)
admin_site.register(ExchangeRateProvider, ExchangeRateProviderAdmin)