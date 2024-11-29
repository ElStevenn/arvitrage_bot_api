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
    biance_all_symbols = await crypto_data_servise.get_all_symbols('binance')

    bitget_filtered_symbols = [s.lstrip("10") if s.startswith("10") else s for s in bitget_all_symbols]; print(len(bitget_filtered_symbols))
    binance_filtered_symbols = [s.lstrip("10") if s.startswith("10") else s for s in biance_all_symbols]; print(len(binance_filtered_symbols))

    
    """Push data to mongodb"""
    for symbol in bitget_filtered_symbols:
        await mongo_service.add_new_symbol(symbol, 'bitget')

    for symbol in binance_filtered_symbols:
        await mongo_service.add_new_symbol(symbol, 'binance')

    return bitget_filtered_symbols, binance_filtered_symbols

async def set_metadata_symbols(bitget_filtered_symbols, binance_filtered_symbols):
    """Push metadata to mongodb"""
    print("Pushing crypto metadata to mongodb\nThis proces may take over 10 minutes...")
    all_symbols = np.union1d(bitget_filtered_symbols, binance_filtered_symbols)

    
    for symbol in all_symbols:
        print(symbol)
        
        metadata = await crypto_data_servise.get_symbol_metadata(symbol)
        general_exchange_metadata = await crypto_data_servise.get_general_exchange_metadata()
        '''
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
            "funding_rate_interval": general_exchange_metadata["funding_rate_interval"],
            "avariable_in": general_exchange_metadata.get("available_on", []),
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
        '''

        
    # await mongo_service.add_crypto_metadata(symbol, data)
    



async def main_cript():
    bitget_filtered_symbols, binance_filtered_symbols = await retrive_list_symbol()


if __name__ == "__main__":
    asyncio.run(main_cript())