import os
import time
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

CAPITAL = 900
MIN_PROFIT_PERCENT = 2.0
TOTAL_COST_PERCENT = 1.30

COINS = ["BTC","ETH","SOL","XRP","DOGE","ADA","AVAX","LINK","DOT","LTC","NEAR","APT","ARB","SUI","AXS","ICP","ATOM","FIL","OP","MATIC"]

# ---------- 1. 【entity-CoinDCX¦canonical_name=CoinDCX】 ----------
def get_coindcx():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10)
        data = r.json()
        prices = {}
        usdt_inr = 0
        for x in data:
            if x['market'] == "USDTINR":
                usdt_inr = float(x['last_price'])
            prices[x['market']] = float(x['last_price'])
        out = {}
        for c in COINS:
            if c+"INR" in prices and usdt_inr:
                out[c] = prices[c+"INR"] / usdt_inr
        return out
    except Exception as e:
        print("【entity-CoinDCX¦canonical_name=CoinDCX】 Error:", e)
        return {}

# ---------- 2. 【entity-Binance¦canonical_name=Binance】 ----------
def get_binance():
    urls = [
        "https://api.binance.us/api/v3/ticker/price",
        "https://data-api.binance.vision/api/v3/ticker/price",
        "https://api.binance.com/api/v3/ticker/price"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                out = {}
                for x in data:
                    if x['symbol'].endswith("USDT"):
                        coin = x['symbol'].replace("USDT","")
                        if coin in COINS:
                            out[coin] = float(x['price'])
                return out
        except:
            continue
    return {}

# ---------- 3. 【entity-KuCoin¦canonical_name=KuCoin】 ----------
def get_kucoin():
    try:
        r = requests.get("https://api.kucoin.com/api/v1/market/allTickers", timeout=10)
        data = r.json().get("data", {}).get("ticker", [])
        out = {}
        for x in data:
            if x['symbol'].endswith("-USDT"):
                coin = x['symbol'].replace("-USDT","")
                if coin in COINS:
                    out[coin] = float(x['last'])
        return out
    except Exception as e:
        print("【entity-KuCoin¦canonical_name=KuCoin】 Error:", e)
        return {}

# ---------- 4. MEXC ----------
def get_mexc():
    try:
        r = requests.get("https://api.mexc.com/api/v3/ticker/price", timeout=10)
        data = r.json()
        out = {}
        for x in data:
            if x['symbol'].endswith("USDT"):
                coin = x['symbol'].replace("USDT","")
                if coin in COINS:
                    out[coin] = float(x['price'])
        return out
    except Exception as e:
        print("MEXC Error:", e)
        return {}

def scan():
    cdcx = get_coindcx()
    binp = get_binance()
    ku = get_kucoin()
    mexc = get_mexc()

    all_prices = {
        "【entity-CoinDCX¦canonical_name=CoinDCX】": cdcx,
        "【entity-Binance¦canonical_name=Binance】": binp,
        "【entity-KuCoin¦canonical_name=KuCoin】": ku,
        "MEXC": mexc,
    }
    print("Loaded:", {k: len(v) for k,v in all_prices.items()})

    results = []
    for coin in COINS:
        lst = []
        for ex, mp in all_prices.items():
            if coin in mp and mp[coin] > 0:
                lst.append((ex, mp[coin]))
        if len(lst) < 2:
            continue
        buy_ex, buy_price = min(lst, key=lambda x: x[1])
        sell_ex, sell_price = max(lst, key=lambda x: x[1])
        diff_pct = ((sell_price - buy_price) / buy_price) * 100
        net_pct = diff_pct - TOTAL_COST_PERCENT
        final_inr = CAPITAL + (CAPITAL * net_pct / 100)
        results.append({
            "coin": coin,
            "buy_ex": buy_ex, "sell_ex": sell_ex,
            "buy": round(buy_price, 4), "sell": round(sell_price, 4),
            "diff": round(diff_pct, 3),
            "final": round(final_inr, 2),
            "profit_pct": round(net_pct, 3),
            "status": "PROFIT - TRADE" if net_pct >= MIN_PROFIT_PERCENT else "SKIP"
        })
    results.sort(key=lambda x: x['profit_pct'], reverse=True)
    scan_time = time.strftime("%d %b %Y %I:%M %p")
    return results, scan_time

HTML = """
<html><head><meta http-equiv="refresh" content="30">
<style>body{font-family:Arial;padding:12px} table{width:100%;border-collapse:collapse} th,td{border:1px solid #ddd;padding:7px;text-align:center;font-size:12px} .green{color:green;font-weight:bold} .red{color:red} .safe{background:#d4edda}</style></head>
<body>
<h2>MULTI-EXCHANGE Arbitrage - 4 Live Exchanges</h2>
<p><b>Capital:</b> Rs.900 | <b>Min Profit:</b> 2.0% | <b>Fees:</b> 1.30% | <b>Last Scan:</b> {{scan_time}}</p>
<p style="font-size:12px;color:green"><b>Exchanges: CoinDCX | Binance | KuCoin | MEXC - WazirX REMOVED</b></p>
<table><tr><th>Coin</th><th>Buy On</th><th>Sell On</th><th>Buy Price</th><th>Sell Price</th><th>Diff %</th><th>Final INR</th><th>Profit %</th><th>Status</th></tr>
{% for r in results %}
<tr class="{{ 'safe' if r.profit_pct >= 2 else '' }}">
<td><b>{{r.coin}}</b></td><td>{{r.buy_ex}}</td><td>{{r.sell_ex}}</td><td>{{r.buy}}</td><td>{{r.sell}}</td><td>{{r.diff}}%</td><td>{{r.final}}</td><td class="{{ 'green' if r.profit_pct>0 else 'red' }}">{{r.profit_pct}}%</td><td><b>{{r.status}}</b></td></tr>
{% endfor %}
</table>
<p style="font-size:11px;color:#666">Scanning only. No auto buy/sell yet.</p>
</body></html>
"""

@app.route("/")
def home():
    results, scan_time = scan()
    return render_template_string(HTML, results=results, scan_time=scan_time)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
