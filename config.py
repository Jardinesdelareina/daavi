import environs
from binance.client import Client

env = environs.Env()
env.read_env('.env')

TELETOKEN = env('TELETOKEN')
CHAT_ID = env('CHAT_ID')
CLIENT = Client(env('API_KEY'), env('SECRET_KEY'), {'verify': True, 'timeout': 20})
