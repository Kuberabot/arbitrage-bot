
import os, time, hmac, hashlib, json, requests, threading
from flask import Flask

app = Flask(__name__)

# --- CONFIG - SAFE, NO KEYS HERE ---
CAPITAL = 900
FEE = 0.001  # 0.1% per trade
MIN_PROFIT_PCT = 1.5  # Only trade if profit > 1.5%
COINS = ["BTC","ETH","BNB","SOL","XRP","ADA","DOGE","MATIC","LTC","TRX","AVAX","DOT","LINK","ICP","NEAR","APT","ARB","FIL","ATOM","HBAR","SUI","INJ","GALA","KAVA","PEPE","SHIB","WIF","BONK","TIA","ALGO","EGLD","UNI","ETC","XLM","VET","GRT","AXS","CHZ","SEI","STX","AAVE","KAS","FTM","OP","IMX","MKR","RNDR","QNT","RUNE","SAND","MANA","THETA"]

API_KEY = os.environ.get("COINDCX_API_KEY", "")
API_SECRET = os.environ.get("COINDCX_SECRET", "").encode()
AUTO_TRADE = os.environ.get("AUTO_TRADE", "FALSE") == "TRUE"
BASE = "https://api.coindcx.com"

last_data = []
last_scan = "Never"
last_trade = "No trade yet"
traded_recently = {}  # coin -> last trade time

def get_tickers():
    try:
        r = requests.get(f"{BASE}/exchange/ticker", timeout=10)
        data = r.json()
        t = {}
        for d in data:
            t[d['market']] = {'bid': float(d['bid']), 'ask': float(d['ask'])}
        return t
    except Exception as e:
        print(f"Ticker error: {e}")
        return {}

def place_order(market, side, quantity):
    """Real CoinDCX order - uses HMAC signature"""
    if not API_KEY:
        return {"error": "No API Key in Render Env"}
    url = f"{BASE}/exchange/v1/orders/create"
    body = {
        "side": side,  # "buy" or "sell"
        "order_type": "market_order",
        "market": market,
        "total_quantity": quantity
    }
    payload = json.dumps(body)
    signature = hmac.new(API_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    headers = {'Content-Type': 'application/json', 'X-AUTH-APIKEY': API_KEY, 'X-AUTH-SIGNATURE': signature}
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def scan_and_trade():
    global last_data, last_scan, last_trade
    while True:
        try:
            t = get_tickers()
            if not t or 'USDTINR' not in t:
                time.sleep(30)
                continue
            usdt_ask = t['USDTINR']['ask']
            usdt_bid = t['USDTINR']['bid']
            results = []
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
                    pct_f = (profit_f / CAPITAL) * 100
                    results.append((f"INR -> USDT -> {c} -> INR", round(final_f,2), round(profit_f,2), round(pct_f,3)))

                    # AUTO TRADE CHECK
                    if pct_f > MIN_PROFIT_PCT and AUTO_TRADE:
                        now = time.time()
                        if now - traded_recently.get(c, 0) > 3600:  # 1 hour cooldown
                            traded_recently[c] = now
                            # Step 1: Buy USDT with INR
                            qty_usdt = CAPITAL / usdt_ask
                            o1 = place_order("USDTINR", "buy", round(qty_usdt, 2))
                            time.sleep(2)
                            # Step 2: Buy COIN with USDT
                            o2 = place_order(m_usdt, "buy", round(coin, 4))
                            time.sleep(2)
                            # Step 3: Sell COIN to INR
                            o3 = place_order(m_inr, "sell", round(coin, 4))
                            last_trade = f"TRADED {c} Profit {profit_f:.2f} | {o1} {o2} {o3}"
                            print(last_trade)
                except: pass

                # REVERSE: INR -> COIN -> USDT -> INR (only scan, no auto trade for safety)
                try:
                    coin2 = (CAPITAL / t[m_inr]['ask']) * (1-FEE)
                    usdt2 = coin2 * t[m_usdt]['bid'] * (1-FEE)
                    final_r = usdt2 * usdt_bid * (1-FEE)
                    profit_r = final_r - CAPITAL
                    pct_r = (profit_r / CAPITAL) * 100
                    results.append((f"INR -> {c} -> USDT -> INR", round(final_r,2), round(profit_r,2), round(pct_r,3)))
                except: pass

            results.sort(key=lambda x: x[2], reverse=True)
            last_data = results[:20]
            last_scan = time.strftime("%d %b %I:%M:%S %p")
            print(f"Scan done {last_scan} Top: {last_data[0] if last_data else 'none'} | AutoTrade: {AUTO_TRADE}")
        except Exception as e:
            print(f"Scan error: {e}")
        time.sleep(30)  # Scan every 30 sec

# Start background thread
threading.Thread(target=scan_and_trade, daemon=True).start()

@app.route("/")
def home():
    html = f"<h2>CoinDCX Auto-Trader - Capital Rs.{CAPITAL} | AutoTrade: {AUTO_TRADE}</h2>"
    html += f"<p>Last scan: {last_scan} | Min Profit to Trade: {MIN_PROFIT_PCT}%</p>"
    html += f"<p><b>Last Trade:</b> {last_trade}</p>"
    html += "<table border=1 cellpadding=6><tr><th>Path</th><th>Final INR</th><th>Profit</th><th>%</th></tr>"
    for path, final, profit, pct in last_data:
        color = "green" if profit > 0 else "red"
        html += f"<tr><td>{path}</td><td>{final}</td><td style='color:{color}'>{profit}</td><td>{pct}%</td></tr>"
    html += "</table><p>Auto-refresh 30s</p><meta http-equiv='refresh' content='30'>"
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
