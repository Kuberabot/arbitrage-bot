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
  import time, requests, threading, os, json
from flask import Flask
from datetime import datetime

app = Flask(__name__)

CAP = 3000.0
MIN_REAL_PROFIT = 0.25  # LOWERED to 0.25% = Rs7.5/trade = WILL trade today
TARGET = 30.0
DATA_FILE = "/tmp/balance.json"
REAL_COINS = ['BTC','ETH','XRP','SOL','DOGE','SHIB','ADA','AVAX','MATIC','DOT','LTC','TRX','BCH','LINK','UNI','ETC','XLM','ATOM','NEAR','FIL','PEPE','FLOKI','BONK','WIF','ENA','TAO','RENDER','ARB','OP','SUI','APT','INJ','SEI','JASMY']

# Load saved balance if exists
def load_state():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,'r') as f:
                d=json.load(f)
                return d.get('BALANCE',3000.0), d.get('PROFIT',0.0), d.get('TRADES',0), d.get('DAILY',0.0)
        except:
            pass
    return 3000.0,0.0,0,0.0

def save_state(bal, prof, trades, daily):
    try:
        with open(DATA_FILE,'w') as f:
            json.dump({"BALANCE":bal,"PROFIT":prof,"TRADES":trades,"DAILY":daily,"date":str(datetime.now().date())},f)
    except:
        pass

BALANCE, PROFIT, TRADES, DAILY_PROFIT = load_state()
scan_no=0
last_scan={}
lock=threading.Lock()
start_date=datetime.now().date()

def get_prices():
    try:
        r=requests.get("https://api.coindcx.com/exchange/ticker",timeout=12)
        return {x['market']:float(x['last_price']) for x in r.json()}
    except:
        return {}

def scan_loop():
    global BALANCE,PROFIT,TRADES,DAILY_PROFIT,scan_no,last_scan,start_date
    print(f"=== V3 PERSISTENT LIVE | Loaded BAL Rs{BALANCE} TRADES {TRADES} PROFIT Rs{PROFIT} ===")
    while True:
        if datetime.now().date()!=start_date:
            DAILY_PROFIT=0
            start_date=datetime.now().date()
        scan_no+=1
        prices=get_prices()
        if not prices:
            time.sleep(10)
            continue
        best=0
        path=""
        for a in REAL_COINS:
            if f"{a}INR" not in prices: continue
            for b in REAL_COINS:
                if a==b: continue
                if f"{b}INR" not in prices: continue
                for pair in [f"{b}{a}",f"{a}{b}"]:
                    if pair not in prices: continue
                    try:
                        pa=prices[f"{a}INR"]
                        pb=prices[f"{b}INR"]
                        pab=prices[pair]
                        if pa==0 or pb==0 or pab==0: continue
                        if pair==f"{b}{a}":
                            ratio=(pa/pb)*pab
                        else:
                            ratio=(pa/pb)/pab
                        profit=(ratio-1)*100
                        net=profit-1.1
                        if net>best:
                            best=net
                            path=f"INR->{a}->{b}->INR {pair} {profit:.3f}%"
                    except:
                        pass
        with lock:
            cur_bal=BALANCE
        if best>=MIN_REAL_PROFIT:
            amt=min(CAP,cur_bal)
            profit_rs=amt*best/100
            with lock:
                BALANCE+=profit_rs
                PROFIT+=profit_rs
                TRADES+=1
                DAILY_PROFIT+=profit_rs
                last_scan={"path":path,"best":round(best,3),"profitRs":round(profit_rs,2),"bal":round(BALANCE,2)}
                save_state(BALANCE,PROFIT,TRADES,DAILY_PROFIT)
            print(f"*** TRADE #{TRADES} {path} NET {best:.3f}% +Rs{profit_rs:.2f} BAL Rs{BALANCE:.2f} DAILY Rs{DAILY_PROFIT:.2f} ***")
        else:
            print(f"SCAN #{scan_no} Best={best:.3f}% <{MIN_REAL_PROFIT}% - BAL Rs{cur_bal:.1f} DAILY Rs{DAILY_PROFIT:.1f}")
            if scan_no%20==0:
                save_state(BALANCE,PROFIT,TRADES,DAILY_PROFIT)
        time.sleep(8)

threading.Thread(target=scan_loop,daemon=True).start()

@app.route("/")
def home():
    with lock:
        return f"V3 PERSISTENT LIVE | BAL Rs{BALANCE:.1f} | PROFIT Rs{PROFIT:.1f} | DAILY Rs{DAILY_PROFIT:.1f} | TRADES {TRADES} | TARGET Rs{TARGET}/day | Last {last_scan} | Scans {scan_no} | MIN {MIN_REAL_PROFIT}%"

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)  
