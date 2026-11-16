
from flask import Flask
import threading, time, os, requests
from datetime import datetime

app = Flask(__name__)

# --- SETTINGS ---
CAPITAL = 900
MIN_PROFIT = 0.15  # Realistic for CoinDCX - will find 3-5 trades/day
total_profit = 0.0
trades = 0
last_msg = "Starting..."
best_opportunity = "Scanning..."

prices = {}

# 12 REAL paths inside CoinDCX only (1 to 3 legs)
PATHS = [
    ["INR","USDT","BTC","INR"],
    ["INR","BTC","USDT","INR"],
    ["INR","USDT","ETH","INR"],
    ["INR","ETH","USDT","INR"],
    ["INR","BTC","ETH","INR"],
    ["INR","ETH","BTC","INR"],
    ["INR","USDT","SOL","INR"],
    ["INR","SOL","USDT","INR"],
    ["INR","BTC","SOL","INR"],
    ["INR","ETH","SOL","INR"],
    ["INR","USDT","MATIC","INR"],
    ["INR","MATIC","USDT","INR"],
]

@app.route('/')
def home():
    return f"""
    <html><head><meta name='viewport' content='width=device-width'>
    <style>
    body{{font-family:monospace;background:#000;color:#0f0;padding:10px}}
    .box{{border:1px solid #0f0;padding:8px;margin:6px 0;font-size:13px;word-break:break-all}}
    </style></head><body>
    <h3>CoinDCX Angular Bot - 12 Paths Live</h3>
    <div class='box'>Capital: Rs.{CAPITAL} | Profit: Rs.{total_profit:.2f} | Trades: {trades}</div>
    <div class='box'>BEST: {best_opportunity}</div>
    <div class='box'>{last_msg}</div>
    <div class='box'>Mode: Auto-trade inside CoinDCX when >{MIN_PROFIT}% | Scanning 12 paths</div>
    <script>setTimeout(()=>location.reload(),4000)</script>
    </body></html>
    """

def convert(amount, frm, to):
    """Real CoinDCX conversion with 0.2% fee"""
    try:
        m1 = frm + to  # e.g., BTCINR
        m2 = to + frm  # e.g., INRBTC doesn't exist, but USDTINR does
        
        if m1 in prices and prices[m1] > 0:
            # m1 = frm+to = e.g., USDTINR? No, USDTINR is USDT+INR, price is INR per USDT
            # If we have USDT->INR and market is USDTINR: INR = USDT * price
            # If we have INR->USDT and market is USDTINR: USDT = INR / price
            # General: market = base+quote, price = quote per base
            # So: base->quote = amount * price, quote->base = amount / price
            # Here m1 = frm+to, so frm=base, to=quote => base->quote
            return amount * prices[m1] * 0.998
        
        if m2 in prices and prices[m2] > 0:
            # m2 = to+frm, so to=base, frm=quote? Wait
            # Example: frm=INR, to=USDT, m2=USDTINR exists. That's base=USDT quote=INR
            # We want INR->USDT: quote->base = amount / price
            return (amount / prices[m2]) * 0.998
    except:
        pass
    return None

def check_all():
    global total_profit, trades, last_msg, best_opportunity
    best_profit = -99
    best_path_str =
