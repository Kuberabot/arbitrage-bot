import os, requests, time, threading
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
                if price > 0.10 and price < 20000000:
                    m[x['market']] = price
            except: pass
        return m
    except: return {}def calc(path, markets):
    amt = START_INR
    first = f"{path[0]}INR"
    if first not in markets: return 0,0
    amt = amt / markets[first]
    for i in range(1, len(path)):
        frm = path[i-1]; to = path[i]
        if to == "INR":
            mk = f"{frm}INR"
            if mk not in markets: return 0,0
            amt = amt * markets[mk]
        else:
            m1 = f"{to}{frm}"; m2 = f"{frm}{to}"
            if m1 in markets: amt = amt * markets[m1]
            elif m2 in markets: amt = amt / markets[m2]
            else:
                f_inr = f"{frm}INR"; t_inr = f"{to}INR"
                if f_inr in markets and t_inr in markets:
                    amt = amt * markets[f_inr] / markets[t_inr]
                else: return 0,0
    if amt < 1500 or amt > 6000: return 0,0
    net = amt * (1 - len(path)*FEE - 0.01)
    pct = (net-START_INR)/START_INR*100
    return net, pctdef run():
    paths = [["BTC","ETH","SOL","INR"],["BTC","ETH","USDT","INR"],["BTC","SOL","BNB","INR"],["ETH","SOL","BNB","INR"],["BTC","ETH","BNB","INR"],["SOL","MATIC","BNB","INR"]]
    print("=== KUBERABOT RELOADED Rs3000 SAFE ===", flush=True)
    while True:
        mkts = get_prices()
        if not mkts: time.sleep(5); continue
        for p in paths:
            net,pct = calc(p, mkts)
            if net==0: continue
            arrow = "->".join(p)
            if pct >= MIN_PROFIT:
                print(f"PROFIT {len(p)}-ANG: INR->{arrow} | Rs3000 -> Rs{net:.2f} ({pct:.2f}%)", flush=True)
            else:
                print(f"Scan {len(p)}-ang INR->{arrow} : {pct:.2f}%", flush=True)
        time.sleep(15)
threading.Thread(target=run, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
