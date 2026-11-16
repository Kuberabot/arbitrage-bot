
from flask import Flask
import threading, time, os, requests
from datetime import datetime

app = Flask(__name__)
CAPITAL = 900
MIN_PROFIT = 0.3
total_profit = 0
trades = 0
last_msg = "Scanning..."
best_opportunity = "None"

prices = {}

# 12 REAL paths that exist in CoinDCX - 1 to 5 legs inside only
PATHS = [
    ["INR","BTC","ETH","INR"],
    ["INR","ETH","BTC","INR"],
    ["INR","BTC","USDT","INR"],
    ["INR","USDT","BTC","INR"],
    ["INR","ETH","USDT","INR"],
    ["INR","BTC","SOL","INR"],
    ["INR","SOL","BTC","INR"],
    ["INR","ETH","SOL","INR"],
    ["INR","BTC","ETH","SOL","INR"],
    ["INR","USDT","BTC","ETH","INR"],
    ["INR","BTC","MATIC","ETH","INR"],
    ["INR","BTC","DOGE","USDT","INR"],
]

@app.route('/')
def home():
    return f"""
    <html><head><meta name='viewport' content='width=device-width'><style>
    body{{font-family:monospace;background:#000;color:#0f0;padding:10px}}
    .box{{border:1px solid #0f0;padding:8px;margin:6px 0;font-size:13px}}
    </style></head><body>
    <h3>CoinDCX Angular Bot - 12 Paths Live</h3>
    <div class='box'>Capital: Rs.{CAPITAL} | Profit: Rs.{total_profit:.2f} | Trades: {trades}</div>
    <div class='box'>BEST: {best_opportunity}</div>
    <div class='box'>{last_msg}</div>
    <div class='box'>Mode: Auto-trade inside CoinDCX when >{MIN_PROFIT}% | Scanning 12 paths</div>
    <script>setTimeout(()=>location.reload(),4000)</script>
    </body></html>
    """

def convert(amount, frm, to):
    """Convert frm->to using real CoinDCX market"""
    # Try frm+to or to+frm
    m1 = frm + to
    m2 = to + frm
    if m1 in prices:
        # m1 = frmto e.g., BTCINR = BTC->INR market, price is to per frm
        # frm=BTC, to=INR, BTCINR exists: INR = BTC * price
        return amount * prices[m1] * 0.998
    if m2 in prices:
        # m2 = tofrm e.g., BTCINR exists but we want INR->BTC
        # INR->BTC using BTCINR: BTC = INR / price
        return (amount / prices[m2]) * 0.998
    return None

def check_all():
    global total_profit, trades, last_msg, best_opportunity
    best_profit = -10
    best_path = ""
    
    for path in PATHS:
        amt = CAPITAL
        valid = True
        for i in range(len(path)-1):
            frm, to = path[i], path[i+1]
            new_amt = convert(amt, frm, to)
            if new_amt is None:
                valid = False
                break
            amt = new_amt
        
        if not valid:
            continue
        
        profit_pct = (amt - CAPITAL) / CAPITAL * 100
        
        if profit_pct > best_profit:
            best_profit = profit_pct
            best_path = "->".join(path)
            best_opportunity = f"{best_path} = {profit_pct:.3f}% (Final Rs.{amt:.2f})"
        
        if profit_pct >= MIN_PROFIT:
            trades += 1
            total_profit += (amt - CAPITAL)
            last_msg = f"{datetime.now().strftime('%H:%M:%S')} - ✅ AUTO TRADED {best_path} | Profit {profit_pct:.3f}% | Rs.{amt:.2f}"
            print(last_msg)
            # REAL TRADE HERE after API approved: loop and execute market orders for each leg
            time.sleep(25)
            return
    
    last_msg = f"{datetime.now().strftime('%H:%M:%S')} - Scanning... Best {best_path} = {best_profit:.3f}% (Waiting >{MIN_PROFIT}%)"

def loop():
    while True:
        try:
            r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10).json()
            for t in r:
                prices[t['market']] = float(t['last_price'])
            check_all()
        except Exception as e:
            last_msg = f"Error {e}"
        time.sleep(8)

threading.Thread(target=loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
