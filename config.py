
import psycopg2

BOT_TOKEN = "8127613906:AAGdr_DIVMFwHzj_PU9c8ZhvjmL1bOrzZyY"
JWT_SECRET = "secret"
JWT_EXPIRES_IN = 36000000

POSTGRES_CONFIG = {
    "host": "localhost",
    "database": "ServiceProject",
    "user": "postgres",
    "password": "1",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**POSTGRES_CONFIG)
