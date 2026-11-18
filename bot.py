
import requests
import time
from decimal import Decimal
from flask import Flask
import threading

app = Flask(__name__)

CAPITAL_INR = Decimal("900")

# Effective fees (GST included)
FEE_INR = Decimal("0.50") * Decimal("1.18") / Decimal("100")   # ≈ 0.0059
FEE_C2C = Decimal("0.17") * Decimal("1.18") / Decimal("100")   # ≈ 0.0020
TDS = Decimal("0.01")   # 1% per sell leg

# 3-leg paths: INR -> A -> B -> INR
# side decides bid or ask
PATHS = [
    # INR -> USDT -> BTC -> INR
    {"name": "INR→USDT→BTC→INR", "legs": [
        {"pair": "B-USDT_INR", "side": "buy"},   # buy USDT with INR, pay ask
        {"pair": "B-BTC_USDT", "side": "buy"},   # buy BTC with USDT, pay ask
        {"pair": "B-BTC_INR",  "side": "sell"},  # sell BTC for INR, receive bid
    ]},
    # INR -> BTC -> USDT -> INR
    {"name": "INR→BTC→USDT→INR", "legs": [
        {"pair": "B-BTC_INR",  "side": "buy"},
        {"pair": "B-BTC_USDT", "side": "sell"},
        {"pair": "B-USDT_INR", "side": "sell"},
    ]},
    # INR -> USDT -> ETH -> INR
    {"name": "INR→USDT→ETH→INR", "legs": [
        {"pair": "B-USDT_INR", "side": "buy"},
        {"pair": "B-ETH_USDT", "side": "buy"},
        {"pair": "B-ETH_INR",  "side": "sell"},
    ]},
    # INR -> ETH -> USDT -> INR
    {"name": "INR→ETH→USDT→INR", "legs": [
        {"pair": "B-ETH_INR",  "side": "buy"},
        {"pair": "B-ETH_USDT", "side": "sell"},
        {"pair": "B-USDT_INR", "side": "sell"},
    ]},
]

state = {"last_scan": "Starting...", "results": []}


def fetch_orderbook(pair):
    """Return (best_bid, best_ask) as Decimals; None on failure."""
    try:
        r = requests.get(
            "https://public.coindcx.com/market_data/market_data/orderbook/",
            params={"pair": pair},
            timeout=5,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        bids = data.get("bids", {})
        asks = data.get("asks", {})
        if not bids or not asks:
            return None
        best_bid = max(Decimal(p) for p in bids.keys())
        best_ask = min(Decimal(p) for p in asks.keys())
        return (best_bid, best_ask)
    except Exception:
        return None


def compute_path_net(capital_inr, path, books):
    """
    Simulate one 3-leg path.
    Returns (net_profit_pct, final_inr, leg_details) or None if data missing.
    """
    amount = capital_inr
    details = []

    for leg in path["legs"]:
        pair = leg["pair"]
        side = leg["side"]

        if pair not in books or books[pair] is None:
            return None

        bid, ask = books[pair]

        if side == "buy":
            fee_rate = FEE_INR if pair.endswith("_INR") else FEE_C2C
            effective_price = ask * (Decimal("1") + fee_rate)
            amount = amount / effective_price
            details.append(f"BUY {pair} @ ask {ask} fee {fee_rate*100:.2f}%")

        else:  # sell
            fee_rate = FEE_INR if pair.endswith("_INR") else FEE_C2C
            gross = amount * bid
            net = gross * (Decimal("1") - fee_rate - TDS)
            amount = net
            details.append(
                f"SELL {pair} @ bid {bid} "
                f"fee {fee_rate*100:.2f}% + TDS 1%"
            )

    final_inr = amount
    net_pct = (final_inr / capital_inr - Decimal("1")) * Decimal("100")
    return (net_pct, final_inr, details)


def scanner():
    while True:
        try:
            needed = set()
            for path in PATHS:
                for leg in path["legs"]:
                    needed.add(leg["pair"])

            books = {}
            for pair in needed:
                books[pair] = fetch_orderbook(pair)
                time.sleep(0.7)  # respect 100 req/min limit

            results = []
            for path in PATHS:
                out = compute_path_net(CAPITAL_INR, path, books)
                if out is None:
                    continue
                net_pct, final_inr, details = out
                results.append({
                    "path": path["name"],
                    "net_pct": net_pct,
                    "final_inr": final_inr,
                    "details": details,
                })

            results.sort(key=lambda x: x["net_pct"], reverse=True)
            state["results"] = results

            if results:
                best = results[0]
                state["last_scan"] = (
                    f"{time.strftime('%H:%M:%S')} | "
                    f"best: {best['path']} = {best['net_pct']:.3f}% "
                    f"(final ₹{best['final_inr']:.2f})"
                )
            else:
                state["last_scan"] = f"{time.strftime('%H:%M:%S')} | no data"

        except Exception as e:
            state["last_scan"] = f"{time.strftime('%H:%M:%S')} | error: {e}"

        time.sleep(8)


@app.route("/")
def home():
    rows = ""
    for r in state["results"]:
        color = "#0f0" if r["net_pct"] > 0 else "#f44"
        rows += f"""
        <div style='border:1px solid #333;padding:8px;margin:4px 0'>
          <b>{r['path']}</b> →
          <span style='color:{color}'>{r['net_pct']:.3f}%</span>
          (₹{r['final_inr']:.2f})
          <br><small style='color:#888'>{' → '.join(r['details'])}</small>
        </div>
        """
    return f"""
    <html><body style='background:#111;color:#eee;font-family:monospace;padding:15px'>
    <h3>CoinDCX 3-Leg Real Orderbook Scanner</h3>
    <div style='border:1px solid #0f0;padding:10px;margin:8px 0'>
      Capital: ₹{CAPITAL_INR} | Fees: INR {FEE_INR*100:.2f}% / C2C {FEE_C2C*100:.2f}% (incl GST) | TDS: 1%/sell
    </div>
    <div style='border:1px solid #0f0;padding:10px;margin:8px 0'>{state['last_scan']}</div>
    {rows}
    <div style='border:1px solid #f80;padding:10px;margin:8px 0;color:#f80'>
      Negative net profit is the normal result. 3-leg cost floor ≈ 3×C2C(0.20%) + 1×TDS(1%) ≈ 1.6%.
    </div>
    </body></html>
    """


threading.Thread(target=scanner, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
