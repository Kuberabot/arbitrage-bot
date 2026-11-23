import os
import time
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

CAPITAL = 900
MIN_PROFIT_PERCENT = 2.0
TOTAL_COST_PERCENT = 1.30

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
    except Exception as e:
        print("【entity-CoinDCX¦canonical_name=CoinDCX】 Error:", e)
        return {}, 0

def get_all_binance_prices():
    try:
        r = requests.get("https://data-api.binance.vision/api/v3/ticker/price", timeout=10)
        data = r.json()
        prices = {}
        for x in data:
            prices[x['symbol']] = float(x['price'])
        return prices
    except Exception as e:
        print("【entity-Binance¦canonical_name=Binance】 Error:", e)
        return {}

def scan():
    cdcx, usdt_inr = get_coindcx_prices()
    bin_all = get_all_binance_prices()
    if not cdcx or usdt_inr == 0:
        return [], "【entity-CoinDCX¦canonical_name=CoinDCX】 API Error"
    if not bin_all:
        return [], "【entity-Binance¦canonical_name=Binance】 API Error"
    results = []
    for coin in COINS:
        try:
            cdcx_inr = cdcx.get(f"{coin}INR")
            if not cdcx_inr:
                continue
            cdcx_in_usdt = cdcx_inr / usdt_inr
            bin_price = bin_all.get(f"{coin}USDT")
            if not bin_price:
                continue
            diff_pct = ((cdcx_in_usdt - bin_price) / bin_price) * 100
            net_pct = diff_pct - TOTAL_COST_PERCENT
            final_inr = CAPITAL + (CAPITAL * net_pct / 100)
            results.append({
                "coin": coin,
                "path": "Buy 【entity-Binance¦canonical_name=Binance】 -> Sell 【entity-CoinDCX¦canonical_name=CoinDCX】",
                "【entity-binance¦canonical_name=Binance】": round(bin_price, 4),
                "coindcx_usdt": round(cdcx_in_usdt, 4),
                "diff": round(diff_pct, 3),
                "final": round(final_inr, 2),
                "profit_pct": round(net_pct, 3),
                "status": "PROFIT - TRADE" if net_pct >= MIN_PROFIT_PERCENT else "SKIP"
            })
            diff2_pct = ((bin_price - cdcx_in_usdt) / cdcx_in_usdt) * 100
            net2_pct = diff2_pct - TOTAL_COST_PERCENT
            final2_inr = CAPITAL + (CAPITAL * net2_pct / 100)
            results.append({
                "coin": coin,
                "path": "Buy CoinDCX -> Sell Binance",
                "binance": round(bin_price, 4),
                "coindcx_usdt": round(cdcx_in_usdt, 4),
                "diff": round(diff2_pct, 3),
                "final": round(final2_inr, 2),
                "profit_pct": round(net2_pct, 3),
                "status": "PROFIT - TRADE" if net2_pct >= MIN_PROFIT_PERCENT else "SKIP"
            })
        except Exception as e:
            print(f"Error {coin}: {e}")
            continue
    results.sort(key=lambda x: x['profit_pct'], reverse=True)
    scan_time = time.strftime("%d %b %Y %I:%M %p")
    return results, scan_time

HTML = """
<html><head><meta http-equiv="refresh" content="30">
<style>body{font-family:Arial;padding:15px} table{width:100%;border-collapse:collapse} th,td{border:1px solid #ddd;padding:8px;text-align:center;font-size:13px} .green{color:green;font-weight:bold} .red{color:red} .safe{background:#d4edda}</style></head>
<body>
<h2>REAL Arbitrage Bot - 【entity-CoinDCX¦canonical_name=CoinDCX】 vs 【entity-Binance¦canonical_name=Binance】</h2>
<p><b>Capital:</b> Rs.900 | <b>Min Profit:</b> 2.0% | <b>Fees Deducted:</b> 1.30% | <b>Last Scan:</b> {{scan_time}}</p>
<table><tr><th>Coin</th><th>Path</th><th>【entity-Binance¦canonical_name=Binance】</th><th>【entity-CoinDCX¦canonical_name=CoinDCX】</th><th>Diff %</th><th>Final INR</th><th>Profit %</th><th>Status</th></tr>
{% for r in results %}
<tr class="{{ 'safe' if r.profit_pct >= 2 else '' }}">
<td><b>{{r.coin}}</b></td><td>{{r.path}}</td><td>{{r.【entity-binance¦canonical_name=Binance】}}</td><td>{{r.coindcx_usdt}}</td><td>{{r.diff}}%</td><td>{{r.final}}</td><td class="{{ 'green' if r.profit_pct>0 else 'red' }}">{{r.profit_pct}}%</td><td><b>{{r.status}}</b></td></tr>
{% endfor %}
</table>
{% if not results %}<p style="color:red"><b>No data - wait 30 sec and refresh.</b></p>{% endif %}
</body></html>
"""

@app.route("/")
def home():
    results, scan_time = scan()
    return render_template_string(HTML, results=results, scan_time=scan_time)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
