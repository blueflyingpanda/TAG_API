import os

from dotenv import load_dotenv

if not load_dotenv():
    raise RuntimeError('.env not found')

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_SSL_MODE = os.getenv('DB_SSL_MODE')
