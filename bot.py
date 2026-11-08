import os, threading, asyncio, ccxt
print("KUBERA Starting...", flush=True)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

telegram_bot = None
try:
    from telegram import Bot
    if TELEGRAM_TOKEN:
        telegram_bot = Bot(token=TELEGRAM_TOKEN)
except:
    pass

async def send_tg(msg):
    print(msg, flush=True)
    if telegram_bot and TELEGRAM_CHAT_ID:
        try:
            await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        except:
            pass

exchanges = {
    'binance': ccxt.binance({'enableRateLimit': True}),
    'kucoin': ccxt.kucoin({'enableRateLimit': True}),
}

def get_tickers(ex):
    try:
        return ex.fetch_tickers()
    except:
        return {}

async def bot_loop():
    await send_tg("🚀 KUBERA BOT LIVE")
    while True:
        try:
            for ex_name, ex in exchanges.items():
                tickers = get_tickers(ex)
                print(f"{ex_name}: {len(tickers)} tickers", flush=True)
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Error: {e}", flush=True)
            await asyncio.sleep(10)

def run_flask():
    from flask import Flask
    app = Flask(__name__)
    @app.route('/')
    def home():
        return "KUBERA LIVE - OK"
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(bot_loop())
