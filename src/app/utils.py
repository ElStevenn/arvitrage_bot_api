from typing import Tuple



def get_crypto_logo(self, symbol: str) -> Tuple[str, str, str]:
    # ... (Your existing code for get_crypto_logo)
    pass

from datetime import datetime, timedelta
from typing import Literal
import pytz

class FundingFeeCalculator:
    def get_next_funding_fee_hour(self, delay: Literal[8, 4], ans=False):
        now = datetime.now(pytz.utc)
        timezone = pytz.timezone('Europe/Berlin')
        local_now = now.astimezone(timezone)
        is_summer = local_now.dst() != timedelta(0)
        funding_hour = 18 if is_summer else 17
        funding_time_today = local_now.replace(hour=funding_hour, minute=0, second=0, microsecond=0)
        if local_now >= funding_time_today:
            funding_time_today += timedelta(days=1)
        next_funding_time = funding_time_today + timedelta(hours=delay)
        if ans:
            return next_funding_time
        return funding_time_today

    def get_last_funding_fee_hour(self, delay: Literal[8, 4], ans=False):
        now = datetime.now(pytz.utc)
        timezone = pytz.timezone('Europe/Berlin')
        local_now = now.astimezone(timezone)
        is_summer = local_now.dst() != timedelta(0)
        funding_hour = 18 if is_summer else 17
        funding_time_today = local_now.replace(hour=funding_hour, minute=0, second=0, microsecond=0)
        if local_now < funding_time_today:
            funding_time_today -= timedelta(days=1)
        last_funding_time = funding_time_today - timedelta(hours=delay)
        if ans:
            return last_funding_time - timedelta(hours=delay)
        return last_funding_time



calculator = FundingFeeCalculator()
last_hour = calculator.get_last_funding_fee_hour(8, ans=True)
print("Last funding fee hour (ans=True):", last_hour)
last_hour_local = calculator.get_last_funding_fee_hour(8, ans=False)
print("Last funding fee hour (ans=False):", last_hour_local)
