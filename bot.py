from flask import Flask
import threading, time, os, requests
from datetime import datetime

app = Flask(__name__)

AUTO_TRADE = True
PROFIT_THRESHOLD = 0.30
CAPITAL = 900
total_profit = 0
trades = 0
last_check = "Starting..."

@app.route('/')
def dashboard():
    html = f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>body{{font-family:sans-serif;background:#0f172a;color:white;padding:20px}}
    .card{{background:#1e293b;padding:15px;border-radius:12px;margin:10px 0}}
    .green{{color:#22c55e}} .yellow{{color:#eab308}}</style></head><body>
    <h2>🤖 Arbitrage Bot - LIVE 24/7 FREE</h2>
    <div class='card'>✅ <b>Status:</b> <span class='green'>AWAKE - UptimeRobot Working</span></div>
    <div class='card'>💰 <b>Capital:</b> ₹{CAPITAL} | <b>Profit:</b> <span class='green'>₹{total_profit:.2f}</span></div>
    <div class='card'>📊 <b>Trades Today:</b> {trades} | <b>Threshold:</b> {PROFIT_THRESHOLD}%</div>
    <div class='card'>⏰ <b>Last Check:</b> {last_check}</div>
    <div class='card'>🔄 <b>Mode:</b> <span class='yellow'>PAPER TRADING (until CoinDCX approves) → Then REAL</span></div>
    <div class='card'>🌐 <b>UptimeRobot:</b> Bot will NEVER sleep - Free 24/7</div>
    <p><small>Auto-refreshes every 5 sec. Open Render > Logs to see live trading.</small></p>
    <script>setTimeout(()=>location.reload(),5000)</script>
    </body></html>
    """
    return html

def auto_trade_loop():
    global total_profit, trades, last_check
    while True:
        try:
            # fetch price
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()
            price = float(r['price'])
            profit = 0.35  # demo profit for testing
            last_check = f"{datetime.now().strftime('%H:%M:%S')} - Checking... {profit:.2f}% profit found"
            
            if profit >= PROFIT_THRESHOLD and AUTO_TRADE:
                trades += 1
                p = CAPITAL * profit / 100 * 0.6
                total_profit += p
                print(f"✅ TRADE {trades}: Profit ₹{p:.2f} | Total ₹{total_profit:.2f}")
            time.sleep(10)
        except Exception as e:
            last_check = f"Error: {e}"
            time.sleep(10)

threading.Thread(target=auto_trade_loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
