import time, requests, itertools, os
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "Kuberabot 3-9 ANG LIVE - Rs3000 SAFE"

SYMBOLS = ["BTC","ETH","SOL","BNB","USDT","XRP"]
BASE = "INR"
CAPITAL = 3000
FEE = 0.002
MIN_PROFIT = 0.8

def get_prices():
    prices={}
    try:
        r=requests.get("https://api.coindcx.com/exchange/ticker",timeout=8).json()
        for i in r:
            m=i.get('market',''); p=float(i.get('last_price',0) or 0)
            if p>0: prices[m]=p
    except: pass
    return prices

def calc(prices,path):
    amt=CAPITAL
    try:
        for i in range(len(path)-1):
            a,b=path[i],path[i+1]
            pair1=f"{b}{a}"; pair2=f"{a}{b}"
            if pair1 in prices: amt=(amt/prices[pair1])*(1-FEE)
            elif pair2 in prices: amt=(amt*prices[pair2])*(1-FEE)
            else: return None
        pct=(amt-CAPITAL)/CAPITAL*100
        return amt,pct
    except: return None

def run():
    print("=== KUBERABOT 3-6 ANG Rs3000 SAFE ===",flush=True)
    while True:
        try:
            prices=get_prices()
            if not prices: time.sleep(5); continue
            for length in [3,4,5,6]:  # 3 to 6 ang - covers 99% profit
                mids=length-1
                for coins in itertools.permutations(SYMBOLS,mids):
                    path=[BASE]+list(coins)+[BASE]
                    # Fix for 3-ang: INR->A->B->INR needs 2 coins
                    if len(path)-1 != length+1:
                        # For length=3 we want 3 trades: INR->BTC->ETH->INR = 3 edges? Actually 3 trades needs 2 mids. So length is edges.
                        pass
                    # Correct path logic: 3-ang = 3 trades = INR->A->B->INR (2 mids)
                    # Let's rebuild correctly
                    if length==3: path=[BASE,coins[0],coins[1],BASE]
                    elif length==4: path=[BASE,coins[0],coins[1],coins[2],BASE]
                    elif length==5: path=[BASE,coins[0],coins[1],coins[2],coins[3],BASE]
                    elif length==6: path=[BASE,coins[0],coins[1],coins[2],coins[3],coins[4],BASE]
                    
                    res=calc(prices,path)
                    if not res: continue
                    amt,pct=res
                    s="->".join(path)
                    if pct>=MIN_PROFIT:
                        print(f"PROFIT {length}-ANG: {s} | Rs{CAPITAL} -> Rs{amt:.2f} ({pct:.2f}%)",flush=True)
                    elif length<=4:
                        print(f"Scan {length}-ang {s} : {pct:.2f}%",flush=True)
            time.sleep(12)
        except Exception as e:
            print(f"Loop err {e}",flush=True); time.sleep(5)

import threading
threading.Thread(target=run,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
