import os, time, hmac, hashlib, json, requests
from flask import Flask
app = Flask(__name__)
API_KEY = os.getenv("COINDCX_API_KEY","").strip()
API_SECRET = os.getenv("COINDCX_API_SECRET","").strip()
def get_sig(secret, msg): return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
@app.route("/")
def home():
    inr_val=0; coins_html=""; err="Loading..."
    try:
        ts=int(time.time()*1000); body=json.dumps({"timestamp":ts}); sig=get_sig(API_SECRET, body)
        headers={"X-AUTH-APIKEY":API_KEY,"X-AUTH-SIGNATURE":sig,"Content-Type":"application/json"}
        r=requests.post("https://api.coindcx.com/exchange/v1/users/balances", data=body, headers=headers, timeout=10)
        err=f"Status {r.status_code}: {r.text[:400]}"
        if r.status_code==200:
            coins={}
            for x in r.json():
                av=float(x.get("balance",0))+float(x.get("locked_balance",0))
                if av>1e-9: coins[x.get("currency")]=av
                if x.get("currency")=="INR": inr_val=av
            coins_html="<br>".join([f"{k}: {v}" for k,v in coins.items()]) or "Wallet empty"
        else: coins_html=f"API Failed - {err}"
    except Exception as e: err=str(e); coins_html=err
    ops=""
    try:
        prices={x["market"]:float(x["last_price"]) for x in requests.get("https://api.coindcx.com/exchange/ticker", timeout=5).json()}
        for a,b,c in [("BTCINR","ETHBTC","ETHINR"),("BTCINR","XRPBTC","XRPINR")]:
            if a in prices and b in prices and c in prices:
                final=900/prices[a]/prices[b]*prices[c]; pct=(final-900)/9
                col="#0f0" if pct>0.1 else "#f55"
                ops+=f"<div style='background:#222;padding:8px;margin:5px 0;border-left:4px solid {col}'><b>{a}→{b}→{c}</b><br>₹900→₹{final:.2f} <span style='color:{col}'>{pct:.3f}%</span></div>"
    except: ops="Price load fail"
    return f"<html><head><meta name=viewport content='width=device-width'><style>body{{background:#000;color:#fff;font-family:Arial;padding:12px}} .card{{background:#111;padding:12px;border-radius:10px;margin:8px 0;border:1px solid #333}}</style></head><body><h3>🚀 BOT LIVE - FIXED</h3><div class=card><b>₹ Wallet: {inr_val} INR</b><br>Time: {time.strftime('%H:%M:%S')}</div><div class=card><b>Coins:</b><br>{coins_html}</div><div class=card><small style='color:yellow'>{err}</small></div><div class=card><b>Arbitrage:</b><br>{ops}</div><script>setTimeout(()=>location.reload(),15000)</script></body></html>"
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
