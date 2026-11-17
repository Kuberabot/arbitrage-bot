from flask import Flask
import time, requests, threading

app = Flask(__name__)

CAPITAL = 900.0
MIN_PROFIT = 0.3

state = {
    "capital": CAPITAL,
    "profit": 0.0,
    "trades": 0,
    "best": "None",
    "best_profit": 0.0,
    "last_scan": "Starting...",
    "log": []
}

# 12 paths: (coin1, coin2, coin3) - all inside CoinDCX
PATHS = [
    ("USDT","BTC","INR"),
    ("BTC","ETH","INR"),
    ("ETH","USDT","INR"),
    ("USDT","ETH","INR"),
    ("BTC","USDT","INR"),
    ("ETH","BTC","INR"),
    ("USDT","SOL","INR"),
    ("SOL","ETH","INR"),
    ("USDT","DOGE","INR"),
    ("DOGE","USDT","INR"),
    ("USDT","XRP","INR"),
    ("XRP","USDT","INR"),
]

def get_prices():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10)
        data = r.json()
        prices = {}
        for t in data:
            prices[t['market']] = float(t['last_price'])
        return prices
    except Exception as e:
        return {}

def calc_path(prices, a, b, c):
    # INR -> A -> B -> INR
    # Need markets: AINR, BA, BINR
    try:
        # INR -> A
        p1 = prices[f"{a}INR"]
        # A -> B : price of B in A = BINR / AINR  OR BA market
        if f"{b}{a}" in prices:
            p_b_in_a = prices[f"{b}{a}"]
        else:
            p_b_in_a = prices[f"{b}INR"] / prices[f"{a}INR"]
        # B -> INR
        p3 = prices[f"{b}INR"]

        amount = CAPITAL
        amount_a = amount / p1
        amount_b = amount_a / p_b_in_a if f"{b}{a}" in prices else amount_a * (prices[f"{a}INR"] / prices[f"{b}INR"]) * (prices[f"{b}INR"]/prices[f"{b}INR"]) # simplified
        # Simpler triangular calc using INR pairs:
        # INR->A (buy A), A->B (sell A for B via B/A rate), B->INR (sell B)
        # Using INR prices for cross rate is same as direct
        amt_a = CAPITAL / prices[f"{a}INR"]
        # Convert A to B: amt_b = amt_a * (price A in INR / price B in INR) * (1 - fee)
        # If direct BA market exists, use it
        if f"{b}{a}" in prices:
            amt_b = amt_a / prices[f"{b}{a}"]
        else:
            amt_b = amt_a * prices[f"{a}INR"] / prices[f"{b}INR"]
        final = amt_b * prices[f"{b}INR"]
        profit_pct = (final - CAPITAL) / CAPITAL * 100
        return profit_pct, final
    except:
        return None, None

def scanner():
    while True:
        try:
            prices = get_prices()
            if prices:
                best_pct = -999
                best_path = "None"
                best_final = CAPITAL
                for (a,b,c) in PATHS:
                    pct, final = calc_path(prices, a, b, c)
                    if pct is not None and pct > best_pct:
                        best_pct = pct
                        best_path = f"INR->{a}->{b}->INR"
                        best_final = final
                state["trades"] += 1
                state["best"] = best_path
                state["best_profit"] = round(best_pct, 3)
                state["last_scan"] = f"{time.strftime('%H:%M:%S')} - Best {best_path} = {best_pct:.3f}% (Final Rs.{best_final:.2f}) - {'TRADE >0.3%!' if best_pct >= MIN_PROFIT else 'Waiting >0.3%'}"
                # Paper profit only - NO real trade without API key
                if best_pct >= MIN_PROFIT:
                    state["profit"] += (best_final - CAPITAL) * 0.01  # paper log
            time.sleep(5)
        except:
            time.sleep(5)

@app.route("/")
def home():
    return f"""
    <html><body style='background:black;color:#0f0;font-family:monospace;padding:10px'>
    <h3>CoinDCX Angular Bot - 12 Paths Live</h3>
    <div style='border:1px solid #0f0;padding:8px;margin:5px'>Capital: Rs.{CAPITAL} | Profit: Rs.{state['profit']:.2f} | Trades: {state['trades']}</div>
    <div style='border:1px solid #0f0;padding:8px;margin:5px'>BEST: {state['best']} = {state['best_profit']}%</div>
    <div style='border:1px solid #0f0;padding:8px;margin:5px'>{state['last_scan']}</div>
    <div style='border:1px solid #0f0;padding:8px;margin:5px'>Mode: PAPER - Auto-trade inside CoinDCX when >0.3% | Scanning 12 paths | No API yet = No real trade</div>
    <p>Bot is LIVE - Refresh page</p>
    </body></html>
    """

threading.Thread(target=scanner, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
