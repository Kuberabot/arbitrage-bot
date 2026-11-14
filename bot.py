
import time, requests, threading, os, json
from flask import Flask
from datetime import datetime

app = Flask(__name__)

CAP = 3000.0
MIN_REAL_PROFIT = 0.25
TARGET = 30.0
DATA_FILE = "balance.json"
REAL_COINS = ['BTC','ETH','XRP','SOL','DOGE','SHIB','ADA','AVAX','MATIC','DOT','LTC','TRX','BCH','LINK','UNI','ETC','XLM','ATOM','NEAR','FIL','PEPE','FLOKI','BONK','WIF']

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
            json.dump({"BALANCE":bal,"PROFIT":prof,"TRADES":trades,"DAILY":daily},f)
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
    print(f"V3 LIVE Loaded BAL Rs{BALANCE} TRADES {TRADES}")
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
                            path=f"INR->{a}->{b}->INR {pair}"
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
                last_scan={"path":path,"best":round(best,3),"Rs":round(profit_rs,2)}
                save_state(BALANCE,PROFIT,TRADES,DAILY_PROFIT)
            print(f"*** TRADE #{TRADES} {path} NET {best:.3f}% +Rs{profit_rs:.2f} BAL Rs{BALANCE:.2f} ***")
        else:
            print(f"SCAN #{scan_no} Best={best:.3f}% BAL Rs{cur_bal:.1f} DAILY Rs{DAILY_PROFIT:.1f}")
        time.sleep(8)

threading.Thread(target=scan_loop,daemon=True).start()

@app.route("/")
def home():
    with lock:
        return f"V3 PERSISTENT LIVE | BAL Rs{BALANCE:.1f} | PROFIT Rs{PROFIT:.1f} | DAILY Rs{DAILY_PROFIT:.1f} | TRADES {TRADES} | Last {last_scan} | Scans {scan_no}"

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
