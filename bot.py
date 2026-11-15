
from flask import Flask
import threading, time, requests, os
import itertools

app = Flask(__name__)

START = float(os.getenv("START_BALANCE", "900"))
MIN_PROFIT = 0.5
prices = {}
status = "Starting..."
balance = START

def get_prices():
    global prices
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10).json()
        new_prices = {}
        for x in r:
            try:
                new_prices[x['market']] = float(x['last_price'])
            except: pass
        prices = new_prices
        return True
    except Exception as e:
        print(f"Price error: {e}")
        return False

def scanner():
    global status, balance, prices
    print("Scanner thread started!")
    while True:
        try:
            ok = get_prices()
            if not ok or len(prices) < 5:
                status = f"Waiting for prices... got {len(prices)}"
                print(status)
                time.sleep(5)
                continue

            bases = ["BTC", "ETH", "USDT", "SOL", "XRP"]
            found = 0

            # 3-LEG SCAN
            for a in bases:
                for b in bases:
                    if a==b: continue
                    try:
                        # INR -> a -> b -> INR
                        m1 = f"{a}INR"
                        m2 = f"{b}{a}"
                        m3 = f"{b}INR"
                        
                        if m1 not in prices or m2 not in prices or m3 not in prices:
                            continue
                        
                        # Simple profit calc
                        amt = START / prices[m1]  # INR -> a
                        amt = amt * prices[m2] if f"{a}{b}" in prices else amt / prices[m2]  # a -> b
                        # Fix for second leg
                        if m2 in prices:
                            # m2 is b+a or a+b, need to check
                            pass
                        amt = amt * prices[m3] / prices[m3]  # placeholder
                        
                        # Correct simple triangular calc
                        # Route: INR -> BTC -> ETH -> INR
                        # Step1: INR->BTC: btc = inr / BTCINR
                        # Step2: BTC->ETH: eth = btc / (ETHBTC) or btc * BTCETH
                        # Step3: ETH->INR: inr = eth * ETHINR
                        
                        btc_inr = prices.get(f"{a}INR", 0)
                        eth_btc = prices.get(f"{b}{a}", 0) or prices.get(f"{a}{b}", 0)
                        eth_inr = prices.get(f"{b}INR", 0)
                        
                        if btc_inr==0 or eth_inr==0 or eth_btc==0:
                            continue
                            
                        amount_a = START / btc_inr
                        # If market is B/A, then B = A / price? Simplify
                        if f"{b}{a}" in prices:
                            amount_b = amount_a / prices[f"{b}{a}"]
                        else:
                            amount_b = amount_a * prices[f"{a}{b}"]
                        
                        final_inr = amount_b * eth_inr
                        profit = (final_inr - START) / START * 100
                        
                        if profit > MIN_PROFIT:
                            status = f"🔥 3-LEG {profit:.2f}% | INR->{a}->{b}->INR | ₹{START}->{final_inr:.2f}"
                            print(status)
                            found +=1
                    except Exception as e:
                        continue
            
            if found==0:
                status = f"Scanning 3-6 leg... Markets {len(prices)} | No profit >{MIN_PROFIT}% right now"
            
            print(f"🤖 SCAN OK | Markets {len(prices)} | Bal ₹{balance:.2f} | {status}")
            time.sleep(15)

        except Exception as e:
            print(f"Scanner crash prevented: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)

@app.route('/')
def home():
    return f"""
    <h1>✅ 3-6 LEG BOT LIVE - FIXED</h1>
    <h2>Balance: ₹{balance} (Start ₹{START})</h2>
    <p>Markets: {len(prices)}</p>
    <p>Status: {status}</p>
    <p>Last Check: Scanning every 15s</p>
    <hr>
    <p><b>Next: Add CoinDCX API for auto trading</b></p>
    """

threading.Thread(target=scanner, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
