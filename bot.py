
import os, time, hmac, hashlib, json, requests, threading
from flask import Flask
app = Flask(__name__)

API_KEY = os.getenv("COINDCX_API_KEY","").strip()
API_SECRET = os.getenv("COINDCX_API_SECRET","").strip()
START_BAL = float(os.getenv("START_BALANCE","900"))

logs = []
last_trade = "No trades yet"

def sign(secret, body):
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

def get_balances():
    try:
        ts = int(time.time()*1000)
        body = json.dumps({"timestamp": ts})
        sig = sign(API_SECRET, body)
        headers = {"X-AUTH-APIKEY": API_KEY, "X-AUTH-SIGNATURE": sig, "Content-Type": "application/json"}
        r = requests.post("https://api.coindcx.com/exchange/v1/users/balances", data=body, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            inr = 0
            for x in data:
                if x.get("currency")=="INR":
                    inr = float(x.get("balance",0)) + float(x.get("locked_balance",0))
            return inr, f"OK {r.status_code}", data
        else:
            return START_BAL, f"API {r.status_code}: {r.text[:200]}", []
    except Exception as e:
        return START_BAL, f"Error: {e}", []

def check_arb():
    try:
        ticker = requests.get("https://api.coindcx.com/exchange/ticker", timeout=5).json()
        prices = {x["market"]: float(x["last_price"]) for x in ticker}
        # Triangle: INR->BTC->ETH->INR
        if "BTCINR" in prices and "ETHBTC" in prices and "ETHINR" in prices:
            # Start 900 INR -> BTC -> ETH -> INR
            btc_qty = 900 / prices["BTCINR"]
            eth_qty = btc_qty / prices["ETHBTC"]
            final_inr = eth_qty * prices["ETHINR"]
            profit = (final_inr - 900)/9
            return profit, final_inr, prices
        return -1, 0, {}
    except:
        return -1, 0, {}

def trader_loop():
    global last_trade, logs
    while True:
        try:
            profit, final_inr, prices = check_arb()
            if profit > 0.4:  # 0.4% profit = Trade!
                # Here would place real orders
                # For safety with ₹900, we just LOG it first
                last_trade = f"TRADE SIGNAL! Profit {profit:.2f}% | ₹900→₹{final_inr:.2f} at {time.strftime('%H:%M:%S')}"
                logs.insert(0, last_trade)
                logs = logs[:20]
                # REAL ORDER CODE (uncomment after you test):
                # Place orders here via /exchange/v1/orders/create
            time.sleep(5)
        except:
            time.sleep(5)

threading.Thread(target=trader_loop, daemon=True).start()

@app.route("/")
def home():
    inr, status, raw = get_balances()
    profit, final_inr, prices = check_arb()
    color = "#0f0" if profit>0.4 else "#f55"
    action = "✅ WOULD TRADE NOW!" if profit>0.4 else "❌ Waiting (saving money)"

    return f"""
    <html><head><meta name=viewport content=width=device-width>
    <style>body{{background:#000;color:#fff;font-family:Arial;padding:12px}}
    .card{{background:#111;padding:12px;border-radius:10px;margin:8px 0;border:1px solid #333}}
    .green{{color:#0f0;font-weight:bold;font-size:18px}}</style></head>
    <body>
    <h3>🚀 REAL AUTO-TRADER LIVE</h3>
    <div class=card>
      <div class=green>₹ Wallet: {inr} INR</div>
      API: {status}<br>
      Time: {time.strftime('%H:%M:%S')}
    </div>
    <div class=card>
      <b>Live Arbitrage:</b><br>
      <div style='border-left:4px solid {color};padding:8px;margin:6px 0;background:#222'>
      BTCINR→ETHBTC→ETHINR<br>
      ₹900 → ₹{final_inr:.2f} <span style='color:{color}'>{profit:.3f}% {action}</span>
      </div>
    </div>
    <div class=card>
      <b>Last Signal:</b><br>{last_trade}<br><br>
      <b>Logs:</b><br>{"<br>".join(logs) or "No trades yet - waiting for +0.4% profit"}
    </div>
    <div class=card>
      <small>Mode: REAL keys loaded, but PAPER trading for safety until you confirm. 
      When you see ✅ WOULD TRADE, I will enable real buy/sell.</small>
    </div>
    <script>setTimeout(()=>location.reload(),10000)</script>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
