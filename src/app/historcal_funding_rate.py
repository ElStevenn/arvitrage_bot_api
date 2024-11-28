from datetime import datetime, time, timedelta
import aiohttp
import asyncio
import uuid
import pytz
import numpy as np
import logging
import time as lowtime
from typing import Tuple, Literal
from src.config import COINMARKETCAP_APIKEY

from src.app.crypto_data_service import CryptoDataService
from src.app.mongo.controller import MongoDB_Crypto

from src.app.mongo.schema import *
from src.app.chart_analysis import FundingRateChart



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainServiceLayer:
    def __init__(self) -> None:
        self.data_service = CryptoDataService()
        self.mongo_service = MongoDB_Crypto()
        self.timezone = "Europe/Amsterdam"

    # FUNCTION EVERY DAY
    async def crypto_rebase(self):
        # ... (Your existing code for crypto_rebase)
        pass

    # FUNCTION EVERY 8 or 4 HOURS - DEPENDING | every XX and 1 minute!
    async def schedule_set_analysis(self, period: Literal['4h', '8h']):
        """
        Save new funding rate in order to build the chart:
        - Create new analysis entries for cryptos that don't have funding rates.
        - Update existing entries by analyzing funding rates.
        - Function executed every 8 or 4 hours, depending on the period.
        """
        period_value = int(period[:-1])
        exec_time = int(self.get_last_period_funding_rate(period_value).timestamp() * 1000)

        # Fetch cryptos based on the period
        if period_value == 4:
            cryptos = await self.mongo_service.get_all_current_analysis(4)
        else:
            cryptos = await self.mongo_service.get_all_current_analysis(-1)

        logger.info(f"Cryptos to analyze for period {period}: {cryptos}")

        semaphore = asyncio.Semaphore(5)

        if not cryptos:
            # No cryptos available for analysis, initializing for the first time
            logger.warning("No cryptos available for analysis, adding new analysis for the first time ever")
            list_cryptos = await self.data_service.get_all_cryptos()

            for i in range(0, len(list_cryptos), 40):
                batch = list_cryptos[i:i+40]
                logger.info(f"Processing batch {i // 40 + 1} with {len(batch)} cryptos.")

                tasks = [self.set_first_analysis(crypto, semaphore, exec_time) for crypto in batch]
                await asyncio.gather(*tasks)

                # Wait 1 minute before processing the next batch
                await asyncio.sleep(60)

            logger.info("Finished initializing analysis for all cryptos.")

        else:
            # Process existing cryptos
            symbols_to_create = []
            symbols_to_analyze = []

            # Iterate over the list of cryptos
            for crypto_dict in cryptos:
                for symbol, data in crypto_dict.items():
                    if data is None:
                        symbols_to_create.append(symbol)
                    else:
                        symbols_to_analyze.append(symbol)

            logger.info(f"Symbols to create: {symbols_to_create}")
            logger.info(f"Symbols to analyze: {symbols_to_analyze}")

            # Process symbols that need new funding rate entries
            for i in range(0, len(symbols_to_create), 40):
                batch = symbols_to_create[i:i+40]
                logger.info(f"Processing creation batch {i // 40 + 1} with {len(batch)} cryptos.")

                tasks = [self.set_first_analysis(symbol, semaphore, exec_time) for symbol in batch]
                await asyncio.gather(*tasks)

                # Wait 1 minute before processing the next batch
                await asyncio.sleep(60)

            # Process symbols that need to be analyzed
            for i in range(0, len(symbols_to_analyze), 40):
                batch = symbols_to_analyze[i:i+40]
                logger.info(f"Processing analysis batch {i // 40 + 1} with {len(batch)} cryptos.")

                tasks = [self.decide_analysis_crypto(symbol, exec_time, semaphore) for symbol in batch]
                await asyncio.gather(*tasks)

                # Wait 1 minute before processing the next batch
                await asyncio.sleep(60)

            logger.info("Finished analyzing all cryptos.")

    async def decide_analysis_crypto(self, crypto: str, exec_time, semaphore):
        """
        Analyze the funding rate for a crypto and update its analysis if necessary.
        """
        async with semaphore:
            try:
                # Retrieve the last funding rate analysis
                current_contract_funding_rate, last_contract_funding_rate, current_period_ts, last_period_ts, current_period, last_period = await self.data_service.get_last_contract_funding_rate(crypto)
                
            except Exception as e:
                logger.error(f"Failed to get last funding rate for {crypto}: {e}")
                return None

        async with semaphore:
            try:
                # Get current index price
                index_period_price = await self.data_service.get_price_of_period(symbol=crypto, period=exec_time)
            except Exception as e:
                logger.error(f"Failed to get price for {crypto}: {e}")
                return None

        # Create a new funding rate analysis entry
        current_analysis = FundingRateAnalysis(
            period_ts=current_period_ts,
            period=current_period,
            funding_rate_value=float(current_contract_funding_rate),
            index_period_price=index_period_price,
            key_moment=float(current_contract_funding_rate) <= -0.5,
            analysis={}
        )
        logger.info(f"Current analysis for {crypto}: {current_analysis}")

        # Save current analysis no matter the funding value
        await self.mongo_service.save_current_funding_rate(symbol=crypto, analysis=current_analysis)

        # If the last funding rate was <= -0.5, generate analysis for last period
        if float(last_contract_funding_rate) <= -0.5:
            logger.info(f"Last funding rate <= -0.5 for {crypto}. Generating analysis for last period.")
            try:
                # Generate analysis
                analysis_chart = FundingRateChart(symbol=crypto)
                last_analysis_data = await analysis_chart.set_analysis(period=int(last_period_ts))

                # Prepare the updated analysis data
                analysis_data = Analysis(
                    description=last_analysis_data["description"],
                    eight_hour_variation=last_analysis_data["eight_hour_variation"],
                    ten_minute_variation=last_analysis_data["ten_minute_variation"],
                    one_minute_variation=last_analysis_data["one_minute_variation"]
                )

                # Update the previous funding rate analysis entry with the new analysis
                await self.data_service.save_last_funding_rate_analysis(symbol=crypto, analysis=analysis_data)

                logger.info(f"Added analysis to previous funding rate for {crypto}")

            except Exception as e:
                logger.error(f"Failed to generate analysis for {crypto}: {e}")
                return None

    async def set_first_analysis(self, symbol: str, semaphore, exec_time):
        """
        Create the first funding rate analysis entry for a crypto.
        """
        # Get current funding rate
        async with semaphore:
            try:
                current_contract_funding_rate, _, current_period_ts, _, current_period, _ = await self.data_service.get_last_contract_funding_rate(symbol)
            except Exception as e:
                logger.error(f"Failed while getting the crypto last analysis for {symbol}: {e}")
                return None

        # Get index price
        async with semaphore:
            try:
                # Get current index price
                index_period_price = await self.data_service.get_price_of_period(symbol=symbol, period=exec_time)
            except Exception as e:
                logger.error(f"Failed while getting the index price for {symbol}: {e}")
                return None
        
        current_analysis = FundingRateAnalysis(
            period_ts=current_period_ts,
            period=current_period,
            funding_rate_value=float(current_contract_funding_rate),
            index_period_price=index_period_price,
            key_moment=float(current_contract_funding_rate) <= -0.5,
            analysis={}
        )

        await self.data_service.save_current_funding_rate(symbol=symbol, analysis=current_analysis)
        logger.info(f"Initialized analysis for {symbol}")

    # Other methods remain unchanged...

    def get_next_funding_rate(self, delay: Literal[8, 4], ans=False):
        # ... (Your existing code for get_next_funding_rate)
        pass

    def get_last_period_funding_rate(self, delay: Literal[8, 4], ans=False):
        # ... (Your existing code for get_last_period_funding_rate)
        pass

    async def get_crypto_logo(self, symbol: str) -> Tuple[str, str, str]:
        # ... (Your existing code for get_crypto_logo)
        pass


async def main_testing():
    myown_service = MainServiceLayer()

    # Uncomment the following line to run crypto_rebase
    # await myown_service.crypto_rebase()
    # print(myown_service.get_next_funding_rate(4, True))

    # Execute the schedule_set_analysis method
    await myown_service.schedule_set_analysis('8h')

    # Alternatively, to test decide_analysis_crypto with a specific crypto:
    # semaphore = asyncio.Semaphore(5)
    # exec_time = int(myown_service.get_last_period_funding_rate(8).timestamp() * 1000)
    # await myown_service.decide_analysis_crypto('BIGTIMEUSDT', exec_time, semaphore)

    logger.info("***** Analysis Completed *****")


if __name__ == "__main__":
    asyncio.run(main_testing())
