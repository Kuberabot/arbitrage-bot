
import time, requests, itertools, os
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "KUBERABOT ALL-COINS LIVE"

BASE = "INR"
CAP = 3000
FEE = 0.002
MINP = 0.8

def get_all():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=15).json()
        prices = {}
        coins = []
        for i in r:
            market = i.get('market','')
            try:
                price = float(i.get('last_price',0))
            except:
                continue
            if price <= 0:
                continue
            prices[market] = price
            if market.endswith(BASE):
                coin = market.replace(BASE,'')
                if coin and coin != BASE and coin not in coins:
                    coins.append(coin)
        return prices, coins
    except Exception as e:
        print(f"API FAIL {e}", flush=True)
        return {}, []

def calc(pr, path):
    a = CAP
    try:
        for j in range(len(path)-1):
            x = path[j]
            y = path[j+1]
            p1 = y + x
            p2 = x + y
            if p1 in pr:
                a = (a / pr[p1]) * (1 - FEE)
            elif p2 in pr:
                a = (a * pr[p2]) * (1 - FEE)
            else:
                return None
        return a, (a - CAP) / CAP * 100
    except:
        return None

def run():
    print("=== KUBERABOT ALL-COINS STARTED ===", flush=True)
    scan = 0
    while True:
        scan += 1
        pr, ALL_COINS = get_all()
        if not ALL_COINS:
            time.sleep(5)
            continue
        total = len(ALL_COINS) * (len(ALL_COINS)-1)
        print(f"\n--- SCAN #{scan} TIME {time.strftime('%H:%M:%S')} COINS={len(ALL_COINS)} COMBOS={total} ---", flush=True)
        print(f"Coins list: {ALL_COINS[:20]}...", flush=True)
        
        profit = 0
        for c1, c2 in itertools.permutations(ALL_COINS, 2):
            path = [BASE, c1, c2, BASE]
            res = calc(pr, path)
            if res:
                amt, pct = res
                if pct >= MINP:
                    print(f"*** PROFIT {pct:.2f}% {'->'.join(path)} Rs{amt:.1f} ***", flush=True)
                    profit += 1
                elif pct >= 0.2:
                    print(f"{'->'.join(path)} +{pct:.2f}%", flush=True)
        
        if profit == 0:
            print(f"SCAN #{scan} DONE - No profit >{MINP}%", flush=True)
        time.sleep(10)

import threading
threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
