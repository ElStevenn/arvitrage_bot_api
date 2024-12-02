import asyncio
import numpy as np
from datetime import datetime
import time
import aiohttp

from ..app.mongo.controller import MongoDB_Crypto
from ..app.crypto_data_service import CryptoDataService

"""Set up the essential data for cryptocurrency searches and populate the database with the required information"""

crypto_data_service = CryptoDataService()
mongo_service = MongoDB_Crypto()

class TokenBucketRateLimiter:
    def __init__(self, rate, capacity):
        self._rate = rate  # tokens per second
        self._capacity = capacity  # maximum burst size
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._last_refill = now
            # Refill the bucket
            self._tokens = min(self._tokens + elapsed * self._rate, self._capacity)
            if self._tokens >= 1:
                self._tokens -= 1
                return
            else:
                # Calculate sleep time
                sleep_time = (1 - self._tokens) / self._rate
        await asyncio.sleep(sleep_time)
        await self.acquire()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

async def retrieve_list_symbol():
    bitget_all_symbols = await crypto_data_service.get_all_symbols('bitget')
    binance_all_symbols = await crypto_data_service.get_all_symbols('binance')

    bitget_filtered_symbols = [s.lstrip("10") if s.startswith("10") else s for s in bitget_all_symbols]
    binance_filtered_symbols = [s.lstrip("10") if s.startswith("10") else s for s in binance_all_symbols]

    return bitget_filtered_symbols, binance_filtered_symbols

async def fetch_symbol_data(symbol, rate_limiter_metadata, rate_limiter_exchange_metadata, symbol_exchanges):
    print(f"Fetching data for {symbol}")

    # Rate-limited API calls
    metadata_task = asyncio.create_task(
        rate_limited_call(
            func=crypto_data_service.get_symbol_metadata,
            rate_limiter=rate_limiter_metadata,
            symbol=symbol
        )
    )
    general_exchange_metadata_task = asyncio.create_task(
        rate_limited_call(
            func=crypto_data_service.get_general_exchange_metadata,
            rate_limiter=rate_limiter_exchange_metadata,
            symbol=symbol
        )
    )

    # Run both tasks concurrently
    metadata, general_exchange_metadata = await asyncio.gather(
        metadata_task, general_exchange_metadata_task
    )

    if metadata is None:
        print(f"No metadata found for {symbol}, skipping.")
        return

    data = {
        # METADATA
        "symbol": metadata["symbol"],
        "name": metadata["name"],
        "description": metadata["description"],
        "logo": metadata["logo"],
        "urls": metadata["urls"],

        # Internal irrelevant data
        "date_added": datetime.now().isoformat(),
        "tags": metadata["tags"],
        "decimals": metadata.get("decimals", None),

        # Token Info and Market Data
        "max_supply": None,
        "funding_rate_interval": general_exchange_metadata.get("funding_rate_interval"),
        "available_in": symbol_exchanges.get(symbol, None),
        "blockchain": None,
        "token_type": None,
        "genesis_date": None,
        "consensus_mechanism": None,

        # Advanced Token Data
        "price_spread": None,
        "historical_ohlc_url": None,
        "funding_rate_history_url": None,
        "average_gas_cost": None,

        # Miscellaneous
        "average_volatility": None,
        "network_activity": None,  # Active wallets or tx volume
        "use_cases": [],  # Example: ["store-of-value", "payments"]
    }

    print(f"Added data for {symbol}")
    await mongo_service.add_crypto_metadata(symbol, data)

async def rate_limited_call(func, rate_limiter, *args, **kwargs):
    async with rate_limiter:
        return await func(*args, **kwargs)

async def set_metadata_symbols(bitget_filtered_symbols, binance_filtered_symbols):
    """Push metadata to mongodb"""
    print("Pushing crypto metadata to mongodb\nThis process may take over 10 minutes...")
    all_symbols = np.union1d(bitget_filtered_symbols, binance_filtered_symbols)
    exchange_symbols = {
        'bitget': bitget_filtered_symbols,
        'binance': binance_filtered_symbols
    }
    symbol_exchanges = {
        crypto: [platform for platform, symbols in exchange_symbols.items() if crypto in symbols]
        for crypto in set(bitget_filtered_symbols + binance_filtered_symbols)
    }

    # Create separate rate limiters
    rate_limiter_metadata = TokenBucketRateLimiter(rate=30/60, capacity=1)  # 30 calls per minute
    rate_limiter_exchange_metadata = TokenBucketRateLimiter(rate=50/60, capacity=1)  # Adjust as needed

    tasks = [
        fetch_symbol_data(symbol, rate_limiter_metadata, rate_limiter_exchange_metadata, symbol_exchanges)
        for symbol in all_symbols
    ]
    await asyncio.gather(*tasks)

async def main_crypt():
    bitget_filtered_symbols, binance_filtered_symbols = await retrieve_list_symbol()
    await set_metadata_symbols(bitget_filtered_symbols, binance_filtered_symbols)

if __name__ == "__main__":
    asyncio.run(main_crypt())
