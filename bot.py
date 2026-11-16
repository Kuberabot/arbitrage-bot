from flask import Flask
import threading, time, os, requests
from datetime import datetime

app = Flask(__name__)

CAPITAL = 900
MIN_PROFIT = 0.3  # Profit after fees
total_profit = 0
trades = 0
last_msg = "Starting..."

# REAL PATHS - These actually exist in CoinDCX
PATHS = [
    ["INR", "BTC", "ETH"],  # INR->BTC, BTC->ETH, ETH->INR
]

prices = {}  # BTCINR, ETHINR, ETHBTC etc

@app.route('/')
def home():
    return f"""
    <html><head><meta name='viewport' content='width=device-width'><style>
    body{{font-family:monospace;background:#000;color:#0f0;padding:15px}}
    .box{{border:1px solid #0f0;padding:10px;margin:10px 0}}
    </style></head><body>
    <h3>CoinDCX Triangular Bot - REAL PRICES</h3>
    <div class='box'>Capital: Rs.{CAPITAL} | Profit: Rs.{total_profit:.2f} | Trades: {trades}</div>
    <div class='box'>{last_msg}</div>
    <div class='box'>Prices: BTC={prices.get('BTCINR',0):,.0f} | ETH={prices.get('ETHINR',0):,.0f} | ETH/BTC={prices.get('ETHBTC',0):.5f}</div>
    <div class='box'>Path: INR -> BTC -> ETH -> INR (Inside CoinDCX Only)</div>
    <script>setTimeout(()=>location.reload(),5000)</script>
    </body></html>
    """

def get_all_prices():
    global prices
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=15).json()
        for t in r:
            prices[t['market']] = float(t['last_price'])
        return True
    except Exception as e:
        print(e)
        return False

def check_triangular():
    """REAL Triangular calculation: INR -> BTC -> ETH -> INR"""
    global total_profit, trades, last_msg
    try:
        btc_inr = prices.get('BTCINR')
        eth_inr = prices.get('ETHINR')
        eth_btc = prices.get('ETHBTC')

        if not btc_inr or not eth_inr or not eth_btc:
            last_msg = f"{datetime.now().strftime('%H:%M:%S')} - Waiting for CoinDCX prices..."
            return

        # Step 1: INR -> BTC
        # 900 INR / 9000000 = 0.0001 BTC
        btc_amount = CAPITAL / btc_inr
        btc_amount *= 0.998  # 0.2% fee

        # Step 2: BTC -> ETH
        # ETHBTC = 0.05 means 1 ETH = 0.05 BTC, so ETH = BTC / 0.05
        eth_amount = btc_amount / eth_btc
        eth_amount *= 0.998

        # Step 3: ETH -> INR
        final_inr = eth_amount * eth_inr
        final_inr *= 0.998

        profit_pct = (final_inr - CAPITAL) / CAPITAL * 100

        last_msg = f"{datetime.now().strftime('%H:%M:%S')} - INR {CAPITAL} -> BTC {btc_amount:.6f} -> ETH {eth_amount:.6f} -> INR {final_inr:.2f} | Profit: {profit_pct:.3f}%"

        print(last_msg)

        if profit_pct >= MIN_PROFIT:
            trades += 1
            profit_rs = final_inr - CAPITAL
            total_profit += profit_rs
            last_msg = f"✅ PROFIT FOUND! {profit_pct:.3f}% - AUTO TRADE! Final INR {final_inr:.2f} (+Rs.{profit_rs:.2f})"
            print(last_msg)
            # HERE REAL TRADE CODE WILL COME AFTER YOUR API APPROVED
            # For now it just counts profit (PAPER)
            time.sleep(20)

    except Exception as e:
        last_msg = f"Calc Error: {e}"

def loop():
    while True:
        if get_all_prices():
            check_triangular()
        time.sleep(10)

threading.Thread(target=loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
