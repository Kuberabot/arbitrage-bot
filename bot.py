import os, time, hmac, hashlib, json, requests
from flask import Flask
import threading

app = Flask(__name__)

API_KEY = os.getenv("COINDCX_API_KEY","").strip()
API_SECRET = os.getenv("COINDCX_API_SECRET","").strip()
START_BAL = float(os.getenv("START_BALANCE","900"))

data = {"time":"starting...","inr":0,"coins":{},"ops":[],"err":"init"}

def get_signature(secret, message):
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

def get_balance():
    try:
        if not API_KEY: 
            data["err"] = "No API KEY"
            return None
        timestamp = int(time.time()*1000)
        body = {"timestamp": timestamp}
        json_body = json.dumps(body)
        signature = get_signature(API_SECRET, json_body)
        headers = {
            "X-AUTH-APIKEY": API_KEY,
            "X-AUTH-SIGNATURE": signature,
            "Content-Type": "application/json"
        }
        r = requests.post("https://api.coindcx.com/exchange/v1/users/balances", data=json_body, headers=headers, timeout=10)
        data["err"] = f"API {r.status_code}: {r.text[:150]}"
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        data["err"] = f"Error: {str(e)}"
        return None

def get_prices():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=5)
        return {x["market"]: float(x["last_price"]) for x in r.json()}
    except:
        return {}

def find_arbitrage():
    prices = get_prices()
    ops = []
    paths = [
        ("BTCINR","ETHBTC","ETHINR"),
        ("BTCINR","XRPBTC","XRPINR"),
        ("BTCINR","SOLBTC","SOLINR"),
    ]
    for a,b,c in paths:
        if a in prices and b in prices and c in prices and prices[a]>0 and prices[b]>0:
            try:
                start_amt = 900
                btc = start_amt / prices[a]
                mid = btc / prices[b] if prices[b]!=0 else 0
                final = mid * prices[c]
                profit = final - start_amt
                pct = profit/start_amt*100
                ops.append({"path": f"{a}→{b}→{c}", "start": start_amt, "end": round(final,2), "profit": round(profit,2), "pct": round(pct,3)})
            except:
                pass
    return sorted(ops, key=lambda x: x["pct"], reverse=True)[:5]

def loop():
    while True:
        try:
            data["ops"] = find_arbitrage()
            bal = get_balance()
            if bal and isinstance(bal, list):
                total_inr = 0
                coins = {}
                for x in bal:
                    curr = x.get("currency")
                    av = float(x.get("balance",0)) + float(x.get("locked_balance",0))
                    if av > 0.0000001:
                        coins[curr] = av
                        if curr == "INR":
                            total_inr = av
                data["coins"] = coins
                data["inr"] = total_inr if total_inr>0 else data["inr"]
            data["time"] = time.strftime("%H:%M:%S")
        except Exception as e:
            data["err"] = str(e)
        time.sleep(15)

threading.Thread(target=loop, daemon=True).start()

@app.route("/")
def home():
    ops_html = ""
    for o in data["ops"]:
        color = "#0f0" if o["pct"]>0 else "#f00"
        ops_html += f"<div style='background:#222;padding:12px;margin:8px 0;border-radius:10px;border-left:4px solid {color}'><b>{o['path']}</b><br>₹{o['start']} → ₹{o['end']} <span style='color:{color}'>{o['pct']}% (₹{o['profit']})</span></div>"
    
    coins_str = "<br>".join([f"{k}: {v}" for k,v in data["coins"].items()]) if data["coins"] else "Loading..."
    
    return f"""
    <html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
    <style>
    body{{background:#000;color:#fff;font-family:Arial;padding:15px;margin:0}}
    .card{{background:#111;padding:15px;border-radius:12px;margin:10px 0;border:1px solid #333}}
    .big{{font-size:22px;font-weight:bold}}
    .green{{color:#0f0}} .yellow{{color:#ff0}} .red{{color:#f55}}
    </style></head><body>
    <h2>🚀 ARBITRAGE BOT LIVE</h2>
    <div class=card><span class=big>₹ Wallet: {data['inr']} INR</span><br>Start: {START_BAL} INR<br>Time: {data['time']}</div>
    <div class=card><b>Your Coins:</b><br>{coins_str}</div>
    <div class=card><b>CoinDCX Response:</b><br><small class=yellow>{data['err']}</small></div>
    <div class=card><b>Best Arbitrage (₹900 test):</b>{ops_html if ops_html else "<br>Scanning markets..."}</div>
    <div class=card><small>Auto refreshes every 15 sec | If API error 401 = Check CoinDCX IP whitelist disabled & permissions Read enabled</small></div>
    <script>setTimeout(()=>location.reload(),15000)</script>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
