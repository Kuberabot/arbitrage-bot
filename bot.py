import os
import time
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# ===== SETTINGS - DO NOT CHANGE FEES =====
CAPITAL = 900  # Rs.900 per trade like before
MIN_PROFIT_PERCENT = 2.0  # <-- SAFE SETTING: Only show > 2%
BUY_FEE = 0.0059  # 【entity-CoinDCX¦canonical_name=CoinDCX】 0.50% + 18% GST = 0.59%
SELL_FEE = 0.0059 # Same on sell
TOTAL_FEE_PERCENT = (BUY_FEE + SELL_FEE) * 100  # = 1.18%

AUTO_TRADE = False  # Keep False for now. True = Real money!

# 【entity-CoinDCX¦canonical_name=CoinDCX】 Public API - No Key Needed For Prices
BASE_URL = "https://api.coindcx.com/exchange/ticker"

# Coins to scan - Top liquid coins only. Don't scan 86 low coins, they have high slippage
COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "MATIC", "DOT", "LTC", "NEAR", "APT", "ARB", "SUI", "AXS", "ICP", "ATOM", "FIL", "OP"]

last_results = []
last_scan_time = "Never"

def get_price(market):
    try:
        r = requests.get(BASE_URL, timeout=5)
        data = r.json()
        for item in data:
            if item['market'] == market:
                return float(item['last_price'])
        return None
    except:
        return None

def get_all_prices():
    try:
        r = requests.get(BASE_URL, timeout=10)
        return {x['market']: float(x['last_price']) for x in r.json()}
    except Exception as e:
        print("Price Error:", e)
        return {}

def scan_triangular():
    global last_results, last_scan_time
    prices = get_all_prices()
    if not prices:
        return []
    
    results = []
    
    # Strategy: INR -> COIN -> USDT -> INR
    # Example: Buy BTC with INR, Sell BTC for USDT, Sell USDT for INR
    # If USDT price in INR is different, we get profit
    
    usdt_inr = prices.get("USDTINR")
    if not usdt_inr:
        return []

    for coin in COINS:
        try:
            coin_inr_market = f"{coin}INR"
            coin_usdt_market = f"{coin}USDT"

            coin_inr_price = prices.get(coin_inr_market)
            coin_usdt_price = prices.get(coin_usdt_market)

            if not coin_inr_price or not coin_usdt_price:
                continue

            # Step 1: Buy Coin with INR
            coin_qty = (CAPITAL * (1 - BUY_FEE)) / coin_inr_price
            
            # Step 2: Sell Coin for USDT
            usdt_qty = coin_qty * coin_usdt_price * (1 - SELL_FEE)
            
            # Step 3: Sell USDT for INR
            final_inr = usdt_qty * usdt_inr * (1 - SELL_FEE)

            gross_profit = final_inr - CAPITAL
            gross_percent = (gross_profit / CAPITAL) * 100

            # Net profit AFTER all fees is already in calculation
            # Only keep if > 2%
            if gross_percent >= MIN_PROFIT_PERCENT:
                results.append({
                    "coin": coin,
                    "path": f"INR -> {coin} -> USDT -> INR",
                    "start": CAPITAL,
                    "final": round(final_inr, 2),
                    "profit_rs": round(gross_profit, 2),
                    "profit_pct": round(gross_percent, 3),
                    "status": "SAFE TO TRADE"
                })
            else:
                # For dashboard, show as skipped
                results.append({
                    "coin": coin,
                    "path": f"INR -> {coin} -> USDT -> INR",
                    "start": CAPITAL,
                    "final": round(final_inr, 2),
                    "profit_rs": round(gross_profit, 2),
                    "profit_pct": round(gross_percent, 3),
                    "status": "SKIP - Below 2%"
                })

        except Exception as e:
            print(f"Error {coin}: {e}")
            continue

    # Sort by profit high to low
    results.sort(key=lambda x: x['profit_pct'], reverse=True)
    last_results = results
    last_scan_time = time.strftime("%d %b %Y %I:%M %p")
    return results

HTML = """
<html><head><meta http-equiv="refresh" content="30">
<style>body{font-family:Arial;padding:15px} table{width:100%;border-collapse:collapse} th,td{border:1px solid #ddd;padding:8px;text-align:center} .green{color:green;font-weight:bold} .red{color:red} .safe{background:#d4edda}</style></head>
<body>
<h2>Triangular Arbitrage Bot - SAFE MODE</h2>
<p><b>Capital:</b> Rs.{{capital}} | <b>Min Profit Filter:</b> {{min_profit}}% | <b>Fees Already Deducted:</b> 1.18% | <b>AutoTrade:</b> {{auto}}</p>
<p><b>Last Scan:</b> {{scan_time}} | Auto-refresh every 30 sec</p>
<table><tr><th>Coin</th><th>Path</th><th>Final INR</th><th>Profit Rs</th><th>Profit %</th><th>Status</th></tr>
{% for r in results %}
<tr class="{{'safe' if r.profit_pct >= 2 else ''}}">
<td>{{r.coin}}</td><td>{{r.path}}</td><td>{{r.final}}</td>
<td class="{{'green' if r.profit_rs>0 else 'red'}}">{{r.profit_rs}}</td>
<td class="{{'green' if r.profit_pct>0 else 'red'}}">{{r.profit_pct}}%</td>
<td><b>{{r.status}}</b></td></tr>
{% endfor %}
</table>
<p style="color:#666;font-size:13px">Rule: Bot will ONLY show GREEN + SAFE when profit is above 2%. Below 2% = SKIP, do not trade.</p>
</body></html>
"""

@app.route("/")
def home():
    results = scan_triangular()
    return render_template_string(HTML, results=results, capital=CAPITAL, min_profit=MIN_PROFIT_PERCENT, auto=AUTO_TRADE, scan_time=last_scan_time)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
