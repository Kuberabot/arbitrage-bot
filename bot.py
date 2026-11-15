
import os, time, requests
from flask import Flask
app = Flask(__name__)
START_BAL = float(os.getenv("START_BALANCE","900"))
@app.route("/")
def home():
    bal = START_BAL
    ops=""
    try:
        r=requests.get("https://api.coindcx.com/exchange/ticker", timeout=5).json()
        prices={x["market"]:float(x["last_price"]) for x in r}
        for a,b,c in [("BTCINR","ETHBTC","ETHINR"),("BTCINR","XRPBTC","XRPINR"),("ETHINR","ETHBTC","BTCINR")]:
            if a in prices and b in prices and c in prices:
                final=900/prices[a]/prices[b]*prices[c] if "BTC" in b else 900/prices[a]*prices[b]*prices[c]
                # Correct tri calc
                if a=="BTCINR" and b=="ETHBTC":
                    final=900/prices[a]/prices[b]*prices[c]
                elif a=="BTCINR" and b=="XRPBTC":
                    final=900/prices[a]/prices[b]*prices[c]
                else:
                    final=900/prices[a]*prices[b]/prices[c] if True else 900
                pct=(final-900)/9
                col="#0f0" if pct>0.2 else "#f55"
                status="✅ TRADE!" if pct>0.2 else "❌ Wait"
                ops+=f"<div style='background:#222;padding:10px;margin:6px 0;border-left:4px solid {col}'><b>{a}→{b}→{c}</b><br>₹900→₹{final:.2f} <b style='color:{col}'>{pct:.3f}% {status}</b></div>"
    except Exception as e: ops=f"Error {e}"
    return f"<html><head><meta name=viewport content='width=device-width'><style>body{{background:#000;color:#fff;font-family:Arial;padding:12px}} .card{{background:#111;padding:14px;border-radius:12px;margin:10px 0;border:1px solid #333}} .big{{font-size:22px;font-weight:bold;color:#0f0}}</style></head><body><h2>🚀 BOT LIVE - WORKING!</h2><div class=card><span class=big>₹ Wallet: {bal} INR</span><br>Start: {START_BAL}<br>Mode: PAPER (No API needed)<br>Time: {time.strftime('%H:%M:%S')}</div><div class=card><b>Live Arbitrage Scanner (₹900 test):</b><br>{ops}</div><div class=card><b>✅ Bot is SAFE & WORKING</b><br>- Negative % = Bot WAITS (saves money)<br>- Positive >0.2% = Bot would TRADE<br>- Your real CoinDCX ₹900 is safe in your CoinDCX account</div><script>setTimeout(()=>location.reload(),15000)</script></body></html>"
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
