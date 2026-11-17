
import requests
import time
import logging
from decimal import Decimal, InvalidOperation
from flask import Flask
import threading

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger("coindcx-arb")

CAPITAL_INR = Decimal("900")
FEE_INR = Decimal("0.005")      # 0.50%
FEE_C2C = Decimal("0.0017")     # 0.17%
TDS = Decimal("0.01")           # 1% per sell leg
MIN_REPORT_PCT = Decimal("0.01")  # report only if gross > 0.01%

# CoinDCX market name format: B-BTC_INR, B-BTC_USDT, etc.
# We need INR pairs and USDT pairs
INR_PAIRS = ["B-BTC_INR", "B-ETH_INR", "B-SOL_INR", "B-XRP_INR", "B-DOGE_INR"]
USDT_PAIRS = ["B-BTC_USDT", "B-ETH_USDT", "B-SOL_USDT", "B-XRP_USDT", "B-DOGE_USDT"]
C2C_PAIRS = ["B-ETH_BTC", "B-SOL_BTC", "B-XRP_BTC"]  # crypto-to-crypto

state = {
    "best_path": "None",
    "best_net": Decimal("0"),
    "last_scan": "Starting...",
    "max_seen": Decimal("-999"),
}

def fetch_orderbook(pair):
    """Get top-of-book bid/ask for a pair. Returns (bid, ask) or None."""
    try:
        r = requests.get(
            f"https://api.coindcx.com/exchange/v1/orders/top?pair={pair}",
            timeout=5
        )
        if r.status_code != 200:
            return None
        data = r.json()
        # CoinDCX top orderbook response structure may vary; adjust if needed
        # Typical: {"bids": [["price","qty"],...], "asks": [...]}
        if isinstance(data, dict) and "bids" in data and "asks" in data:
            bid = Decimal(str(data["bids"][0][0]))
            ask = Decimal(str(data["asks"][0][0]))
            return (bid, ask)
        # Alternative structure: list of {price, quantity}
        if isinstance(data, list) and len(data) >= 2:
            # fallback: assume [bids_list, asks_list]
            pass
    except Exception as e:
        log.warning("fetch %s failed: %s", pair, e)
    return None

def build_price_map():
    """Build a dict of pair -> (bid, ask)."""
    prices = {}
    all_pairs = INR_PAIRS + USDT_PAIRS + C2C_PAIRS
    for pair in all_pairs:
        ob = fetch_orderbook(pair)
        if ob:
            prices[pair] = ob
        time.sleep(0.7)  # respect 100 req/min
    return prices

def find_3leg_cycles(prices):
    """Find all 3-leg loops: INR -> X -> Y -> INR (or via USDT)."""
    cycles = []
    # INR -> USDT -> COIN -> INR
    for coin in ["BTC", "ETH", "SOL", "XRP", "DOGE"]:
        usdt_pair = f"B-{coin}_USDT"
        inr_pair = f"B-{coin}_INR"
        if usdt_pair not in prices or inr_pair not in prices:
            continue
        # Buy coin with USDT (ask on USDT pair), sell coin for INR (bid on INR pair)
        # But we start with INR: first INR->USDT (need USDT_INR pair, not in our list yet)
        # Need to add USDT_INR
        pass

    # Simplified: INR -> COIN -> USDT -> INR (requires USDT_INR)
    # For now, just report what we can compute with available pairs
    return cycles

def scanner():
    while True:
        prices = build_price_map()
        if not prices:
            state["last_scan"] = f"{time.strftime('%H:%M:%S')} | No data"
            time.sleep(10)
            continue

        best_net = Decimal("-999")
        best_desc = "None"

        # Check 3-leg: INR -> BTC -> USDT -> INR (need BTC_INR, BTC_USDT, USDT_INR)
        # We don't have USDT_INR in pairs yet, add it
        # For now, report available pairs count
        pair_count = len(prices)
        state["last_scan"] = f"{time.strftime('%H:%M:%S')} | {pair_count} pairs fetched | waiting for path calc"

        # NOTE: Full 3-leg calculation requires USDT_INR pair.
        # Add "B-USDT_INR" to INR_PAIRS above if available on CoinDCX.

        time.sleep(8)  # safe for 100 req/min

@app.route("/")
def home():
    return f"""
    <html><body style='background:#111;color:#0f0;font-family:monospace;padding:15px'>
    <h3>CoinDCX Real Orderbook Scanner (No Keys, No Trading)</h3>
    <div style='border:1px solid #0f0;padding:10px;margin:8px 0'>
      Capital: ₹{CAPITAL_INR} | Mode: MONITOR ONLY
    </div>
    <div style='border:1px solid #0f0;padding:10px;margin:8px 0'>
      Best net seen: {state['max_seen']}%
    </div>
    <div style='border:1px solid #0f0;padding:10px;margin:8px 0'>
      {state['last_scan']}
    </div>
    <div style='border:1px solid #f80;padding:10px;margin:8px 0;color:#f80'>
      Cost floor: fees (0.17%-0.50% per leg) + 1% TDS on sell legs.<br>
      3-leg minimum cost ≈ 1.51%. If "Best net seen" &lt; 1.51%, strategy is structurally unprofitable.
    </div>
    </body></html>
    """

threading.Thread(target=scanner, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
