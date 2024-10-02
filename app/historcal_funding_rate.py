from datetime import datetime
import aiohttp
import asyncio
import numpy as np

from app.redis_layer import RedisService
from app.bitget_layer import BitgetService
from typing import Tuple
from config import COINMARKETCAP_APIKEY


class MainServiceLayer():
    
    def __init__(self) -> None:
        self.redis_service = RedisService()
        self.bitget_service = BitgetService()

    async def crypto_rebase(self):
        """Everyday Update the list of cryptos as well as gets its logos"""
        list_current_cryptos = self.redis_service.get_list_cryptos(); print("current cryptos -> ",list_current_cryptos)
        bitget_cryptos = await self.bitget_service.get_all_cryptos()

        # Find cryptos that doesn't match
        cryptos_to_delete = list_current_cryptos[~np.isin(list_current_cryptos, bitget_cryptos)]
        cryptos_to_add = bitget_cryptos[~np.isin(bitget_cryptos, list_current_cryptos)]

        
        # Add or remove cryptos
        if cryptos_to_delete.any():
            for crypto_to_remove in cryptos_to_delete:
                self.redis_service.delete_crypto(crypto_to_remove)

        
        if cryptos_to_add.any():
            for crypto in cryptos_to_add:

                if str(crypto).lower().startswith('1000'):
                    crypto = crypto[4:]
                    
                print("Adding crypto..", crypto)
                crypto_logo, name, description = await self.get_crypto_logo(crypto)

                crypto_logo = crypto_logo.replace("64x64", "128x128")

                self.redis_service.add_symbol_only(crypto, name, crypto_logo, description)
                


    async def get_crypto_logo(self, symbol: str) -> Tuple[str, str, str]:

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

                    # Extract the logo URL
                    try:
                        logo_url = api_response['data'][symbol]['logo']
                        name = api_response['data'][symbol]['name']
                        description = api_response['data'][symbol]['description']
                        id = api_response['data'][symbol]['id']
                        return logo_url, name, description
                    except KeyError:
                        print(f"An error ocurred while fetching the result: {api_response}")

                else:
                    text_response = await response.text()
                    print(f"An error has occurred: {text_response}")
                    raise Exception(f"An error occurred with the API: {text_response}")




async def main_testing():
    myown_service = MainServiceLayer()

    res = await myown_service.crypto_rebase()
    print("*****")
    print(res)

if __name__ == "__main__":
    asyncio.run(main_testing())