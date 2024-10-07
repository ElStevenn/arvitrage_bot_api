from datetime import datetime, time, timedelta
import aiohttp
import asyncio
import uuid
import pytz
import numpy as np
import logging

from app.redis_layer import RedisService
from app.bitget_layer import BitgetService
from app.chart_analysis import FundingRateChart
from typing import Tuple, Literal
from config import COINMARKETCAP_APIKEY


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainServiceLayer:
    def __init__(self) -> None:
        self.redis_service = RedisService()
        self.bitget_service = BitgetService()
        self.timezone = "Europe/Amsterdam"

    # FUNCTION EVERY DAY
    async def crypto_rebase(self):
        """Everyday Update the list of cryptos as well as gets its logos"""
        list_current_cryptos = self.redis_service.get_list_cryptos(); print("current cryptos redis -> ", list_current_cryptos)
        logger.info(f"Current cryptos -> {list_current_cryptos}")
        bitget_cryptos = await self.bitget_service.get_all_cryptos()

        # Find cryptos that don't match
        if list_current_cryptos.any():
            cryptos_to_delete = list_current_cryptos[~np.isin(list_current_cryptos, bitget_cryptos)]
            cryptos_to_add = bitget_cryptos[~np.isin(bitget_cryptos, list_current_cryptos)]
        else:
            cryptos_to_delete = np.array([])
            cryptos_to_add = bitget_cryptos

        # Remove outdated cryptos
        if cryptos_to_delete.any():
            for crypto_to_remove in cryptos_to_delete:
                self.redis_service.delete_crypto(crypto_to_remove)
                logger.info(f"Removed crypto: {crypto_to_remove}")

        # Add new cryptos
        if cryptos_to_add.any():
            for crypto in cryptos_to_add:
                if str(crypto).lower().startswith('1000'):
                    crypto = crypto[4:]

                logger.info(f"Adding crypto: {crypto}")
                try:
                    crypto_logo, name, description = await self.get_crypto_logo(crypto)
                except Exception as e:
                    logger.error(f"Failed to get logo for {crypto}: {e}")
                    continue

                # Modify logo and set it to 128 pixels
                crypto_logo = crypto_logo.replace("64x64", "128x128")
                
                try:
                    funding_rate = await self.bitget_service.get_funding_rate_period(symbol=crypto)
                except Exception as e:
                    logger.error(f"Failed to get funding rate for {crypto}: {e}")
                    funding_rate = "N/A" 

                # Add the new crypto to Redis
                self.redis_service.add_crypto_metadata(crypto, name, crypto_logo, description, funding_rate)
                logger.info(f"Added crypto to Redis: {crypto}")

    # FUNCTION EVERY 8 or 4 HOURS - DEPENDING | every XX and 1 minute!
    async def schedule_set_analysis(self, period: Literal['4h', '8h']):
        """
        Save new funding rate in order to build the chart:
         - Set an anlysis if funding rate was less than -0.5, otherwise it'll save the new funding rate.
         - Function executed every 8 or 4 hours, depending of period 
        
        """
        # Fetch cryptos based on the period
        if period == '4h':
            cryptos = self.redis_service.get_cryptos_by_fr_expiration_optimized('4h')
        else:
            cryptos = self.redis_service.get_list_cryptos()

        logger.info(f"Cryptos to analyze for period {period}: {cryptos}")

        if cryptos.size == 0:
            logger.warning("No cryptos available for analysis.")
            return

        for crypto in cryptos:
            await self.decide_analysis_crypto(crypto)

    logger.info("Completed setting analysis for all applicable cryptos.")

    async def decide_analysis_crypto(self, crypto: str):
            try:
                # Retrieve the last funding rate analysis
                fund_rate_ans, fund_period_ans, fund_id_ans = self.redis_service.get_last_funding_rate(symbol=crypto)
            except Exception as e:
                logger.error(f"Failed to get last funding rate for {crypto}: {e}")
                return None

            try:
                # Get the latest funding rate from Bitget
                fund_rate, fund_period = await self.bitget_service.get_last_contract_funding_rate(crypto, False)
            except Exception as e:
                logger.error(f"Failed to get current funding rate for {crypto}: {e}")
                return None

            # Create a new funding rate analysis entry
            current_analysis = {
                "period": fund_period,
                "funding_rate_value": float(fund_rate),
                "analysis": {}
            }; print("current analysis -> ", current_analysis)
            
            # Add the new funding rate entry to Redis
            try:
                if fund_rate > -0.5:
                    self.redis_service.add_funding_rate_analysis(symbol=crypto, funding_rate_analysis=current_analysis)
                    logger.info(f"Added new funding rate entry for {crypto}: {current_analysis}")
                    return None
            except Exception as e:
                logger.error(f"Failed to add new funding rate for {crypto}: {e}")
                return None
            """
            # Conditional Analysis: If previous funding rate <= -0.5, add analysis to pre-last entry
            if fund_rate_ans is not None and float(fund_rate_ans) <= -0.5 and fund_period_ans:
                logger.info(f"Funding rate <= -0.5 for {crypto}. Adding analysis to previous entry.")
                try:
                    analysis_chart = FundingRateChart(symbol=crypto)
                    last_analysis = analysis_chart.set_analysis(period=int(fund_period_ans))
                except Exception as e:
                    logger.error(f"Failed to generate analysis for {crypto}: {e}")
                    return None

                # Prepare the updated analysis data
                new_last_analysis = {
                    "id": fund_id_ans,
                    "period": fund_period_ans,
                    "funding_rate_value": fund_rate_ans,
                    "analysis": last_analysis
                }

                # Add analysis to the pre-last funding rate entry
                try:
                    self.redis_service.add_analysis_funding_rate(symbol=crypto, analysis_data=new_last_analysis)
                    logger.info(f"Added analysis to pre-last funding rate for {crypto}: {new_last_analysis}")
                except Exception as e:
                    logger.error(f"Failed to add analysis to pre-last funding rate for {crypto}: {e}")
                    return None
                """

    async def get_crypto_logo(self, symbol: str) -> Tuple[str, str, str]:
        """Fetches the crypto logo, name, and description from CoinMarketCap API."""
        if symbol.lower().endswith('usdt'):
            symbol = symbol[:-4]

        api_url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?symbol={symbol}"
        headers = {
            "X-CMC_PRO_API_KEY": COINMARKETCAP_APIKEY,
            "Accept": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url=api_url, headers=headers) as response:
                if response.status == 200:
                    api_response = await response.json()

                    try:
                        data = api_response['data'][symbol]; print("API response -> ", data)
                        logo_url = data['logo']
                        name = data['name']
                        description = data['description']
                        return logo_url, name, description
                    except KeyError:
                        error_msg = f"Missing expected data for symbol: {symbol} in API response."
                        logger.error(error_msg)
                        raise KeyError(error_msg)
                else:
                    text_response = await response.text()
                    error_msg = f"API request failed for symbol: {symbol}. Status: {response.status}, Response: {text_response}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

    def get_next_funding_rate(self, delay: Literal[8,4], ans = False):
        # Define next execution times
        execution_times = [time(hour, 0) for hour in range(2, 23, delay)]

        timezone = pytz.timezone(self.timezone)
        now_datetime = datetime.now(timezone)
        now_time = now_datetime.time()

        sorted_times = sorted(t for t in execution_times if t > now_time)
        if sorted_times:
            next_time_of_day = sorted_times[1] if ans and len(sorted_times) > 1 else sorted_times[0]
        else:
            next_time_of_day = execution_times[0]

        # Combine current date with next_time_of_day
        naive_datetime = datetime.combine(now_datetime.date(), next_time_of_day)

        # Localize the naive datetime to the specified timezone
        next_execution_datetime = timezone.localize(naive_datetime)

        # If the scheduled time is in the past, schedule for the next day
        if next_execution_datetime <= now_datetime:
            next_execution_datetime += timedelta(days=1)

        return next_execution_datetime


async def main_testing():
    myown_service = MainServiceLayer()

    # Uncomment the following line to run crypto_rebase
    # await myown_service.crypto_rebase()
    # print(myown_service.get_next_funding_rate(4, True))


    # Run set_analysis for '8h' period
    # await myown_service.schedule_set_analysis('8h')
    # await myown_service.decide_analysis_crypto('BTCUSDT')
    await myown_service.get_crypto_logo("BTCUSDT")
    logger.info("***** Analysis Completed *****")


if __name__ == "__main__":
    asyncio.run(main_testing())