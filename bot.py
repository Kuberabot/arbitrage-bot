
import time, requests, itertools, os
from flask import Flask
app = Flask(__name__)

# ===== YOUR REAL MONEY SETTINGS =====
BASE = "INR"
CAP = 3000.0
FEE = 0.002  # 0.2% per trade
SLIPPAGE = 0.005  # 0.5% extra for bid/ask difference - THIS MAKES IT REALISTIC
MINP_REAL = 0.8  # Trade only if real profit >0.8% after fees+slippage

# Only high liquidity coins - paper profit = real profit here
HIGH_VOLUME_COINS = ["BTC","ETH","XRP","SOL","DOGE","SHIB","ADA","AVAX","LINK","MATIC","DOT","LTC","TRX","UNI","ETC","BCH","ATOM","XLM","NEAR","FIL","PEPE","BONK","WIF","FLOKI","USDT"]

# ===== PAPER BALANCE =====
balance = 3000.0
total_profit = 0.0
trades = 0

@app.route('/')
def home():
    return f"KUBERABOT REAL-MODE LIVE | Balance Rs{balance:.1f} | Profit Rs{total_profit:.1f} | Trades {trades} | Cap Rs{CAP}"

def get_all():
    try:
        # Get ticker
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=15).json()
        prices = {}
        all_coins = []
        for i in r:
            m = i.get('market','')
            try: p = float(i.get('last_price',0))
            except: continue
            if p <= 0: continue
            prices[m] = p
            if m.endswith(BASE):
                c = m.replace(BASE,'')
                if c and c != BASE and c not in all_coins:
                    all_coins.append(c)
        return prices, all_coins
    except Exception as e:
        print(f"API FAIL {e}", flush=True)
        return {}, []

def calc_real_profit(pr, path):
    """Calculate REAL profit after fees + slippage"""
    a = CAP
    try:
        for j in range(len(path)-1):
            x, y = path[j], path[j+1]
            if (y+x) in pr:
                # Buy with x, get y
                a = (a / pr[y+x]) * (1 - FEE - SLIPPAGE)
            elif (x+y) in pr:
                # Sell x for y
                a = (a * pr[x+y]) * (1 - FEE - SLIPPAGE)
            else:
                return None
        profit_pct = (a - CAP) / CAP * 100
        return a, profit_pct
    except:
        return None

def run():
    global balance, total_profit, trades
    print(f"=== REAL-PROFIT BOT STARTED ===", flush=True)
    print(f"CAP Rs{CAP} FEE {FEE*100}% SLIPPAGE {SLIPPAGE*100}% MIN_REAL_PROFIT {MINP_REAL}%", flush=True)
    print(f"TRADING ONLY HIGH VOLUME COINS: {HIGH_VOLUME_COINS}", flush=True)
    print(f"MODE: PAPER TRADING WITH REALISTIC PROFIT (no real money)", flush=True)
    scan = 0
    while True:
        scan += 1
        pr, all_coins = get_all()
        if not all_coins:
            time.sleep(5)
            continue
        
        # Filter only high volume coins for real trading
        coins = [c for c in all_coins if c in HIGH_VOLUME_COINS]
        
        print(f"\n--- SCAN #{scan} {time.strftime('%H:%M:%S')} AllCoins={len(all_coins)} RealCoins={len(coins)} BAL=Rs{balance:.1f} PROFIT=Rs{total_profit:.1f} ---", flush=True)
        
        best = None
        for c1, c2 in itertools.permutations(coins, 2):
            path = [BASE, c1, c2, BASE]
            res = calc_real_profit(pr, path)
            if not res:
                continue
            amt, pct = res
            # Show only real profits
            if pct >= 0.3:
                print(f"Real {pct:.2f}% {'->'.join(path)} -> Rs{amt:.1f}", flush=True)
            
            if pct >= MINP_REAL:
                # REAL PAPER TRADE
                profit_rs = amt - CAP
                balance += profit_rs
                total_profit += profit_rs
                trades += 1
                print(f"*** REAL PAPER TRADE #{trades} PROFIT {pct:.2f}% {'->'.join(path)} +Rs{profit_rs:.1f} BALANCE Rs{balance:.1f} ***", flush=True)
                best = (path, pct, profit_rs)
                time.sleep(1)
                break  # Trade 1 per scan to avoid over-trading
        
        if not best:
            print(f"No REAL profit >{MINP_REAL}% this scan - Balance Rs{balance:.1f}", flush=True)
        else:
            print(f"=== TOTAL: {trades} trades | Profit Rs{total_profit:.1f} | Balance Rs{balance:.1f} ===", flush=True)
        
        time.sleep(12)

import threading
threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
