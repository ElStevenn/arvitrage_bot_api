import asyncio
import numpy as np
from datetime import datetime

from ..app.mongo.controller import MongoDB_Crypto
from ..app.crypto_data_service import CryptoDataService

"""Set up the essential data for cryptocurrency searches and populate the database with the required information"""

crypto_data_servise = CryptoDataService()
mongo_service = MongoDB_Crypto()


async def retrive_list_symbol():
    bitget_all_symbols = await crypto_data_servise.get_all_symbols('bitget')
    # biance_all_symbols = await crypto_data_servise.get_all_symbols('binance')

    bitget_filtered_symbols = [s.lstrip("10") if s.startswith("10") else s for s in bitget_all_symbols]
    # binance_filtered_symbols = [s.lstrip("10") if s.startswith("10") else s for s in biance_all_symbols]


    """Push data to mongodb"""
    for symbol in bitget_filtered_symbols:
        await mongo_service.add_new_symbol(symbol, 'bitget')

    # for symbol in binance_filtered_symbols:
    #     await mongo_service.push_crypto_metadata(symbol, 'binance')

    print("Pushing crypto metadata to mongodb\nThis proces may take over 10 minutes...")
    """Push metadata to mongodb"""
    for symbol in bitget_filtered_symbols:
        metadata = await crypto_data_servise.get_symbol_metadata(symbol)
        gerneral_exchange_metadata = await crypto_data_servise.get_general_exchange_metadata()

        data = {
            # General Information
            "symbol": metadata["symbol"],
            "name": metadata["name"],
            "description": metadata["description"],
            "logo": metadata["logo"],
            "urls": metadata["urls"],
            "date_added": datetime.now().isoformat(),
            "tags": metadata["tags"],

            # Suplly and market data
            "decimals": None,
            "max_supply": None,
            "funding_rate_interval": int(gerneral_exchange_metadata['funding_rate_interval']),
            "avariable_in": []
        }
        
        await mongo_service.add_crypto_metadata(symbol, data)


async def set_metadata_symbols():
    pass



async def main_cript():
    res = await retrive_list_symbol(); print("Result of retrive crypto -> ", res)


if __name__ == "__main__":
    asyncio.run(main_cript())