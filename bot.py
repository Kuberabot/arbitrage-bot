
# COPY EVERYTHING BELOW - THIS IS YOUR FINAL BOT
import os, time, hmac, hashlib, json, requests
from flask import Flask, jsonify, render_template_string
import threading
app = Flask(__name__)
API_KEY = os.getenv("COINDCX_API_KEY", "")
API_SECRET = os.getenv("COINDCX_API_SECRET", "")
START_BALANCE = float(os.getenv("START_BALANCE", "900"))
AUTO_TRADE = True
MIN_PROFIT_PCT = 0.5
TRADE_AMOUNT_INR = 850
last_scan = {}
balance_cache = {"INR": 0, "last_update": 0}
trade_history = []
def get_signature(secret, body):
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
def coindcx_request(endpoint, payload={}):
    if not API_KEY or not API_SECRET:
        return None
    try:
        body = json.dumps(payload)
        signature = get_signature(API_SECRET, body)
        headers = {"X-AUTH-APIKEY": API_KEY,"X-AUTH-SIGNATURE": signature,"Content-Type": "application/json"}
        url = f"https://api.coindcx.com{endpoint}"
        r = requests.post(url, data=body, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        print(f"API Error: {e}")
        return None
def get_balances():
    data = coindcx_request("/exchange/v1/users/balances")
    if data:
        bal = {}
        for b in data:
            if float(b.get("balance",0))>0 or b.get("currency")=="INR":
                bal[b["currency"]] = float(b["balance"])
        return bal
    return {}
def get_tickers():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=5).json()
        prices = {}
        for t in r:
            prices[t["market"]] = float(t["last_price"])
        return prices
    except:
        return {}
def find_triangular_arbitrage():
    prices = get_tickers()
    if not prices:
        return []
    opportunities = []
    triangles = [("BTCINR","ETHBTC","ETHINR"),("BTCINR","XRPBTC","XRPINR"),("ETHINR","XRPETH","XRPINR"),("BTCINR","LTCBTC","LTCINR"),("ETHINR","LTCETH","LTCINR"),("BTCINR","BCHBTC","BCHINR"),]
    for t1, t2, t3 in triangles:
        if t1 in prices and t2 in prices and t3 in prices:
            amount_inr = 1000
            try:
                if t2=="ETHBTC":
                    btc = amount_inr / prices[t1]
                    eth_amount = btc / prices[t2]
                    final_inr = eth_amount * prices[t3]
                elif t2=="XRPBTC":
                    btc = amount_inr / prices[t1]
                    xrp = btc / prices[t2]
                    final_inr = xrp * prices[t3]
                elif t1=="ETHINR" and t2=="XRPETH":
                    eth = amount_inr / prices[t1]
                    xrp = eth / prices[t2]
                    final_inr = xrp * prices[t3]
                else:
                    btc = amount_inr / prices[t1]
                    second = btc / prices[t2]
                    final_inr = second * prices[t3]
                profit = final_inr - amount_inr
                profit_pct = (profit / amount_inr) * 100
                if profit_pct > -2:
                    opportunities.append({"path": f"{t1} -> {t2} -> {t3}","start": amount_inr,"end": round(final_inr,2),"profit": round(profit,2),"profit_pct": round(profit_pct,3),"prices": {t1: prices[t1], t2: prices[t2], t3: prices[t3]}})
            except:
                continue
    opportunities.sort(key=lambda x: x["profit_pct"], reverse=True)
    return opportunities[:5]
def scanner_loop():
    global last_scan, balance_cache
    while True:
        try:
            opps = find_triangular_arbitrage()
            bals = get_balances()
            if bals:
                balance_cache = bals
                balance_cache["last_update"] = time.time()
            last_scan = {"time": time.strftime("%Y-%m-%d %H:%M:%S IST"),"opportunities": opps,"balances": balance_cache}
            print(f"Scan: best {opps[0]['profit_pct'] if opps else 0}%")
            if AUTO_TRADE and opps and opps[0]["profit_pct"] > MIN_PROFIT_PCT:
                best = opps[0]
                trade_history.append({"time": time.strftime("%H:%M:%S"),"path": best["path"],"profit_pct": best["profit_pct"],"status": "SIMULATED - Check profit for 24h then enable real"})
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(15)
threading.Thread(target=scanner_loop, daemon=True).start()
HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Auto Arbitrage LIVE</title><style>body{font-family:Arial;background:#0f0f0f;color:#fff;padding:15px}.card{background:#1e1e1e;border-radius:12px;padding:15px;margin:10px 0;border-left:4px solid #00ff88}.profit{color:#00ff88;font-weight:bold}.loss{color:#ff4444}.badge{background:#00ff88;color:#000;padding:4px 10px;border-radius:20px;font-size:12px}.live{animation:blink 1s infinite}@keyframes blink{0%{opacity:1}50%{opacity:0.3}}pre{white-space:pre-wrap}</style><script>setInterval(()=>location.reload(),15000);</script></head><body><h2>🤖 CoinDCX Bot <span class="badge live">LIVE</span></h2><p>Balance: {{balances}} | Start: {{start}} INR | MinProfit: {{minp}}%</p><p>Last: {{time}}</p><h3>💰 Real Balance</h3><div class="card"><pre>{{balances_str}}</pre></div><h3>📈 Top Opportunities</h3>{% for o in opps %}<div class="card"><b>{{o.path}}</b><br>1000 → {{o.end}} = <span class="{{'profit' if o.profit>0 else 'loss'}}">{{o.profit}} INR ({{o.profit_pct}}%)</span><br><small>{{o.prices}}</small>{% if o.profit_pct>0.5 %}<br><span class="badge">🔥 >0.5%</span>{% endif %}</div>{% endfor %}<h3>📜 History</h3><div class="card">{% for t in history %}{{t.time}} - {{t.path}} - {{t.profit_pct}}% - {{t.status}}<br>{% else %}Waiting for >0.5%...{% endfor %}</div></body></html>"""
@app.route("/")
def home():
    return render_template_string(HTML, time=last_scan.get("time","Starting..."),opps=last_scan.get("opportunities",[]),balances=balance_cache,balances_str=json.dumps(balance_cache, indent=2),start=START_BALANCE,auto=AUTO_TRADE,minp=MIN_PROFIT_PCT,history=trade_history[-10:])
@app.route("/api/scan")
def api_scan():
    return jsonify(last_scan)
@app.route("/api/balance")
def api_balance():
    return jsonify(get_balances())
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
