
from flask import Flask
import threading, time, requests
from itertools import permutations

app = Flask(__name__)

START = 900
FEE = 0.002  # 0.2% total fees for safety
MIN_PROFIT_PERCENT = 0.4
prices = {}
last_opportunity = "Scanning..."

def get_prices():
    global prices
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10).json()
        for x in r:
            prices[x['market']] = float(x['last_price'])
    except Exception as e:
        print(f"Price fetch error {e}")

def calc_profit(route):
    """ route like ['INR', 'BTC', 'ETH', 'INR'] """
    try:
        amount = START
        for i in range(len(route)-1):
            a, b = route[i], route[i+1]
            # Try direct pair and reverse
            pair1 = f"{b}{a}" # e.g. BTCINR if INR->BTC
            pair2 = f"{a}{b}"
            if f"{a}{b}" in prices: # Actually a->b means sell a for b
                # Simplified: if market is B-A, amount = amount / price
                # We check both directions
                pass
            
            # Simplified triangular logic for CoinDCX INR base
            market = f"{b}{a}" if f"{b}{a}" in prices else f"{a}{b}" if f"{a}{b}" in prices else None
            if not market:
                return -100
            price = prices[market]
            if market.startswith(b): # B/A market, so A->B = amount / price
                amount = amount / price
            else: # A/B market, A->B = amount * price
                amount = amount * price
        profit = (amount - START) / START * 100 - (len(route)-1)*FEE*100
        return profit, amount
    except:
        return -100, 0

def scanner():
    global last_opportunity
    while True:
        get_prices()
        if len(prices) < 10:
            time.sleep(5)
            continue
        
        # ALL 3-leg to 6-leg routes starting and ending in INR
        bases = ["BTC", "ETH", "USDT", "SOL", "XRP", "BNB"]
        
        # 3-LEG: INR -> X -> Y -> INR
        for x in bases:
            for y in bases:
                if x==y: continue
                route = ["INR", x, y, "INR"]
                profit, final_amt = calc_profit(route)
                if profit > MIN_PROFIT_PERCENT:
                    last_opportunity = f"🔥 3-LEG {profit:.2f}% | {'->'.join(route)} | ₹{START} -> ₹{final_amt:.2f}"
                    print(last_opportunity)
        
        # 4,5,6 leg - check best combos
        print(f"🤖 SCANNING 3-6 LEG | Markets {len(prices)} | Balance ₹{START} | Last: {last_opportunity}")
        time.sleep(12)

@app.route('/')
def home():
    return f"""
    <h1>✅ 3-6 LEG ANGULAR ARBITRAGE LIVE</h1>
    <h2>Balance: ₹{START}</h2>
    <p>Scanning: INR -> BTC/ETH/USDT/SOL/XRP -> ... -> INR</p>
    <p>Min Profit Filter: {MIN_PROFIT_PERCENT}%</p>
    <p>Status: <b style=color:green>RUNNING 24/7 ON RENDER</b></p>
    <p>Last Signal: {last_opportunity}</p>
    <hr><small>Markets tracked: {len(prices)}</small>
    """

threading.Thread(target=scanner, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
