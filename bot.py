
import os, time, hmac, hashlib, json, requests
from flask import Flask, jsonify, render_template_string
import threading
app = Flask(__name__)
API_KEY = os.getenv("COINDCX_API_KEY", "").strip()
API_SECRET = os.getenv("COINDCX_API_SECRET", "").strip()
START_BALANCE = float(os.getenv("START_BALANCE", "900"))
last_scan = {}
balance_cache = {"INR": 0, "status": "checking..."}
last_error = "none"

def get_signature(secret, body):
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

def coindcx_request(endpoint):
    global last_error
    if not API_KEY or not API_SECRET:
        last_error = "NO API KEY/SECRET in Render Env!"
        return None
    try:
        payload = {"timestamp": int(time.time()*1000)}
        body = json.dumps(payload)
        signature = get_signature(API_SECRET, body)
        headers = {"X-AUTH-APIKEY": API_KEY, "X-AUTH-SIGNATURE": signature, "Content-Type": "application/json"}
        url = f"https://api.coindcx.com{endpoint}"
        r = requests.post(url, data=body, headers=headers, timeout=15)
        last_error = f"Status {r.status_code}: {r.text[:300]}"
        print(last_error)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except Exception as e:
        last_error = f"Exception: {e}"
        print(last_error)
        return None

def get_balances():
    data = coindcx_request("/exchange/v1/users/balances")
    if data and isinstance(data, list):
        bal = {}
        for b in data:
            curr = b.get("currency")
            avail = float(b.get("balance",0))
            locked = float(b.get("locked_balance",0))
            if avail>0 or locked>0 or curr=="INR":
                bal[curr] = avail+locked
        return bal if bal else {"INR": 0}
    return None

def get_tickers():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10).json()
        prices = {}
        for t in r:
            prices[t["market"]] = float(t["last_price"])
        return prices
    except:
        return {}

def find_arbitrage():
    prices = get_tickers()
    if not prices:
        return []
    opps = []
    triangles = [("BTCINR","ETHBTC","ETHINR"),("BTCINR","XRPBTC","XRPINR"),("ETHINR","XRPETH","XRPINR")]
    for t1,t2,t3 in triangles:
        if t1 in prices and t2 in prices and t3 in prices:
            try:
                amt = 1000
                first = amt / prices[t1]
                second = first / prices[t2]
                final = second * prices[t3]
                profit = final - amt
                pct = (profit/amt)*100
                opps.append({"path": f"{t1}->{t2}->{t3}", "end": round(final,2), "profit": round(profit,2), "profit_pct": round(pct,3)})
            except:
                continue
    opps.sort(key=lambda x: x["profit_pct"], reverse=True)
    return opps[:5]

def scanner_loop():
    global last_scan, balance_cache
    while True:
        try:
            opps = find_arbitrage()
            bals = get_balances()
            if bals:
                balance_cache = bals
            last_scan = {"time": time.strftime("%H:%M:%S"), "opportunities": opps, "balances": balance_cache, "error": last_error, "keys_present": bool(API_KEY)}
        except Exception as e:
            print(e)
        time.sleep(10)

threading.Thread(target=scanner_loop, daemon=True).start()

HTML = """<html><head><meta name="viewport" content="width=device-width"><style>body{background:#000;color:#fff;padding:15px;font-family:Arial}.card{background:#222;padding:12px;border-radius:10px;margin:8px 0;border-left:4px solid #0f0}.err{border-left-color:red;color:#f88}</style><script>setTimeout(()=>location.reload(), 15000)</script></head><body><h2>🤖 Bot LIVE</h2><p>Start: {{start}} | Time: {{time}} | Keys: {{keys}}</p><div class="card err"><b>DEBUG ERROR:</b><br>{{error}}</div><div class="card"><b>Wallet:</b><br>{{balances}}</div><h3>Opportunities</h3>{% for o in opps %}<div class="card">{{o.path}} | 1000->{{o.end}} | {{o.profit_pct}}%</div>{% endfor %}</body></html>"""

@app.route("/")
def home():
    return render_template_string(HTML, time=last_scan.get("time","..."), opps=last_scan.get("opportunities",[]), balances=json.dumps(balance_cache, indent=2), start=START_BALANCE, error=last_scan.get("error","waiting..."), keys=last_scan.get("keys_present", False))

@app.route("/api/balance")
def api_balance():
    return jsonify({"balances": get_balances(), "error": last_error, "key_len": len(API_KEY), "secret_len": len(API_SECRET)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
