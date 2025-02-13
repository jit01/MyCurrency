from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Currency, CurrencyExchangeRate
from .serializers import CurrencySerializer, CurrencyExchangeRateSerializer
from datetime import datetime
from .providers import get_exchange_rate_data


class CurrencyViewSet(viewsets.ModelViewSet):
    """
    CRUD API for currencies.
    """
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


class ExchangeRateListView(APIView):
    """
    Retrieve a list (time series) of exchange rates for a specific period.
    Query parameters:
      - source_currency (code)
      - date_from (YYYY-MM-DD)
      - date_to (YYYY-MM-DD)
    """

    def get(self, request):
        source_code = request.query_params.get('source_currency')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if not (source_code and date_from and date_to):
            return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            source_currency = Currency.objects.get(code=source_code)
        except Currency.DoesNotExist:
            return Response({'error': 'Source currency not found'}, status=status.HTTP_404_NOT_FOUND)

        rates = CurrencyExchangeRate.objects.filter(
            source_currency=source_currency,
            valuation_date__range=(date_from_obj, date_to_obj)
        )
        serializer = CurrencyExchangeRateSerializer(rates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConvertAmountView(APIView):
    """
    Convert an amount from one currency to another using the latest exchange rate.
    Query parameters:
      - source_currency (code)
      - exchanged_currency (code)
      - amount (decimal)
    """

    def get(self, request):
        source_code = request.query_params.get('source_currency')
        target_code = request.query_params.get('exchanged_currency')
        amount = request.query_params.get('amount')

        if not (source_code and target_code and amount):
            return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(amount)
        except ValueError:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            source_currency = Currency.objects.get(code=source_code)
            target_currency = Currency.objects.get(code=target_code)
        except Currency.DoesNotExist:
            return Response({'error': 'Currency not found'}, status=status.HTTP_404_NOT_FOUND)

        # Try to get today's exchange rate; if not available, fetch from providers.
        from datetime import date
        today = date.today()
        rate_obj = CurrencyExchangeRate.objects.filter(
            source_currency=source_currency,
            exchanged_currency=target_currency,
            valuation_date=today
        ).order_by('-valuation_date').first()

        if not rate_obj:
            try:
                rate_value = get_exchange_rate_data(source_currency, target_currency, today)
                rate_obj = CurrencyExchangeRate.objects.create(
                    source_currency=source_currency,
                    exchanged_currency=target_currency,
                    valuation_date=today,
                    rate_value=rate_value
                )
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            rate_value = rate_obj.rate_value

        converted_amount = amount * float(rate_value)
        response_data = {
            'source_currency': source_code,
            'exchanged_currency': target_code,
            'amount': amount,
            'rate': float(rate_value),
            'converted_amount': converted_amount,
            'valuation_date': rate_obj.valuation_date
        }
        return Response(response_data, status=status.HTTP_200_OK)

def home(request):
    rates = CurrencyExchangeRate.objects.all().order_by('-valuation_date')[:10]
    return render(request, 'index.html', {'rates': rates})

def convert_currency(request):
    target_code, amount, source_code = None, None, None
    currencies = Currency.objects.all()
    result = None

    if request.method == "POST":
        source_code = request.POST['source_currency']
        target_code = request.POST['target_currency']
        amount = float(request.POST['amount'])

        source = Currency.objects.get(code=source_code)
        target = Currency.objects.get(code=target_code)
        rate = CurrencyExchangeRate.objects.filter(
            source_currency=source, exchanged_currency=target
        ).order_by('-valuation_date').first()

        if rate:
            result = amount * float(rate.rate_value)

    return render(request, 'convert.html', {'currencies': currencies, 'result': result,'source_selected': source_code,
        'target_selected': target_code,
        'amount_entered': amount,})

def exchange_history(request):
    history = CurrencyExchangeRate.objects.all().order_by('-valuation_date')
    return render(request, 'history.html', {'history': history})