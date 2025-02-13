"""
URL configuration for mycurrency project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from currency.admin import admin_site
from currency.views import home,convert_currency,exchange_history

urlpatterns = [
    path('admin/', admin_site.urls), # This admin to use extra interface to calculate currency
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('convert/', convert_currency, name='convert_currency'),
    path('history/', exchange_history, name='exchange_history'),
    path('api/v1/', include('currency.urls')),

]
