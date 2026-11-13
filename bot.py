import os, requests, time, threading
from flask import Flask
from collections import defaultdict

app = Flask(__name__)
@app.route('/')
def home():
    return f"<h1>Kuberabot LIVE | ₹3000 Capital | Scanning 4-6 Angular</h1><p>Target: ₹3000/day in 60 days | Capital: ₹{START_INR}</p>"

START_INR = 3000
MIN_PROFIT_PCT = 2.2
MAX_LEGS = 6
LIVE_TRADING = False

def get_markets():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10)
        data = r.json()
        markets = {}
        for d in data:
            m=d['market']; p=float(d['last_price'])
            if p>0: markets[m]=p
        return markets
    except: return {}

def find_arbitrage():
    markets = get_markets()
    if not markets: return
    paths = [
        ["BTC","ETH","SOL","INR"],
        ["BTC","ETH","USDT","INR"],
        ["BTC","SOL","DOGE","INR"],
        ["ETH","SOL","MATIC","INR"],
        ["BTC","ETH","SOL","BNB","INR"],
        ["BTC","AVAX","MATIC","USDT","INR"],
        ["DOGE","SHIB","PEPE","USDT","INR"],
        ["BTC","ETH","SOL","AVAX","MATIC","INR"],
    ]
    for path in paths:
        try:
            amount = START_INR
            prev = "INR"
            # INR->first
            if f"{path[0]}INR" in markets:
                amount = amount / markets[f"{path[0]}INR"]
                prev = path[0]
            else: continue
            # middle hops
            for i in range(1,len(path)):
                fr=path[i-1]; to=path[i]
                if to=="INR":
                    if f"{fr}INR" in markets: amount = amount * markets[f"{fr}INR"]
                    else: amount=0; break
                else:
                    m1=f"{to}{fr}"; m2=f"{fr}{to}"
                    if m1 in markets: amount = amount * markets[m1]
                    elif m2 in markets: amount = amount / markets[m2]
                    else:
                        if f"{fr}INR" in markets and f"{to}INR" in markets:
                            inr_val = amount * markets[f"{fr}INR"]
                            amount = inr_val / markets[f"{to}INR"]
                        else: amount=0; break
            if amount>0:
                fee = (len(path))*0.002*amount
                tds = amount*0.01
                net = amount - fee - tds
                profit = net - START_INR
                pct = (profit/START_INR)*100
                if pct >= MIN_PROFIT_PCT:
                    print(f"✅ PROFIT {len(path)}-ANG: {'->'.join(['INR']+path)} | ₹{START_INR} -> ₹{net:.2f} | +{pct:.2f}% = +₹{profit:.2f}", flush=True)
                else:
                    print(f"Scan {len(path)}-ang INR->{ '->'.join(path)} : {pct:.2f}%", flush=True)
        except Exception as e: pass

def loop():
    print(f"===== KUBERABOT STARTED ₹{START_INR} =====", flush=True)
    while True:
        find_arbitrage()
        time.sleep(12)

threading.Thread(target=loop, daemon=True).start()
if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
