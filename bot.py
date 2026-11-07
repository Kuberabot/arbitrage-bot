import ccxt
import time

print("KUBERA BOT STARTED - 24/7 Running")

COINS = ['BTC/USDT','ETH/USDT','BNB/USDT','SOL/USDT','XRP/USDT','DOGE/USDT','ADA/USDT','SHIB/USDT','AVAX/USDT','TRX/USDT']

binance = ccxt.binance()

while True:
    try:
        print("\n--- SCANNING COINS ---")
        for coin in COINS:
            try:
                price = binance.fetch_ticker(coin)['last']
                print(f"{coin}: ${price}")
            except:
                pass
            time.sleep(0.5)
        print("Waiting 60 sec...")
        time.sleep(60)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
