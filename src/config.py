import os
from dotenv import load_dotenv
"""How can i install this"""
import paramiko

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# API-KEYS
COINMARKETCAP_APIKEY = os.getenv('COINMARKETCAP_APIKEY', 'coinmarketcap-apikey')

# SECURITY
def load_public_key(path):
    """
    Load a public key from an OpenSSH format file as plain text.
    """
    absolute_path = os.path.join(BASE_DIR, path)
    with open(absolute_path, 'r') as public_key_file:
        public_key_data = public_key_file.read().strip()  
    return public_key_data

def load_private_key(path):
    """
    Load a private key from an OpenSSH format file.
    """
    absolute_path = os.path.join(BASE_DIR, path)
    private_key = paramiko.RSAKey(filename=absolute_path)
    return private_key

# Specify the paths to the keys
PUBLIC_KEY = load_public_key('src/security/secure_key.pub')
PRIVATE_KEY = load_private_key('src/security/secure_key')

