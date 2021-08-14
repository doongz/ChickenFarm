import os


USER = os.getenv('DB_USERNAME', None)
PWD = os.getenv('DB_PASSWORD', None)
ADDRESS = os.getenv('DB_ADDRESS', None)
PORT = os.getenv('DB_PORT', None)
DB_FUND = os.getenv('DB_FUND', None)
DB_NETVALUE = os.getenv('DB_NETVALUE', None)