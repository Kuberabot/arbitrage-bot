
import os, time, hmac, hashlib, json, requests
from flask import Flask

app = Flask(__name__)

CAPITAL = 900
FEE = 0.001
MIN_PROFIT_PCT = 1.5
COINS = ["BTC","ETH","BNB","SOL","XRP","ADA","DOGE","MATIC","LTC","TRX","AVAX","DOT","LINK","ICP","NEAR","APT","ARB","FIL","ATOM","HBAR","SUI","INJ","GALA","KAVA","PEPE","SHIB","WIF","BONK","TIA","ALGO","EGLD","UNI","ETC","XLM","VET","GRT","AXS","CHZ","SEI","STX","AAVE","KAS","FTM","OP","IMX","MKR","RNDR","QNT","RUNE","SAND","MANA","THETA"]

API_KEY = os.environ.get("COINDCX_API_KEY", "")
API_SECRET = os.environ.get("COINDCX_SECRET", "").encode()
AUTO_VAL = os.environ.get("AUTO_TRADE", "FALSE")
if AUTO_VAL == "TRUE":
    AUTO_TRADE = True
else:
    AUTO_TRADE = False

BASE = "https://api.coindcx.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_tickers():
    try:
        r = requests.get(BASE + "/exchange/ticker", headers=HEADERS, timeout=10)
        print("STATUS")
        print(r.status_code)
        data = r.json()
        print("TYPE")
        print(type(data))
        t = {}
        if isinstance(data, dict):
            # CoinDCX sometimes returns {"data": [...]}
            if "data" in data:
                data = data["data"]
            else:
                return t, "Dict keys: " + str(list(data.keys())[:5])
        for d in data:
            try:
                market = d.get('market')
                if market is None:
                    market = d.get('pair')
                if market:
                    t[market] = {'bid': float(d['bid']), 'ask': float(d['ask'])}
            except:
                pass
        return t, "OK got " + str(len(t)) + " markets"
    except Exception as e:
        return {}, "ERROR: " + str(e)

def do_scan():
    t, debug = get_tickers()
    if not t:
        return [], "No tickers - " + debug, "Never"
    if 'USDTINR' not in t:
        keys = list(t.keys())[:10]
        return [], "USDTINR missing. Have: " + str(keys), "Never"
    usdt_ask = t['USDTINR']['ask']
    usdt_bid = t['USDTINR']['bid']
    results = []
    for c in COINS:
        m_usdt = c + "USDT"
        m_inr = c + "INR"
        if m_usdt not in t:
            continue
        if m_inr not in t:
            continue
        try:
            usdt = (CAPITAL / usdt_ask) * (1-FEE)
            coin = (usdt / t[m_usdt]['ask']) * (1-FEE)
            final_f = coin * t[m_inr]['bid'] * (1-FEE)
            profit_f = final_f - CAPITAL
            pct_f = (profit_f / CAPITAL) * 100
            results.append((c, final_f, profit_f, pct_f))
        except:
            pass
        try:
            coin2 = (CAPITAL / t[m_inr]['ask']) * (1-FEE)
            usdt2 = coin2 * t[m_usdt]['bid'] * (1-FEE)
            final_r = usdt2 * usdt_bid * (1-FEE)
            profit_r = final_r - CAPITAL
            pct_r = (profit_r / CAPITAL) * 100
            results.append((c, final_r, profit_r, pct_r))
        except:
            pass
    results.sort(key=lambda x: x[2], reverse=True)
    scan_time = time.strftime("%d %b %I:%M:%S %p")
    return results[:20], debug + " | Scanned " + str(len(results)), scan_time

@app.route("/")
def home():
    results, debug, scan_time = do_scan()
    html = "<h2>CoinDCX Auto-Trader - Capital Rs.900</h2>"
    html = html + "<p>Last scan: " + scan_time + "</p>"
    html = html + "<p>AutoTrade: " + str(AUTO_TRADE) + "</p>"
    html = html + "<p>Debug: " + debug + "</p>"
    html = html + "<table border=1 cellpadding=6><tr><th>Coin</th><th>Final INR</th><th>Profit</th><th>%</th></tr>"
    for coin_name, final, profit, pct in results:
        if profit > 0:
            color = "green"
        else:
            color = "red"
        html = html + "<tr><td>" + coin_name + "</td><td>" + str(round(final,2)) + "</td><td style='color:" + color + "'>" + str(round(profit,2)) + "</td><td>" + str(round(pct,3)) + "%</td></tr>"
    html = html + "</table><p>Auto-refresh 30s</p><meta http-equiv='refresh' content='30'>"
    return html

@app.route("/test")
def test():
    t, debug = get_tickers()
    return "Test: " + debug + " | USDTINR in list: " + str('USDTINR' in t)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
