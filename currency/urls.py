from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CurrencyViewSet, ExchangeRateListView, ConvertAmountView


router = DefaultRouter()
router.register(r'currencies', CurrencyViewSet, basename='currency')

urlpatterns = [
    path('', include(router.urls)),
    path('rates/', ExchangeRateListView.as_view(), name='exchange_rates'),
    path('convert/', ConvertAmountView.as_view(), name='convert_amount'),
]