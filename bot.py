import os, time, threading, traceback
from decimal import Decimal
import requests
from flask import Flask
app = Flask(__name__)
CAPITAL = Decimal("900")
FEE_PCT = Decimal("0.001")
PATHS = [
    ("USDTINR","BTCUSDT","BTCINR","INR -> USDT -> BTC -> INR"),
    ("USDTINR","ETHUSDT","ETHINR","INR -> USDT -> ETH -> INR"),
    ("USDTINR","SOLUSDT","SOLINR","INR -> USDT -> SOL -> INR"),
    ("USDTINR","XRPUSDT","XRPINR","INR -> USDT -> XRP -> INR"),
    ("USDTINR","DOGEUSDT","DOGEINR","INR -> USDT -> DOGE -> INR"),
    ("USDTINR","ADAUSDT","ADAINR","INR -> USDT -> ADA -> INR"),
    ("USDTINR","LTCUSDT","LTCINR","INR -> USDT -> LTC -> INR"),
    ("USDTINR","MATICUSDT","MATICINR","INR -> USDT -> MATIC -> INR"),
    ("USDTINR","BNBUSDT","BNBINR","INR -> USDT -> BNB -> INR"),
    ("USDTINR","TRXUSDT","TRXINR","INR -> USDT -> TRX -> INR"),
]
state = {"last_scan":"Not scanned yet","results":[],"errors":"","debug":"No debug yet"}

def fetch_all_prices():
    headers = {"User-Agent":"Mozilla/5.0","Accept":"application/json"}
    urls = [
        "https://api.coindcx.com/exchange/ticker",
        "https://public.coindcx.com/exchange/ticker",
        "https://api.coindcx.com/exchange/v1/tickers",
    ]
    logs=[]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            logs.append(f"{url} -> status {r.status_code} len {len(r.text)} start:{r.text[:120]}")
            if r.status_code != 200:
                continue
            data = r.json()
            prices={}
            items = data if isinstance(data, list) else data.get("data", [])
            for item in items:
                m=item.get("market","")
                try:
                    prices[m]=(Decimal(str(item.get("bid"))), Decimal(str(item.get("ask"))))
                except: continue
            if prices:
                state["debug"]=" | ".join(logs)
                return prices
            logs.append(f"{url} parsed 0 prices")
        except Exception as e:
            logs.append(f"{url} EXCEPTION {e}")
    state["debug"]=" | ".join(logs)
    return {}

def scan_once():
    prices = fetch_all_prices()
    if not prices:
        state["errors"]="Ticker empty - see /debug"
        state["last_scan"]=time.strftime("%d %b %I:%M:%S %p")+" | NO DATA"
        return
    results=[]
    for p1,p2,p3,label in PATHS:
        try:
            if p1 not in prices or p2 not in prices or p3 not in prices: continue
            ask1=prices[p1][1]; ask2=prices[p2][1]; bid3=prices[p3][0]
            if ask1==0 or ask2==0: continue
            usdt=CAPITAL/ask1*(Decimal("1")-FEE_PCT)
            coin=usdt/ask2*(Decimal("1")-FEE_PCT)
            final=coin*bid3*(Decimal("1")-FEE_PCT)
            profit=final-CAPITAL
            results.append({"path":label,"final":round(float(final),2),"profit":round(float(profit),2),"profit_pct":round(float(profit/CAPITAL*100),3),"ask1":str(ask1),"ask2":str(ask2),"bid3":str(bid3)})
        except: continue
    results.sort(key=lambda x: x["profit_pct"], reverse=True)
    state["results"]=results; state["errors"]=""; state["last_scan"]=time.strftime("%d %b %I:%M:%S %p")

def loop():
    while True:
        try: scan_once()
        except Exception as e: state["last_scan"]=f"Error {e}"
        time.sleep(30)

@app.route("/")
def home():
    rows=""
    for r in state["results"]:
        c="green" if r["profit"]>0 else "red"
        rows+=f"<tr><td>{r['path']}</td><td>Rs.{r['final']}</td><td style='color:{c}'><b>Rs.{r['profit']} ({r['profit_pct']}%)</b></td><td>{r['ask1']} / {r['ask2']} / {r['bid3']}</td></tr>"
    if not rows: rows=f"<tr><td colspan='4'>Scanning... Refresh in 30 sec. Error: {state['errors']}</td></tr>"
    return f"<html><head><meta http-equiv='refresh' content='30'></head><body style='font-family:Arial;padding:16px'><h2>CoinDCX Triangular Arbitrage - Capital Rs.900</h2><p>Last scan: {state['last_scan']} | Auto-refresh 30s</p><p><a href='/debug'>View Debug</a></p><table border='1' cellpadding='8'><tr><th>Path</th><th>Final INR</th><th>Profit</th><th>Ask1 / Ask2 / Bid3</th></tr>{rows}</table><p>Profit after 0.1% fee.</p></body></html>"

@app.route("/debug")
def debug():
    return f"<html><body style='font-family:Arial;padding:16px;word-break:break-all'><h2>Debug</h2><p>Last: {state['last_scan']}</p><p>{state['debug']}</p><p><a href='/'>Back</a></p></body></html>"

threading.Thread(target=loop, daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
