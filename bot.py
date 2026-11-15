
import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    key = os.getenv("COINDCX_API_KEY", "")
    secret = os.getenv("COINDCX_API_SECRET", "")
    bal = os.getenv("START_BALANCE", "900")
    
    html = f"""
    <html><head><meta name='viewport' content='width=device-width'>
    <style>body{{background:#000;color:#fff;font-family:Arial;padding:20px}}
    .box{{background:#111;padding:15px;border-radius:10px;margin:10px 0}}</style></head>
    <body>
    <h2>✅ BOT LIVE!</h2>
    <div class=box>START_BALANCE: {bal} INR</div>
    <div class=box>API KEY Length: {len(key)} (should be 40+)</div>
    <div class=box>API SECRET Length: {len(secret)} (should be 80+)</div>
    <div class=box>
    Status: {"✅ KEYS FOUND" if len(key)>20 else "❌ KEYS MISSING - Check Environment names ALL CAPS"}
    </div>
    <div class=box>
    <b>Your ₹900 wallet will show here after keys fixed</b><br>
    Debug: Key exists = {bool(key)}
    </div>
    <script>setTimeout(()=>location.reload(),5000)</script>
    </body></html>
    """
    return html

@app.route("/api/balance")
def bal_api():
    key = os.getenv("COINDCX_API_KEY", "")
    return {"key_len": len(key), "key_found": bool(key), "msg": "Add COINDCX_API_KEY in ALL CAPS"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
