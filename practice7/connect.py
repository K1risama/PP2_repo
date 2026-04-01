

import psycopg2
from config import DB_CONFIG


def get_connection():

    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    return conn
