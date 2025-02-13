import asyncio
from datetime import timedelta
from asgiref.sync import sync_to_async
from .models import Currency, CurrencyExchangeRate
from .providers import get_exchange_rate_data

# Wrap ORM queries to make them work inside async functions
@sync_to_async(thread_sensitive=True)
def get_all_currencies():
    return list(Currency.objects.all())

@sync_to_async(thread_sensitive=True)
def save_exchange_rate(source, target, valuation_date, rate):
    return CurrencyExchangeRate.objects.create(
        source_currency=source,
        exchanged_currency=target,
        valuation_date=valuation_date,
        rate_value=rate
    )

async def fetch_rate(source_currency, target_currency, valuation_date):
    """ Fetch exchange rate asynchronously. """
    loop = asyncio.get_event_loop()
    rate = await loop.run_in_executor(
        None, get_exchange_rate_data, source_currency, target_currency, valuation_date, None
    )
    return rate

async def load_historical_data(start_date, end_date):
    """
    Load historical exchange rates asynchronously.
    """
    currencies = await get_all_currencies()  # 🔥 FIX: Wrapped inside sync_to_async

    if not currencies:
        print("No currencies found in the database.")
        return

    tasks_list = []
    current_date = start_date
    while current_date <= end_date:
        for source in currencies:
            for target in currencies:
                if source == target:
                    continue
                # Avoid duplicate fetches if data already exists
                exists = await sync_to_async(
                    lambda: CurrencyExchangeRate.objects.filter(
                        source_currency=source,
                        exchanged_currency=target,
                        valuation_date=current_date
                    ).exists(),
                    thread_sensitive=True
                )()

                if not exists:
                    tasks_list.append((source, target, current_date))
        current_date += timedelta(days=1)

    async def process_task(task):
        source, target, valuation_date = task
        try:
            rate = await fetch_rate(source, target, valuation_date)
            await save_exchange_rate(source, target, valuation_date, rate)  # 🔥 FIX: Wrapped inside sync_to_async
            print(f"Saved rate for {source} -> {target} on {valuation_date}: {rate}")
        except Exception as e:
            print(f"Error fetching rate for {source} -> {target} on {valuation_date}: {e}")

    # Limit concurrency with a semaphore (e.g., 10 concurrent tasks)
    semaphore = asyncio.Semaphore(10)
    async def sem_task(coro):
        async with semaphore:
            return await coro
    coros = [sem_task(process_task(task)) for task in tasks_list]
    await asyncio.gather(*coros)