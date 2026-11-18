
import os
import time
import threading
from decimal import Decimal
import requests
from flask import Flask

app = Flask(__name__)

CAPITAL = Decimal("900")
FEE_PCT = Decimal("0.001")  # 0.1% per trade, 3 trades = 0.3%

# Triangular paths: (pair1, pair2, pair3, description)
# Example: INR -> USDT -> BTC -> INR
PATHS = [
    ("B-USDT_INR", "B-BTC_USDT", "B-BTC_INR", "INR -> USDT -> BTC -> INR"),
    ("B-USDT_INR", "B-ETH_USDT", "B-ETH_INR", "INR -> USDT -> ETH -> INR"),
    ("B-USDT_INR", "B-SOL_USDT", "B-SOL_INR", "INR -> USDT -> SOL -> INR"),
    ("B-USDT_INR", "B-XRP_USDT", "B-XRP_INR", "INR -> USDT -> XRP -> INR"),
    ("B-USDT_INR", "B-DOGE_USDT", "B-DOGE_INR", "INR -> USDT -> DOGE -> INR"),
    ("B-USDT_INR", "B-ADA_USDT", "B-ADA_INR", "INR -> USDT -> ADA -> INR"),
    ("B-USDT_INR", "B-LTC_USDT", "B-LTC_INR", "INR -> USDT -> LTC -> INR"),
    ("B-USDT_INR", "B-MATIC_USDT", "B-MATIC_INR", "INR -> USDT -> MATIC -> INR"),
]

state = {
    "last_scan": "Not scanned yet",
    "results": [],
    "errors": "",
}

def fetch_orderbook(pair):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    urls = [
        f"https://api.coindcx.com/market_data/orderbook?pair={pair}",
        f"https://public.coindcx.com/market_data/orderbook?pair={pair}",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()
            if "orderbook" in data:
                data = data["orderbook"]
            bids = data.get("bids", {})
            asks = data.get("asks", {})
            if not bids or not asks:
                continue
            if isinstance(bids, list):
                best_bid = max(Decimal(str(x[0])) for x in bids)
            else:
                best_bid = max(Decimal(str(p)) for p in bids.keys())
            if isinstance(asks, list):
                best_ask = min(Decimal(str(x[0])) for x in asks)
            else:
                best_ask = min(Decimal(str(p)) for p in asks.keys())
            return (best_bid, best_ask)
        except Exception:
            continue
    return None

def scan_once():
    results = []
    errors = []
    # Cache prices so we don't fetch same pair twice
    cache = {}
    def get_price(pair):
        if pair not in cache:
            cache[pair] = fetch_orderbook(pair)
        return cache[pair]

    for p1, p2, p3, label in PATHS:
        try:
            ob1 = get_price(p1)  # INR -> USDT : we BUY USDT with INR, use ASK
            ob2 = get_price(p2)  # USDT -> Coin : BUY Coin with USDT, use ASK
            ob3 = get_price(p3)  # Coin -> INR : SELL Coin for INR, use BID
            if not ob1 or not ob2 or not ob3:
                errors.append(f"{p1}/{p2}/{p3} no data")
                continue
            ask1 = ob1[1]
            ask2 = ob2[1]
            bid3 = ob3[0]
            if ask1 == 0 or ask2 == 0:
                continue
            # Step 1: INR -> USDT
            usdt = CAPITAL / ask1
            usdt_after_fee = usdt * (Decimal("1") - FEE_PCT)
            # Step 2: USDT -> Coin
            coin = usdt_after_fee / ask2
            coin_after_fee = coin * (Decimal("1") - FEE_PCT)
            # Step 3: Coin -> INR
            final_inr = coin_after_fee * bid3
            final_inr = final_inr * (Decimal("1") - FEE_PCT)
            profit = final_inr - CAPITAL
            profit_pct = (profit / CAPITAL) * Decimal("100")
            results.append({
                "path": label,
                "final": round(float(final_inr), 2),
                "profit": round(float(profit), 2),
                "profit_pct": round(float(profit_pct), 3),
                "ask1": str(ask1),
                "ask2": str(ask2),
                "bid3": str(bid3),
            })
        except Exception as e:
            errors.append(f"{label}: {e}")
    results.sort(key=lambda x: x["profit_pct"], reverse=True)
    state["results"] = results
    state["errors"] = " | ".join(errors[:3])
    state["last_scan"] = time.strftime("%d %b %I:%M:%S %p")

def scanner_loop():
    while True:
        try:
            scan_once()
        except Exception as e:
            state["last_scan"] = f"Error: {e}"
        time.sleep(30)

@app.route("/")
def home():
    rows = ""
    for r in state["results"]:
        color = "green" if r["profit"] > 0 else "red"
        rows += f"<tr><td>{r['path']}</td><td>Rs.{r['final']}</td><td style='color:{color}'><b>Rs.{r['profit']} ({r['profit_pct']}%)</b></td><td>{r['ask1']} / {r['ask2']} / {r['bid3']}</td></tr>"
    if not rows:
        rows = "<tr><td colspan='4'>Scanning... waiting for CoinDCX data. Refresh in 30 sec.</td></tr>"
    return f"""
    <html><head><meta http-equiv="refresh" content="30"><title>Arbitrage Bot</title></head>
    <body style="font-family:Arial;padding:16px">
    <h2>CoinDCX Triangular Arbitrage - Capital Rs.900</h2>
    <p>Last scan: {state['last_scan']} | Auto-refresh 30s | Errors: {state['errors']}</p>
    <table border="1" cellpadding="8" cellspacing="0">
    <tr><th>Path</th><th>Final INR</th><th>Profit</th><th>Ask1 / Ask2 / Bid3</th></tr>
    {rows}
    </table>
    <p style="color:gray;font-size:13px">Profit is after 0.1% fee per trade. Green = profitable.</p>
    </body></html>
    """

threading.Thread(target=scanner_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
