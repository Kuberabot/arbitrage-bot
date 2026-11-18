
import requests, time
from flask import Flask

app = Flask(__name__)
CAPITAL = 900
FEE = 0.001  # 0.1% per trade

# 55 COINS
COINS = ["BTC","ETH","BNB","SOL","XRP","ADA","DOGE","TRX","LINK","AVAX","LTC","DOT","MATIC","ATOM","NEAR","ARB","OP","APT","SUI","PEPE","SHIB","UNI","ETC","FIL","ALGO","VET","ICP","HBAR","MKR","AAVE","SAND","MANA","AXS","FTM","EGLD","FLOW","THETA","XTZ","EOS","KAVA","GRT","CHZ","ENJ","GALA","LRC","IMX","STX","RNDR","FET","INJ","TIA","SEI","BONK","WIF","XLM"]

last_data = []
last_scan = "Never"

def get_tickers():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=15)
        d = {}
        for x in r.json():
            # 【entity-CoinDCX¦canonical_name=CoinDCX】 gives bid/ask
            d[x['market']] = {'bid': float(x['bid']), 'ask': float(x['ask'])}
        return d
    except:
        return {}

def scan():
    global last_data, last_scan
    t = get_tickers()
    if not t or 'USDTINR' not in t:
        return
    results = []
    usdt_ask = t['USDTINR']['ask']
    usdt_bid = t['USDTINR']['bid']

    for c in COINS:
        m_usdt = f"{c}USDT"
        m_inr = f"{c}INR"
        if m_usdt not in t or m_inr not in t:
            continue
        # FORWARD: INR -> USDT -> COIN -> INR
        try:
            usdt = (CAPITAL / usdt_ask) * (1-FEE)
            coin = (usdt / t[m_usdt]['ask']) * (1-FEE)
            final_f = coin * t[m_inr]['bid'] * (1-FEE)
            profit_f = final_f - CAPITAL
            results.append((f"INR -> USDT -> {c} -> INR", final_f, profit_f, f"{usdt_ask} / {t[m_usdt]['ask']} / {t[m_inr]['bid']}"))
        except: pass
        # REVERSE: INR -> COIN -> USDT -> INR
        try:
            coin2 = (CAPITAL / t[m_inr]['ask']) * (1-FEE)
            usdt2 = coin2 * t[m_usdt]['bid'] * (1-FEE)
            final_r = usdt2 * usdt_bid * (1-FEE)
            profit_r = final_r - CAPITAL
            results.append((f"INR -> {c} -> USDT -> INR", final_r, profit_r, f"{t[m_inr]['ask']} / {t[m_usdt]['bid']} / {usdt_bid}"))
        except: pass

    results.sort(key=lambda x: x[2], reverse=True)
    last_data = results
    last_scan = time.strftime("%d %b %I:%M:%S %p")

scan()

@app.route("/")
def home():
    if not last_data:
        scan()
    html = f"""
    <h2>CoinDCX Triangular Arbitrage - Capital Rs.900 - 55 Coins x 2 Directions</h2>
    <p>Last scan: {last_scan} | Auto-refresh 30s | <a href='/scan'>Force Scan Now</a></p>
    <table border=1 cellpadding=6 style='border-collapse:collapse; font-size:14px;'>
    <tr><th>Path</th><th>Final INR</th><th>Profit</th><th>Ask1 / Ask2 / Bid3</th></tr>
    """
    for path, final, profit, prices in last_data:
        pct = profit/CAPITAL*100
        color = "green" if profit > 0 else "red"
        bg = "#d4edda" if profit > 0 else ""
        # Highlight big profit
        if profit > 9:
            bg = "#00ff00"
        html += f"<tr style='background:{bg}'><td>{path}</td><td>Rs.{final:.2f}</td><td style='color:{color}'><b>Rs.{profit:.2f} ({pct:.3f}%)</b></td><td>{prices}</td></tr>"
    html += "</table><p>Profit after 0.1% fee per trade. Green = Profitable. Bright Green = > Rs.9 (1%) - TRADE THIS!</p>"
    html += "<meta http-equiv='refresh' content='30'>"
    return html

@app.route("/scan")
def force():
    scan()
    return home()

@app.route("/debug")
def debug():
    t = get_tickers()
    return f"Tickers: {len(t)} | USDTINR: {t.get('USDTINR')} | BTCUSDT: {t.get('BTCUSDT')}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
