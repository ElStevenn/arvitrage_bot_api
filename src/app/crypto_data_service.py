import asyncio
import numpy as np
import pandas as pd
import aiohttp
import pytz
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Literal
import re

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
# from web3 import AsyncWeb3, Web3
# from web3 import AsyncHTTPProvider

from src.config import AVARIABLE_EXCHANGES, COINMARKETCAP_APIKEY, INFURA_APIKEY
from fastapi import HTTPException

class Granularity:
    MINUTE_1 = '60'
    MINUTE_5 = '300'
    HOUR_1 = '3600'
    HOUR_4 = '14400'
    DAY_1 = '86400'


class CryptoDataService:
    def __init__(self) -> None:
        # Exchanges URL
        self.bitget_url = "https://api.bitget.com"
        self.binance_url = "https://fapi.binance.com"
        
        # External APIs URL
        self.coinmarketcap_url = "https://pro-api.coinmarketcap.com"
        
        # Web3
        # self.infura_url = f"https://mainnet.infura.io/v3/{INFURA_APIKEY}"
        # self.web3 = Web3(Web3.HTTPProvider(self.infura_url))

        # if self.web3.is_connected():
            # print("Connected to Ethereum")
        # else:
            # raise Exception("Failed to connect to Ethereum")
        
    async def get_historical_funding_rate(self, symbol: str,):
        """
        Return: [[funding_rate, datetime_period, period]] 
        Limit: 500
        """
        final_result = np.empty((0, 3))  

        for page_number in range(1, 5 + 1): 
            url = f"https://api.bitget.com/api/v2/mix/market/history-fund-rate?pageSize=100&pageNo={page_number}"
            params = {"symbol": symbol, "productType": "USDT-FUTURES"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result.get("data", [])

                        if data:
                            page_data = [
                                (
                                    float(fr["fundingRate"]) * 100,  
                                    datetime.fromtimestamp(int(fr["fundingTime"]) / 1000, timezone.utc)  
                                    .astimezone(ZoneInfo('Europe/Amsterdam'))
                                    .isoformat(),
                                    float(fr["fundingTime"]),  
                                )
                                for fr in data
                            ]

                            np_page_data = np.array(page_data, dtype=object)  
                            final_result = np.vstack([final_result, np_page_data])
                    else:
                        print(f"Error fetching funding rate data: {response.status}")
                        return np.array([])  

        return final_result

    async def get_current_funding_rate(self, symbol):
        url = "https://api.bitget.com/api/v2/mix/market/current-fund-rate"
        params = {"symbol": symbol, "productType": "USDT-FUTURES"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    funding_rate = float(result['data'][0]['fundingRate']) * 100
                    return round(funding_rate, 4)
                else:
                    text_response = await response.text()
                    raise TypeError(f"An error ocurref with the the API response: {text_response}")

    async def get_last_contract_funding_rate(self, symbol, ans = False):
        url = "https://api.bitget.com/api/v2/mix/market/history-fund-rate"
        params = {"symbol": symbol, "productType": "USDT-FUTURES"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    funding_rate = float(result['data'][0 if not ans else 1]['fundingRate']) * 100
                    funding_time = result['data'][0 if not ans else 1]['fundingTime']
                    return round(funding_rate, 4), funding_time
                else:
                    text_response = await response.text()
                    raise TypeError(f"An error ocurref with the the API response: {text_response}")
                
    async def get_candlestick_chart_v2(self, symbol):pass

    async def get_funding_rate_period(self, symbol):
        """Get funding rate period, either 8h or 4h"""
        # STEP 1, get sample data
        url = "https://api.bitget.com/api/v2/mix/market/history-fund-rate?pageSize=3"
        params = {"symbol": symbol, "productType": "USDT-FUTURES"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get("data", [])

                    # Ensure there are at least two records to calculate the difference
                    if len(data) < 2:
                        raise ValueError("Not enough data to determine the funding rate period.")

                    # Convert the timestamps to datetime objects
                    page_data = [
                        datetime.fromtimestamp(int(fr["fundingTime"]) / 1000, timezone.utc) for fr in data
                    ]

                    # Calculate the time difference between the first two records
                    v1 = page_data[0]
                    v2 = page_data[1]
                    difference = v1 - v2

                    # Check if the difference is either 8 hours or 4 hours
                    if difference == timedelta(hours=8):
                        return 8
                    elif difference == timedelta(hours=4):
                        return 4
                    else:
                        raise ValueError(f"Unexpected time difference: {difference}")


    async def get_all_cryptos(self) -> np.ndarray: # DEPRECIATED
        url = "https://api.bitget.com/api/v2/mix/market/tickers"
        params = {
            "productType": "USDT-FUTURES"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    cryptos = result.get('data')
                    result = np.array([crypto["symbol"] for crypto in cryptos])

                    return result
                else:
                    response = await response.text()
                    raise ValueError(f"An error ocurred, status {response.status}, whole error: {response}")
                
    def calculate_api_calls(self, start_time: int, end_time: int, granularity_ms: int):
        time_diff = end_time - start_time
        total_candles = time_diff // granularity_ms
        max_candles_per_call = 1000

        print(f"Total candles: {total_candles}, time difference: {time_diff}, granularity in ms: {granularity_ms}")

        if total_candles == 0:
            return []

        calls = []
        current_start_time = start_time

        while total_candles > 0:
            candles_in_this_call = min(total_candles, max_candles_per_call)
            current_end_time = current_start_time + (candles_in_this_call * granularity_ms)

            calls.append({
                "start_time": current_start_time,
                "end_time": current_end_time,
                "candles": candles_in_this_call
            })

            current_start_time = current_end_time + granularity_ms
            total_candles -= candles_in_this_call

        print(f"Calculated API calls: {calls}")
        return calls


    def convert_granularity_to_ms(self, granularity: str) -> int:
        if granularity == "1m":
            return 60 * 1000
        elif granularity == "5m":
            return 5 * 60 * 1000
        elif granularity == "15m":
            return 15 * 60 * 1000
        elif granularity == "30m":
            return 30 * 60 * 1000
        elif granularity == "1H":
            return 3600 * 1000
        elif granularity == "4H":
            return 4 * 3600 * 1000
        elif granularity == "12H":
            return 12 * 3600 * 1000
        elif granularity == "1D":
            return 24 * 3600 * 1000
        elif granularity == "1W":
            return 7 * 24 * 3600 * 1000
        elif granularity == "1MO":
            return 30 * 24 * 3600 * 1000
        else:
            raise ValueError(f"Unsupported granularity: {granularity}")          

    async def get_candlestick_chart(self, symbol: str, granularity: str, start_time: int = None, end_time: int = None) -> np.ndarray:
            final_result = np.empty((0, 7))
            base_url = 'https://api.bitget.com/api/v2/mix/market/candles'
            params = {
                'symbol': symbol,
                'granularity': granularity,
                'productType': 'USDT-FUTURES',
                'limit': 1000
            }

            # Get how many times do I need to call the API
            granularity_ms = self.convert_granularity_to_ms(granularity)
            api_calls = self.calculate_api_calls(start_time, end_time, granularity_ms)
            # total_candles = (end_time - start_time) // granularity_ms
       
            
            async with aiohttp.ClientSession() as session:
                for i, call in enumerate(api_calls):
                    if start_time:
                        params['startTime'] = str(call['start_time'])
                    if end_time:
                        params['endTime'] = str(call['end_time'])

                    async with session.get(base_url, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            data = result.get("data", [])

                            if not data:
                                print(f"there wasn't data in attempt {i}")
                                break

                            np_data = np.array([
                                [
                                    int(item[0]),    # The timestamp in milliseconds
                                    float(item[1]),  # Open price
                                    float(item[2]),  # High price
                                    float(item[3]),  # Low price
                                    float(item[4]),  # Close price
                                    float(item[5]),  # Volume (traded amount in the base currency)
                                    float(item[6])   # Notional value (the total traded value in quote currency)
                                ]
                                for item in data
                            ], dtype=object)

                            final_result = np.vstack([final_result, np_data])

                            last_timestamp = int(data[-1][0])

                            # If the last fetched timestamp reaches or exceeds the requested end_time, stop fetching data
                            if end_time and last_timestamp >= end_time:
                                break

                            # Update startTime to last_timestamp + 1 to continue fetching the next 1000 candles
                            params['startTime'] = str(last_timestamp + 1)

                        else:
                            print(f"Error fetching candlestick data: {response.status}")
                            break

            return final_result
            
    async def get_price_of_period(self, symbol: str, period: int):
        """Get what was the price from a given symbol (in Opening time)"""
        
        end_time = period + (1 * 60 * 1000)
        period_ = await self.get_candlestick_chart(symbol, '1m', period, end_time)

        if period_.size > 0:
            return period_[0][4]
        else:
            timestamp = datetime.fromtimestamp(int(period) / 1000, pytz.timezone('Europe/Amsterdam'))
            raise ValueError(f"Period {timestamp} doesn't exist")

    async def get_all_symbols(self, exchange: str) -> np.ndarray:
        """Get all cryptos in futures from a given exchange"""
        if exchange not in AVARIABLE_EXCHANGES:
            raise ValueError(f"Exchange {exchange} not supported")
        
        if exchange == 'bitget':
            url = self.bitget_url + '/api/v2/mix/market/tickers'

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={'productType': 'USDT-FUTURES'}) as response:
                    if response.status == 200:
                        result = await response.json()
                        cryptos = result.get('data')
                        result = np.array([crypto["symbol"] for crypto in cryptos])

                        return result
                    else:
                        response = await response.text()
                        raise ValueError(f"An error ocurred, status {response.status}, whole error: {response}")
        elif exchange == 'binance':
            url = self.binance_url + "/fapi/v1/exchangeInfo"
            headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract all symbols
                        symbols = np.array([symbol["symbol"] for symbol in data["symbols"]])
                        return symbols
                    else:
                        error_message = await response.text()
                        raise ValueError(f"Error {response.status}: {error_message}")

    async def get_symbol_metadata(self, symbol: str):
        """Get metadata from a given symbol using CoinGecko API"""
        symbol = symbol.lower().replace('usdt', '').replace('usd', '').strip()

        if symbol.lower().startswith('btc'):
            print("Cannot process this")
            return None

        coin_data_url = self.coinmarketcap_url + f"/v1/cryptocurrency/info?symbol={symbol}"
        headers = {
            "X-CMC_PRO_API_KEY": COINMARKETCAP_APIKEY
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(coin_data_url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get('data', {}).get(symbol.upper(), {})# ; print(data)

                    return {
                        "symbol": data.get('symbol'),
                        "name": data.get('name'),
                        "description": data.get('description', {}),
                        "logo": data.get('logo', {}).replace('64', '128'),
                        "urls": data.get('urls', {}),
                        "tags": data.get('tags'),
                        "contract_address": data.get('contract_address'),
                    }
                    
                else:
                    if response.status == 400:
                        print(f"Couldn't find {symbol}")
                        return {"symbol": None, "name": None, "description": None, "logo": None, "urls": None, "tags": None, "contract_address": None}
                    text_response = await response.text()
                    
                    print("An error ocurred -> ,", text_response)


    async def get_funding_rate_interval(self, symbol: str) -> int:
        """Determine funding rate interval (4h or 8h) from Bitget."""

        # BITGET ATTEMPT
        
        url = f"{self.bitget_url}/api/v2/mix/market/history-fund-rate?symbol={symbol}&productType=usdt-futures"
        async with aiohttp.ClientSession() as session:
            async with  session.get(url) as response:
                data = await response.json()
                if data.get("code") == "00000" and "data" in data:
                    times = [int(entry["fundingTime"]) for entry in data["data"]]
                    if len(times) > 1:
                        interval_ms = abs(times[0] - times[1])
                        return f"{int(interval_ms / 3600000)}" 
        
        
        # BINANCE ATTEMPT
        binance_url = f"{self.binance_url}/fapi/v1/fundingInfo"
        symbol = re.sub(r"(USDT|USD)$", "", symbol, flags=re.IGNORECASE)
        symbol_pattern = re.compile(re.escape(symbol), re.IGNORECASE)
        async with aiohttp.ClientSession() as session:
            response = await session.get(binance_url)
            data = await response.json()
            for entry in data:
                if symbol_pattern.search(entry.get("symbol", "")):
                    return int(entry['fundingIntervalHours'])
        return None
    
    async def get_general_exchange_metadata(self, symbol):
        funding_rate = await self.get_funding_rate_interval(symbol=symbol)
        
        return {
            "funding_rate_interval": funding_rate
        }


    async def get_token_decimals(self, metadata):
        """Get the decimals of a token given its metadata"""
        decimals = metadata.get('decimals')
        if decimals is not None:
            print(f"Decimals from metadata: {decimals}")
            return decimals

        contract_address = metadata.get('contract_address')
        if not contract_address:
            raise ValueError("No contract address available to fetch decimals.")

        abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function",
            }
        ]

        contract = self.web3.eth.contract(address=self.web3.to_checksum_address(contract_address), abi=abi)

        # Call the decimals method
        try:
            decimals = contract.functions.decimals().call()
            print(f"Token Decimals from contract: {decimals}")
            return decimals
        except Exception as e:
            print(f"Error retrieving decimals from contract: {e}")
            raise



async def main_testing():
    start_time = int(datetime.now().timestamp() * 1000) - (5 * 60 * 1000)  
    end_time = int(datetime.now().timestamp() * 1000)  

    crypto_data = CryptoDataService()

    res = await crypto_data.get_symbol_metadata('XRPUSDT'); print(res)


if __name__ == "__main__":
    asyncio.run(main_testing())