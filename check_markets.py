import ccxt
import config

try:
    exchange = ccxt.bitget({
        'apiKey': config.API_KEY,
        'secret': config.SECRET_KEY,
        'password': config.PASSPHRASE,
        'options': {
            'defaultType': 'future'
        }
    })
    exchange.set_sandbox_mode(True)
    markets = exchange.load_markets()
    print("Available symbols containing 'BTC':")
    for symbol in markets:
        if 'BTC' in symbol:
            print(symbol)
except Exception as e:
    print(f"An error occurred: {e}")
