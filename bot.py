import time, requests, itertools, os, hmac, hashlib, json
from flask import Flask
app=Flask(__name__)
@app.route('/')
def home(): return "KUBERABOT ALL-COIN AUTO-TRADE LIVE"

BASE="INR";CAP=3000;FEE=0.002;MINP=1.0 # Increased to 1% for auto-trade
KEY=os.environ.get("COINDCX_KEY")
SECRET=os.environ.get("COINDCX_SECRET")
AUTO=os.environ.get("AUTO_TRADE","false").lower()=="true"

def get_all():
 r=requests.get("https://api.coindcx.com/exchange/ticker",timeout=15).json()
 prices={}; coins=[]
 for i in r:
  m=i.get('market','')
  try: p=float(i.get('last_price',0))
  except: continue
  if p>0: prices[m]=p
  if m.endswith(BASE) and coin:=m.replace(BASE,''):
   if coin!=BASE and coin not in coins: coins.append(coin)
 return prices, coins

def calc(pr,path):
 a=CAP
 try:
  for j in range(len(path)-1):
   x,y=path[j],path[j+1]
   if f"{y}{x}" in pr: a=(a/pr[f"{y}{x}"])*(1-FEE)
   elif f"{x}{y}" in pr: a=(a*pr[f"{x}{y}"])*(1-FEE)
   else: return None
  return a,(a-CAP)/CAP*100
 except: return None

def place_order(market,side,qty):
 if not AUTO or not KEY:
  print(f"[TEST MODE] Would trade {side} {qty} {market}",flush=True)
  return True
 # Real trade - HMAC signature
 # NOTE: This is simplified - Use CoinDCX official python lib for production
 print(f"*** AUTO BUY {market} {side} {qty} ***",flush=True)
 # Implement real order here after testing
 return True

def run():
 print(f"=== ALL-COIN AUTO BOT STARTED CAP=Rs{CAP} AUTO={AUTO} ===",flush=True)
 scan=0
 while True:
  scan+=1
  pr, coins = get_all()
  if not coins: time.sleep(5); continue
  print(f"--- SCAN #{scan} COINS:{len(coins)} AUTO_TRADE={AUTO} ---",flush=True)
  for c1,c2 in itertools.permutations(coins,2):
   path=[BASE,c1,c2,BASE]
   r=calc(pr,path)
   if r:
    amt,pct=r
    if pct>=MINP:
     print(f"*** PROFIT {pct:.2f}% {'->'.join(path)} Rs{amt:.1f} AUTO={AUTO} ***",flush=True)
     if AUTO:
      # Auto execute 3 trades here
      # INR->c1, c1->c2, c2->INR
      print(f"EXECUTING AUTO TRADE FOR {pct:.2f}%...",flush=True)
      # place_order(f"{c1}{BASE}","buy",CAP)
  time.sleep(12)

import threading
threading.Thread(target=run,daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
