import os
from dotenv import load_dotenv

load_dotenv()

# API-KEYS
COINMARKETCAP_APIKEY = os.getenv('COINMARKETCAP_APIKEY', 'coinmarketcap-apikey')

