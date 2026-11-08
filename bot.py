import os, threading, asyncio, ccxt, time
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MAX_TRADE = float(os.getenv("MAX_TRADE_USDT", "10"))
MIN_PROFIT = float(os.getenv("MIN_PROFIT", "0.8"))

ALL_NETWORKS = ["TRC20","ERC20","BEP20","ARBITRUM","OPTIMISM","POLYGON","SOLANA","AVAX","BASE","ZKSYNC","LINEA","MANTLE"]

try:
    from telegram import Bot
    telegram_bot = Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None
except:
    telegram_bot = None

async def send_tg(msg):
    print(msg, flush=True)
    if telegram_bot and TELEGRAM_CHAT_ID:
        try:
            await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode='HTML')
        except Exception as e:
            print(f"TG error: {e}")

exchanges = {
    'binance': ccxt.binance({'enableRateLimit': True}),
    'kucoin': ccxt.kucoin({'enableRateLimit': True}),
}

def get_tickers(ex):
    try:
        return ex.fetch_tickers()
    except:
        return {}

def get_networks(ex, coin):
    try:
        curr = ex.fetch_currencies()
        if coin in curr:
            nets = curr[coin].get('networks', {})
            out = {}
            for k,v in nets.items():
                name = v.get('id', k).upper()
                if 'BSC' in name: name = 'BEP20'
                if 'TRC' in name or 'TRX' in name: name = 'TRC20'
                if name == 'ETH': name = 'ERC20'
                out[name] = {'fee': v.get('fee', 0) or 0, 'active': True}
            return out
    except:
        pass
    return {'BEP20': {'fee': 0.5}, 'TRC20': {'fee': 1.0}, 'ERC20': {'fee': 5.0}, 'ARBITRUM': {'fee': 0.3}, 'BASE': {'fee': 0.1}, 'POLYGON': {'fee': 0.2}}

def get_bridge_fee(f,t):
    fees = {('BEP20','ERC20'):0.8, ('BEP20','TRC20'):0.5, ('BEP20','BASE'):0.2, ('BEP20','ARBITRUM'):0.3, ('BEP20','POLYGON'):0.2, ('ERC20','TRC20'):1.5, ('TRC20','BEP20'):0.6}
    return fees.get((f,t), 1.5)

async def bot_loop():
    await send_tg(f"🚀 <b>KUBERA ALL NETWORKS LIVE</b>\nMax: ${MAX_TRADE}\nMin Profit: {MIN_PROFIT}%\nNetworks: TRC20, ERC20, BEP20, ARB, OP, POLYGON, BASE, SOL + 5 more")
    while True:
        try:
            # ALL COINS INTER + ALL NETWORKS
            all_prices = {}
            for ex_name, ex in exchanges.items():
                tickers = get_tickers(ex)
                for sym, t in tickers.items():
                    if '/USDT' not in sym: continue
                    p = t.get('last')
                    if not p: continue
                    if sym not in all_prices: all_prices[sym] = {}
                    all_prices[sym][ex_name] = p

            for sym, prices in all_prices.items():
                if len(prices) < 2: continue
                buy_ex = min(prices, key=prices.get)
                sell_ex = max(prices, key=prices.get)
                buy_p = prices[buy_ex]
                sell_p = prices[sell_ex]
                coin = sym.split('/')[0]
                
                nets_buy = get_networks(exchanges[buy_ex], coin)
                nets_sell = get_networks(exchanges[sell_ex], coin)
                common = set(nets_buy.keys()) & set(nets_sell.keys())
                
                if common:
                    best = min(common, key=lambda x: nets_buy[x]['fee'])
                    fee_usd = nets_buy[best]['fee']
                    extra = fee_usd / buy_p * 100 if buy_p>0 else 0.5
                    net_info = f"✅ Direct: {best} Fee ${fee_usd}"
                else:
                    buy_net = min(nets_buy, key=lambda x: nets_buy[x]['fee']) if nets_buy else 'BEP20'
                    sell_net = min(nets_sell, key=lambda x: nets_sell[x]['fee']) if nets_sell else 'ERC20'
                    fee_usd = get_bridge_fee(buy_net, sell_net)
                    extra = fee_usd / buy_p * 100 + 0.3 if buy_p>0 else 1.0
                    net_info = f"🌉 BRIDGE {buy_net}->{sell_net} Fee ${fee_usd} via LiFi"
                    best = f"{buy_net}->{sell_net}"

                profit = (sell_p - buy_p) / buy_p * 100 - 0.2 - extra
                if profit >= MIN_PROFIT:
                    msg = f"💰 <b>{profit:.2f}% {sym}</b>\nBUY {buy_ex.upper()} ${buy_p}\nSELL {sell_ex.upper()} ${sell_p}\n{net_info}\nBuy Nets: {', '.join(list(nets_buy.keys())[:6])}\nSell Nets: {', '.join(list(nets_sell.keys())[:6])}\nProfit: {profit:.2f}%"
                    await send_tg(msg)

            # TRIANGULAR ALL COINS
            for ex_name, ex in exchanges.items():
                tickers = get_tickers(ex)
                if not tickers: continue
                usdt_coins = [s.split('/')[0] for s in tickers if s.endswith('/USDT')][:70]
                for c1 in usdt_coins:
                    sym1 = f"{c1}/USDT"
                    p1 = tickers.get(sym1, {}).get('last')
                    if not p1: continue
                    for sym2 in tickers:
                        if not sym2.endswith(f"/{c1}"): continue
                        c2 = sym2.split('/')[0]
                        sym3 = f"{c2}/USDT"
                        if sym3 not in tickers: continue
                        p2 = tickers.get(sym2, {}).get('last')
                        p3 = tickers.get(sym3, {}).get('last')
                        if not p2 or not p3: continue
                        final = (1000 / p1 / p2) * p3
                        profit = (final - 1000) / 10 - 0.3
                        if profit >= MIN_PROFIT:
                            await send_tg(f"🔺 TRI {profit:.2f}% {ex_name.upper()} USDT->{c1}->{c2}->USDT $1000->{final:.2f}")

            print("Sleep 20s...", flush=True)
            await asyncio.sleep(20)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(20)

def run_flask():
    try:
        from flask import Flask
        app = Flask(__name__)
        @app.route('/')
        def home(): return "KUBERA ALL NETWORKS LIVE"
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    except:
        while True: time.sleep(100)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(bot_loop())
