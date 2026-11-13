import time, requests, itertools, os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Kuberabot 3-9 ANG LIVE"

SYMBOLS = ["BTC", "ETH", "SOL", "BNB", "USDT", "XRP", "ADA", "DOGE"]
BASE = "INR"
CAPITAL = 3000
FEE = 0.002 # 0.2% per trade
MIN_PROFIT = 0.008 # 0.8% after fees

def get_prices():
    prices = {}
    try:
        # Get INR markets
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=5).json()
        for item in r:
            market = item.get('market','')
            last = float(item.get('last_price',0) or 0)
            if last>0:
                prices[market]=last
    except:
        pass
    return prices

def calc_profit(prices, path):
    # path = ['INR','BTC','ETH','INR'] 3-ang
    amt = CAPITAL
    try:
        for i in range(len(path)-1):
            a = path[i]
            b = path[i+1]
            # Find pair price
            pair1 = f"{b}{a}" # e.g. BTCINR means 1 BTC = x INR, so INR->BTC = amt / price
            pair2 = f"{a}{b}"
            price = 0
            if pair1 in prices:
                # a->b : e.g. INR->BTC, pair is BTCINR, price is INR per BTC
                price = prices[pair1]
                amt = (amt / price) * (1-FEE)
            elif pair2 in prices:
                price = prices[pair2]
                amt = (amt * price) * (1-FEE)
            else:
                return None
            if amt<=0:
                return None
        profit_pct = (amt - CAPITAL)/CAPITAL*100
        return amt, profit_pct
    except:
        return None

def run_bot():
    print("=== KUBERABOT 3-9 ANG RELOADED Rs3000 SAFE ===", flush=True)
    while True:
        try:
            prices = get_prices()
            if not prices:
                time.sleep(5)
                continue
            
            # Generate all paths 3 to 9 ang: INR -> ... -> INR
            for length in range(3, 10): # 3 to 9
                # length = number of edges, coins in middle = length-1
                # We need permutations of SYMBOLS
                for coins in itertools.permutations(SYMBOLS, length-1):
                    path = [BASE] + list(coins) + [BASE] if length>2 else [BASE, coins[0], BASE]
                    # For 3-ang: INR->BTC->ETH->INR would be length 3? Actually need 2 mids
                    # Let's correct: 3-ang = INR->A->B->INR = length 3 edges, 2 mids
                    # So we already did: for length=3, we need 2 coins
                    if len(path)-1 != length:
                        continue
                    # Avoid too many: limit to first 4 coins for 8-9 ang to prevent crash
                    if length>=7 and len(set(coins))<length-1:
                        continue

                    res = calc_profit(prices, path)
                    if not res:
                        continue
                    amt, pct = res
                    path_str = "->".join(path)
                    if pct >= MIN_PROFIT*100:
                        print(f"PROFIT {length}-ANG: {path_str} | Rs{CAPITAL} -> Rs{amt:.2f} ({pct:.2f}%)", flush=True)
                    else:
                        # Print only some to avoid log flood - print every 20th
                        if length==3 or length==4:
                            print(f"Scan {length}-ang {path_str} : {pct:.2f}%", flush=True)
            time.sleep(15)
        except Exception as e:
            print(f"Error loop: {e}", flush=True)
            time.sleep(5)

import threading
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))import os, requests, time, threading
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "<h2>Kuberabot LIVE Fixed</h2>"

START_INR = 3000
MIN_PROFIT = 1.5
FEE = 0.001

def get_prices():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10).json()
        m = {}
        for x in r:
            try:
                price = float(x['last_price'])
                if 0.10 < price < 20000000:
                    m[x['market']] = price
            except:
                pass
        return m
    except:
        return {}

def calc(path, markets):
    amt = START_INR
    first = f"{path[0]}INR"
    if first not in markets:
        return 0, 0
    amt = amt / markets[first]
    for i in range(1, len(path)):
        frm = path[i-1]
        to = path[i]
        if to == "INR":
            mk = f"{frm}INR"
            if mk not in markets:
                return 0, 0
            amt = amt * markets[mk]
        else:
            m1 = f"{to}{frm}"
            m2 = f"{frm}{to}"
            if m1 in markets:
                amt = amt * markets[m1]
            elif m2 in markets:
                amt = amt / markets[m2]
            else:
                f_inr = f"{frm}INR"
                t_inr = f"{to}INR"
                if f_inr in markets and t_inr in markets:
                    amt = amt * markets[f_inr] / markets[t_inr]
                else:
                    return 0, 0
    if amt < 1500 or amt > 6000:
        return 0, 0
    net = amt * (1 - len(path)*FEE - 0.01)
    pct = (net-START_INR)/START_INR*100
    return net, pct

def run():
    paths = [["BTC","ETH","SOL","INR"],["BTC","ETH","USDT","INR"],["BTC","SOL","BNB","INR"],["ETH","SOL","BNB","INR"],["BTC","ETH","BNB","INR"],["SOL","MATIC","BNB","INR"]]
    print("=== KUBERABOT RELOADED Rs3000 SAFE ===", flush=True)
    while True:
        mkts = get_prices()
        if not mkts:
            time.sleep(5)
            continue
        for p in paths:
            net,pct = calc(p, mkts)
            if net == 0:
                continue
            arrow = "->".join(p)
            if pct >= MIN_PROFIT:
                print(f"PROFIT {len(p)}-ANG: INR->{arrow} | Rs3000 -> Rs{net:.2f} ({pct:.2f}%)", flush=True)
            else:
                print(f"Scan {len(p)}-ang INR->{arrow} : {pct:.2f}%", flush=True)
        time.sleep(15)

threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
