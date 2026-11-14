
import time, requests, threading
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# ===== Rs3000 DAILY PROFIT V2 - FIXED =====
CAP = 3000.0
BALANCE = 3000.0
PROFIT = 0.0
TRADES = 0
MIN_REAL_PROFIT = 0.35  # <--- FIXED FROM 0.8 to 0.35 FOR DAILY PROFIT
DAILY_TARGET = 30.0
MAX_LOSS = 100.0

# 35 high-liquidity coins = more triangles
REAL_COINS = ['BTC','ETH','XRP','SOL','DOGE','SHIB','ADA','AVAX','MATIC','DOT','LTC','TRX','BCH','LINK','UNI','ETC','XLM','ATOM','NEAR','FIL','PEPE','FLOKI','BONK','WIF','ENA','TAO','RENDER','ARB','OP','SUI','APT','INJ','SEI','JASMY']

balance_lock = threading.Lock()
last_scan = {}
scan_no = 0
daily_profit = 0.0
start_of_day = datetime.now().date()

def get_prices():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10)
        data = r.json()
        prices = {}
        for item in data:
            prices[item['market']] = float(item['last_price'])
        return prices
    except:
        return {}

def scan_loop():
    global BALANCE, PROFIT, TRADES, last_scan, scan_no, daily_profit, start_of_day
    print("=== Rs3000 DAILY PROFIT V2 STARTED - Target Rs30/day - Filter 0.35% ===")
    while True:
        if datetime.now().date() != start_of_day:
            print(f"=== DAILY SUMMARY {start_of_day}: Trades {TRADES}, Daily Profit Rs{daily_profit:.2f} ===")
            daily_profit = 0.0
            start_of_day = datetime.now().date()

        scan_no += 1
        prices = get_prices()
        if not prices:
            time.sleep(12)
            continue
        
        best_profit = 0
        best_path = ""
        
        for a in REAL_COINS:
            if f"{a}INR" not in prices: continue
            for b in REAL_COINS:
                if a==b: continue
                if f"{b}INR" not in prices: continue
                # Check both directions
                for pair in [f"{b}{a}", f"{a}{b}"]:
                    if pair in prices:
                        try:
                            pa = prices[f"{a}INR"]
                            pb = prices[f"{b}INR"]
                            pab = prices[pair]
                            if pair == f"{b}{a}":
                                ratio = (pa / pb) * pab if pb>0 and pab>0 else 0
                            else:
                                ratio = (pa / pb) / pab if pb>0 and pab>0 else 0
                            profit_pct = (ratio - 1) * 100
                            net = profit_pct - 1.1  # fee+slippage
                            if net > best_profit and net >= MIN_REAL_PROFIT:
                                best_profit = net
                                best_path = f"INR->{a}->{b}->INR via {pair}"
                        except:
                            pass
        
        with balance_lock:
            current_bal = BALANCE
            current_profit = PROFIT

        if current_bal < (CAP - MAX_LOSS):
            print(f"STOP LOSS - Balance Rs{current_bal:.1f}")
            time.sleep(60)
            continue

        if best_profit >= MIN_REAL_PROFIT:
            trade_amt = min(CAP, current_bal)
            profit_rs = trade_amt * best_profit / 100
            with balance_lock:
                BALANCE += profit_rs
                PROFIT += profit_rs
                TRADES += 1
                daily_profit += profit_rs
                last_scan = {"path": best_path, "profit%": round(best_profit,3), "profitRs": round(profit_rs,2), "balance": round(BALANCE,2)}
            print(f"*** REAL PAPER TRADE #{TRADES} {best_path} PROFIT {best_profit:.3f}% +Rs{profit_rs:.2f} BAL Rs{BALANCE:.2f} DAILY Rs{daily_profit:.2f} ***")
        else:
            # Show closest profit to know market
            print(f"SCAN #{scan_no} All={len(prices)} Best={best_profit:.3f}% <{MIN_REAL_PROFIT}% - No trade - BAL Rs{current_bal:.1f} DAILY Rs{daily_profit:.1f}")
        
        time.sleep(10)

threading.Thread(target=scan_loop, daemon=True).start()

@app.route("/")
def home():
    with balance_lock:
        return f"V2 Rs3000 DAILY LIVE | BAL Rs{BALANCE:.1f} | PROFIT Rs{PROFIT:.1f} | DAILY Rs{daily_profit:.1f} | TRADES {TRADES} | TARGET Rs{DAILY_TARGET}/day | Last {last_scan} | Scans {scan_no}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
