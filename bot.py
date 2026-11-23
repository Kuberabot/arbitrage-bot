import os
import time
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

CAPITAL = 900
MIN_PROFIT_PERCENT = 2.0
# CoinDCX Fee: 0.59% + 【entity-Binance¦canonical_name=Binance】 Fee: 0.10% + Transfer + Slippage = 1.30% total cost
TOTAL_COST_PERCENT = 1.30
AUTO_TRADE = False

COINS = ["BTC","ETH","SOL","XRP","DOGE","ADA","AVAX","LINK","DOT","LTC","NEAR","APT","ARB","SUI","AXS","ICP","ATOM","FIL","OP","MATIC"]

def get_coindcx_prices():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10)
        data = r.json()
        prices = {}
        usdt_inr = 0
        for x in data:
            if x['market'] == "USDTINR":
                usdt_inr = float(x['last_price'])
            prices[x['market']] = float(x['last_price'])
        return prices, usdt_inr
    except:
        return {}, 0

def get_binance_price(symbol):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT", timeout=5)
        return float(r.json()['price'])
    except:
        return None

def scan():
    cdcx, usdt_inr = get_coindcx_prices()
    if not cdcx or usdt_inr == 0:
        return [], "API Error - Retry"
    
    results = []
    for coin in COINS:
        try:
            # CoinDCX price in INR -> convert to USDT value
            cdcx_inr = cdcx.get(f"{coin}INR")
            if not cdcx_inr:
                continue
            cdcx_in_usdt = cdcx_inr / usdt_inr

            # Binance price in USDT
            bin_price = get_binance_price(coin)
            if not bin_price:
                continue

            # If CoinDCX is expensive, we BUY on Binance CHEAP, SELL on CoinDCX HIGH
            # Profit % before fees
            diff_pct = ((cdcx_in_usdt - bin_price) / bin_price) * 100
            # Net profit after all fees 1.30%
            net_pct = diff_pct - TOTAL_COST_PERCENT
            final_inr = CAPITAL + (CAPITAL * net_pct / 100)

            # Also reverse - Buy CoinDCX, Sell Binance (rare, but check)
            diff2_pct = ((bin_price - cdcx_in_usdt) / cdcx_in_usdt) * 100
            net2_pct = diff2_pct - TOTAL_COST_PERCENT
            final2_inr = CAPITAL + (CAPITAL * net2_pct / 100)

            results.append({
                "coin": coin,
                "path": "Buy Binance -> Sell CoinDCX",
                "binance": round(bin_price, 4),
                "coindcx_usdt": round(cdcx_in_usdt, 4),
                "diff": round(diff_pct, 3),
                "final": round(final_inr, 2),
                "profit_rs": round(final_inr - CAPITAL, 2),
                "profit_pct": round(net_pct, 3),
                "status": "✅ PROFIT - TRADE" if net_pct >= MIN_PROFIT_PERCENT else "SKIP"
            })
            results.append({
                "coin": coin,
                "path": "Buy CoinDCX -> Sell Binance",
                "【entity-binance¦canonical_name=Binance】": round(bin_price, 4),
                "coindcx_usdt": round(cdcx_in_usdt, 4),
                "diff": round(diff2_pct, 3),
                "final": round(final2_inr, 2),
                "profit_rs": round(final2_inr - CAPITAL, 2),
                "profit_pct": round(net2_pct, 3),
                "status": "✅ PROFIT - TRADE" if net2_pct >= MIN_PROFIT_PERCENT else "SKIP"
            })
        except:
            continue

    results.sort(key=lambda x: x['profit_pct'], reverse=True)
    scan_time = time.strftime("%d %b %Y %I:%M %p")
    return results, scan_time

HTML = """
<html><head><meta http-equiv="refresh" content="30">
<style>body{font-family:Arial;padding:15px} table{width:100%;border-collapse:collapse} th,td{border:1px solid #ddd;padding:8px;text-align:center;font-size:13px} .green{color:green;font-weight:bold} .red{color:red} .safe{background:#d4edda}</style></head>
<body>
<h2>✅ REAL Arbitrage Bot - CoinDCX vs Binance</h2>
<p><b>Capital:</b> Rs.900 | <b>Min Profit:</b> 2.0% | <b>Fees Deducted:</b> 1.30% | <b>Last Scan:</b> {{scan_time}}</p>
<table><tr><th>Coin</th><th>Path</th><th>Binance $</th><th>CoinDCX $</th><th>Diff %</th><th>Final INR</th><th>Profit %</th><th>Status</th></tr>
{% for r in results %}
<tr class="{{'safe' if r.profit_pct >= 2 else ''}}">
<td><b>{{r.coin}}</b></td><td>{{r.path}}</td><td>{{r.binance}}</td><td>{{r.coindcx_usdt}}</td><td>{{r.diff}}%</td><td>{{r.final}}</td>
<td class="{{'green' if r.profit_pct>0 else 'red'}}">{{r.profit_pct}}%</td>
<td><b>{{r.status}}</b></td></tr>
{% endfor %}
</table>
<p style="color:#666;font-size:13px">GREEN = Real profit after fees. This is cross-exchange, so it actually happens. Old bot was same-exchange, so it never happened.</p>
</body></html>
"""

@app.route("/")
def home():
    results, scan_time = scan()
    return render_template_string(HTML, results=results, scan_time=scan_time)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
