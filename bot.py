import os, time, hmac, hashlib, json, requests
from flask import Flask

app = Flask(__name__)

API_KEY = os.getenv("COINDCX_API_KEY","").strip()
API_SECRET = os.getenv("COINDCX_API_SECRET","").strip()
START_BAL = float(os.getenv("START_BALANCE","900"))

def get_signature(secret, message):
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

@app.route("/")
def home():
    # 1. Get CoinDCX Balance NOW (no thread)
    err_msg = "Checking..."
    coins_html = "Loading..."
    inr_val = 0
    
    try:
        timestamp = int(time.time()*1000)
        body = {"timestamp": timestamp}
        json_body = json.dumps(body)
        signature = get_signature(API_SECRET, json_body)
        headers = {
            "X-AUTH-APIKEY": API_KEY,
            "X-AUTH-SIGNATURE": signature
        }
        r = requests.post("https://api.coindcx.com/exchange/v1/users/balances", data=json_body, headers=headers, timeout=10)
        err_msg = f"Status {r.status_code}: {r.text[:300]}"
        if r.status_code == 200:
            bal_list = r.json()
            coins = {}
            for x in bal_list:
                curr = x.get("currency")
                av = float(x.get("balance",0)) + float(x.get("locked_balance",0))
                if av > 0.0000001:
                    coins[curr] = av
                    if curr == "INR":
                        inr_val = av
            coins_html = "<br>".join([f"{k}: {v}" for k,v in coins.items()]) if coins else "No coins (Empty?)"
        else:
            coins_html = f"API Failed - {err_msg}"
    except Exception as e:
        err_msg = f"Exception: {str(e)}"
        coins_html = err_msg

    # 2. Arbitrage
    ops_html = ""
    try:
        prices = {x["market"]: float(x["last_price"]) for x in requests.get("https://api.coindcx.com/exchange/ticker", timeout=5).json()}
        for a,b,c in [("BTCINR","ETHBTC","ETHINR"),("BTCINR","XRPBTC","XRPINR")]:
            if a in prices and b in prices and c in prices:
                start_amt = 900
                btc = start_amt / prices[a]
                mid = btc / prices[b]
                final = mid * prices[c]
                pct = (final-start_amt)/start_amt*100
                color = "#0f0" if pct>0 else "#f55"
                ops_html += f"<div style='background:#222;padding:10px;margin:6px 0;border-radius:8px;border-left:4px solid {color}'><b>{a}→{b}→{c}</b><br>₹900 → ₹{final:.2f} <span style='color:{color}'>{pct:.3f}%</span></div>"
    except Exception as e:
        ops_html = f"Price error {e}"

    return f"""
    <html><head><meta name='viewport' content='width=device-width'>
    <style>body{{background:#000;color:#fff;font-family:Arial;padding:15px}} .card{{background:#111;padding:15px;border-radius:12px;margin:10px 0;border:1px solid #333}} .big{{font-size:22px;font-weight:bold}}</style></head><body>
    <h2>🚀 BOT LIVE - DIRECT MODE</h2>
    <div class=card><span class=big>₹ Wallet: {inr_val} INR</span><br>Start: {START_BAL}<br>Time: {time.strftime("%H:%M:%S")}</div>
    <div class=card><b>Your Coins:</b><br>{coins_html}</div>
    <div class=card><b>CoinDCX Debug:</b><br><small style='color:yellow;word-break:break-all'>{err_msg}</small></div>
    <div class=card><b>Arbitrage (₹900 test):</b><br>{ops_html}</div>
    <div class=card>If error 401: Go to CoinDCX → API → Edit → DISABLE IP whitelist & Enable READ permission. If 0 INR but you have money: Your money is in Spot? This shows Spot wallet.</div>
    <script>setTimeout(()=>location.reload(),20000)</script>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
