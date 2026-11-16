
from flask import Flask, jsonify
import threading
import time
import os
import requests

app = Flask(__name__)

# ===== CONFIG - YOUR FREE SETUP =====
AUTO_TRADE = True  # Bot will trade by itself!
PROFIT_THRESHOLD = 0.30  # Will trade if profit > 0.30%
CAPITAL = 900  # Your capital

# This keeps bot alive for UptimeRobot
@app.route('/')
def home():
    return jsonify({
        "status": "✅ Bot is AWAKE 24/7 - FREE",
        "uptimerobot": "Working - Bot will never sleep!",
        "auto_trade": AUTO_TRADE,
        "capital": f"₹{CAPITAL}",
        "mode": "PAPER TRADING (until CoinDCX approves) → Then REAL Auto-Trade",
        "profit_threshold": f"{PROFIT_THRESHOLD}%"
    })

@app.route('/status')
def status():
    return home()

# ===== AUTO TRADING LOGIC - TRADES BY ITSELF =====
def get_prices():
    """Fetch prices - you can add real APIs later"""
    try:
        # Example: Binance price
        binance = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()
        binance_price = float(binance['price'])
        
        # For now using 0.5% difference simulation - Replace with CoinDCX API when approved
        coindcx_price = binance_price * 1.005  # Simulating difference
        
        profit = ((coindcx_price - binance_price) / binance_price) * 100
        return profit, binance_price, coindcx_price
    except:
        return 0, 0, 0

def auto_trade_loop():
    """This loop runs 24/7 and trades BY ITSELF - even at 3 AM!"""
    print("🤖 Auto-Trade Loop Started - Bot will trade by itself 24/7 FREE!")
    while True:
        try:
            profit, buy_price, sell_price = get_prices()
            
            print(f"Checking... Profit: {profit:.2f}% | Threshold: {PROFIT_THRESHOLD}%")
            
            if profit >= PROFIT_THRESHOLD and AUTO_TRADE:
                print(f"🚀 PROFIT FOUND! {profit:.2f}% - AUTO TRADING!")
                print(f"Buying at {buy_price} | Selling at {sell_price}")
                
                # PAPER TRADE (until CoinDCX approved)
                estimated_profit = (CAPITAL * profit / 100) - (CAPITAL * 0.004)  # minus fees
                print(f"✅ PAPER TRADE EXECUTED! Estimated Profit: ₹{estimated_profit:.2f}")
                
                # TODO: When CoinDCX API approved, real trade will happen here automatically
                # coindcx_buy() and binance_sell()
                
                time.sleep(60)  # Wait 1 min after trade to avoid double trade
            else:
                print(f"Waiting... No profit yet. Will check again in 10 sec")
                
            time.sleep(10)  # Check every 10 seconds 24/7
            
        except Exception as e:
            print(f"Error in auto-trade loop: {e}")
            time.sleep(10)

# Start auto-trade thread - THIS MAKES IT TRADE BY ITSELF!
threading.Thread(target=auto_trade_loop, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
