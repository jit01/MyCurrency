from django.core.management.base import BaseCommand
from datetime import datetime
import asyncio
from currency.tasks import load_historical_data

class Command(BaseCommand):
    help = 'Load historical exchange rate data asynchronously'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, help='Start date in YYYY-MM-DD')
        parser.add_argument('--end', type=str, help='End date in YYYY-MM-DD')

    def handle(self, *args, **options):
        start_date_str = options.get('start')
        end_date_str = options.get('end')

        if not (start_date_str and end_date_str):
            self.stdout.write(self.style.ERROR('Please provide both --start and --end dates in YYYY-MM-DD format'))
            return

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD.'))
            return

        self.stdout.write(f"Loading historical data from {start_date} to {end_date}...")

        # ✅ FIX: Ensure this is only run in a non-async environment
        try:
            asyncio.get_running_loop()
            self.stdout.write(self.style.ERROR("Cannot run asyncio.run() inside an existing event loop"))
        except RuntimeError:
            asyncio.run(load_historical_data(start_date, end_date))  # Call the async function properly

        self.stdout.write(self.style.SUCCESS("Historical data loading completed."))