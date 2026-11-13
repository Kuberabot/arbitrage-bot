import time, requests, itertools, os
from flask import Flask
app=Flask(__name__)
@app.route('/')
def home(): return "Kuberabot 10-COIN 3-4 ANG LIVE Rs3000"

SYM=["BTC","ETH","SOL","BNB","USDT","XRP","MATIC","ADA","DOGE","SHIB"]
BASE="INR";CAP=3000;FEE=0.002;MINP=0.8

def getp():
 d={}
 try:
  r=requests.get("https://api.coindcx.com/exchange/ticker",timeout=10).json()
  for i in r:
   m=i.get('market',''); p=float(i.get('last_price',0)or 0)
   if p>0: d[m]=p
 except: pass
 return d

def calc(pr,path):
 a=CAP
 try:
  for j in range(len(path)-1):
   x,y=path[j],path[j+1]
   p1=f"{y}{x}"; p2=f"{x}{y}"
   if p1 in pr: a=(a/pr[p1])*(1-FEE)
   elif p2 in pr: a=(a*pr[p2])*(1-FEE)
   else: return None
  return a,(a-CAP)/CAP*100
 except: return None

def run():
 print("=== 10-COIN KUBERABOT 3-4 ANG STARTED ===",flush=True)
 print(f"Coins: {SYM}",flush=True)
 cnt=0
 while True:
  pr=getp()
  if not pr: time.sleep(5); continue
  cnt+=1
  print(f"--- SCAN #{cnt} {time.strftime('%H:%M:%S')} ---",flush=True)
  prof=0
  for coins in itertools.permutations(SYM,2):
   path=[BASE,coins[0],coins[1],BASE]
   r=calc(pr,path)
   if r:
    amt,pct=r
    if pct>=MINP:
     print(f"*** 3-ANG PROFIT {pct:.2f}% {'->'.join(path)} Rs{amt:.1f} ***",flush=True)
     prof+=1
    elif pct>=0.0:
     print(f"3-ANG {'->'.join(path)} +{pct:.2f}% Rs{amt:.1f}",flush=True)
  for coins in itertools.permutations(SYM,3):
   path=[BASE,coins[0],coins[1],coins[2],BASE]
   r=calc(pr,path)
   if r and r[1]>=MINP:
    amt,pct=r
    print(f"*** 4-ANG PROFIT {pct:.2f}% {'->'.join(path)} Rs{amt:.1f} ***",flush=True)
    prof+=1
  if prof==0:
   print(f"No profit >{MINP}% this scan - fees eating",flush=True)
  time.sleep(12)

import threading
threading.Thread(target=run,daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
