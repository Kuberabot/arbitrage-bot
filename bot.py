import ccxt
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Fake web server for Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"KUBERA BOT RUNNING 24/7!")

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

print("KUBERA BOT STARTED - 24/7 Running")

COINS = ['BTC/USDT','ETH/USDT','BNB/USDT','SOL/USDT','XRP/USDT','DOGE/USDT','ADA/USDT','SHIB/USDT']

binance = ccxt.binance()

while True:
    try:
        print("\n--- SCANNING COINS ---")
        for coin in COINS:
            try:
                ticker = binance.fetch_ticker(coin)
                price = ticker['last']
                print(f"{coin}: ${price}")
            except:
                pass
        time.sleep(10)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
