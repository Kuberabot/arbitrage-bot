
import os, time, hmac, hashlib, json, requests
from flask import Flask, jsonify, render_template_string
import threading
app = Flask(__name__)
API_KEY = os.getenv("COINDCX_API_KEY", "")
API_SECRET = os.getenv("COINDCX_API_SECRET", "")
START_BALANCE = float(os.getenv("START_BALANCE", "900"))
AUTO_TRADE = False
MIN_PROFIT_PCT = 0.5
last_scan = {}
balance_cache = {"INR": 0}
trade_history = []
def get_signature(secret, body):
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
def coindcx_request(endpoint):
    if not API_KEY or not API_SECRET:
        return None
    try:
        payload = {"timestamp": int(time.time()*1000)}
        body = json.dumps(payload)
        signature = get_signature(API_SECRET, body)
        headers = {"X-AUTH-APIKEY": API_KEY,"X-AUTH-SIGNATURE": signature,"Content-Type": "application/json"}
        url = f"https://api.coindcx.com{endpoint}"
        r = requests.post(url, data=body, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(r.text[:500])
            return None
    except Exception as e:
        print(f"Error: {e}")
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
                bal[curr] = {"available": avail, "locked": locked, "total": avail+locked}
        return bal
    return {"raw": data}
def get_tickers():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10)
        data = r.json()
        prices = {}
        for t in data:
            prices[t["market"]] = float(t["last_price"])
        return prices
    except:
        return {}
def find_triangular_arbitrage():
    prices = get_tickers()
    if not prices:
        return []
    opps = []
    triangles = [("BTCINR","ETHBTC","ETHINR"),("BTCINR","XRPBTC","XRPINR"),("ETHINR","XRPETH","XRPINR"),("BTCINR","LTCBTC","LTCINR"),("ETHINR","LTCETH","LTCINR"),("BTCINR","BCHBTC","BCHINR")]
    for t1,t2,t3 in triangles:
        if t1 in prices and t2 in prices and t3 in prices:
            try:
                amt = 1000
                first = amt / prices[t1]
                second = first / prices[t2]
                final = second * prices[t3]
                profit = final - amt
                pct = (profit/amt)*100
                if pct > -5:
                    opps.append({"path": f"{t1} -> {t2} -> {t3}","end": round(final,2),"profit": round(profit,2),"profit_pct": round(pct,3),"prices": {t1: prices[t1], t2: prices[t2], t3: prices[t3]}})
            except:
                continue
    opps.sort(key=lambda x: x["profit_pct"], reverse=True)
    return opps[:6]
def scanner_loop():
    global last_scan, balance_cache
    while True:
        try:
            opps = find_triangular_arbitrage()
            bals = get_balances()
            if bals:
                balance_cache = bals
            last_scan = {"time": time.strftime("%d %b %H:%M:%S IST"),"opportunities": opps,"balances": balance_cache}
        except Exception as e:
            print(f"Scanner error {e}")
        time.sleep(12)
threading.Thread(target=scanner_loop, daemon=True).start()
HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>CoinDCX Bot LIVE</title>
<style>body{font-family:Arial;background:#0a0a0a;color:#fff;padding:15px}.card{background:#1e1e1e;border-radius:12px;padding:14px;margin:10px 0;border-left:4px solid #00ff88}.profit{color:#00ff88;font-weight:bold}.loss{color:#ff6666}.badge{background:#00ff88;color:#000;padding:3px 8px;border-radius:12px;font-size:11px}pre{white-space:pre-wrap;word-break:break-all;font-size:12px}</style>
<script>setTimeout(()=>location.reload(), 20000);</script></head>
<body>
<h2>🤖 CoinDCX Arbitrage <span class="badge">LIVE</span></h2>
<p>Start: {{start}} INR | Last: {{time}}</p>
<h3>💰 Real Wallet</h3>
<div class="card"><pre>{{balances_str}}</pre></div>
<h3>📈 Opportunities</h3>
{% for o in opps %}<div class="card"><b>{{o.path}}</b><br>1000 -> {{o.end}} = {{o.profit}} INR ({{o.profit_pct}}%)</div>{% else %}<div class="card">Scanning... refresh in 15s</div>{% endfor %}
</body></html>
"""
@app.route("/")
def home():
    return render_template_string(HTML, time=last_scan.get("time","Starting..."),opps=last_scan.get("opportunities",[]),balances=balance_cache,balances_str=json.dumps(balance_cache, indent=2),start=START_BALANCE)
@app.route("/api/scan")
def api_scan():
    return jsonify(last_scan)
@app.route("/api/balance")
def api_balance():
    return jsonify(get_balances())
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
