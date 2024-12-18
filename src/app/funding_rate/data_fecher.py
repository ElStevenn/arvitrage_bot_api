from typing import Literal, Optional
import asyncio

from src.app.clients.binance import BinanceClient
from src.app.clients.bitget import BitgetClient
from src.app.proxy import APIProxy

class DataFecher:
    def __init__(self):
        self.binance_client = BinanceClient()
        self.bitget_client = BitgetClient()
        

    async def fetch_funding_rate(self, symbol: str):
        """Get funding rates from supported exchanges for a given symbol."""
        funding_rate_data = []

        # Define supported exchanges and corresponding clients
        supported_exchanges = {
            "binance": self.binance_client.get_last_contract_funding_rate,
            "bitget": self.bitget_client.get_last_contract_funding_rate
        }

        # Determine which exchanges support the symbol based on its suffix
        exchange_tasks = []
        if symbol.endswith("USDT"):
            # Add both Binance and Bitget if symbol is in USDT
            exchange_tasks.append(("binance", supported_exchanges["binance"](symbol)))
            exchange_tasks.append(("bitget", supported_exchanges["bitget"](symbol)))
        elif symbol.endswith("UMCBL"):
            exchange_tasks.append(("bitget", supported_exchanges["bitget"](symbol)))
        else:
            return {"funding_rate": []}

        # Fetch funding rates concurrently for supported exchanges
        results = await asyncio.gather(
            *[self._fetch_funding_rate_for_exchange(exchange, task) for exchange, task in exchange_tasks],
            return_exceptions=True  # Capture exceptions for debugging
        )

        # Debugging: Print raw results
        print(f"Raw results: {results}")

        # Filter out None results and structure the data
        funding_rate_data = [
            {"exchange": exchange, "funding_rate": rate}
            for exchange, rate in results if rate is not None
        ]

        return {"funding_rate": funding_rate_data}

    async def _fetch_funding_rate_for_exchange(self, exchange: str, fetch_task):
        """Helper method to fetch funding rate for a specific exchange."""
        try:
            return exchange, await fetch_task
        except Exception as e:
            print(f"Error fetching funding rate for {exchange}: {e}")
            return exchange, None


    async def _fetch_funding_rate_for_exchange(self, exchange: str, fetch_task):
        """Helper method to fetch funding rate for a specific exchange."""
        try:
            return exchange, await fetch_task
        except Exception as e:
            print(f"Error fetching funding rate for {exchange}: {e}")
            return exchange, None



    async def get_fr_log():
        """Get whole funding rate log"""
        pass


async def main_testing():
    data_fecher = DataFecher()

    res = await data_fecher.fetch_funding_rate("bigtimeUSDT"); print("fetched data ->", res)

if __name__ == "__main__":
    asyncio.run(main_testing())