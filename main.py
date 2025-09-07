import os
import time
import requests
from flask import Flask
from threading import Thread

# ---------------------------
# Telegram Setup
# ---------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"
CHAT_ID = int(os.getenv("CHAT_ID") or "YOUR_CHAT_ID")
TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram(msg):
    try:
        r = requests.post(TG_URL, data={"chat_id": CHAT_ID, "text": msg})
        print(f"Telegram response: {r.status_code}, {r.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

send_telegram("✅ Scalping bot started! (debug)")

# ---------------------------
# Coinalyze API Functions
# ---------------------------
BASE_URL = "https://api.coinalyze.net/v1/futures"

def get_candles(symbol, interval="1m", limit=20):
    try:
        r = requests.get(f"{BASE_URL}/candles?symbol={symbol}&interval={interval}&limit={limit}", timeout=10)
        data = r.json()
        if isinstance(data, list):
            return data
    except Exception as e:
        print(f"Candles fetch error for {symbol}: {e}")
    return []

def get_current_price(symbol):
    try:
        r = requests.get(f"{BASE_URL}/tickers?symbol={symbol}", timeout=10)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            return float(data[0].get("last",0))
    except Exception as e:
        print(f"Price fetch error for {symbol}: {e}")
    return None

def get_liquidation_data(symbol):
    try:
        r = requests.get(f"{BASE_URL}/liquidation?symbol={symbol}&limit=20", timeout=10)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            volumes = [float(x.get("volume",0)) for x in data]
            total = sum(volumes)
            avg = total / max(len(volumes),1)
            return total, avg
    except Exception as e:
        print(f"Liquidation fetch error for {symbol}: {e}")
    return 0,0

# ---------------------------
# Bot Logic
# ---------------------------
SYMBOLS = ["BTCUSDT_PERP.A","ETHUSDT_PERP.A"]
CANDLE_INTERVAL = "1m"

def check_scalping_signals():
    for symbol in SYMBOLS:
        try:
            candles = get_candles(symbol, CANDLE_INTERVAL)
            if not candles: continue

            highs = [float(c.get("high",0)) for c in candles]
            volumes = [float(c.get("volume",0)) for c in candles]
            recent_high = max(highs)
            avg_vol = sum(volumes)/len(volumes)

            price = get_current_price(symbol)
            if price is None: continue

            total_liq, avg_liq = get_liquidation_data(symbol)

            if price > recent_high:
                send_telegram(f"🚀 Breakout scalp {symbol} Price: {price:.2f} High: {recent_high:.2f}")
            if volumes[-1] > avg_vol*1.5:
                send_telegram(f"📊 Volume spike {symbol} Volume: {volumes[-1]:.2f} Avg: {avg_vol:.2f}")
            if total_liq > avg_liq*1.5:
                send_telegram(f"💥 Liquidation spike {symbol} Total: {total_liq:.0f} Avg: {avg_liq:.0f}")

        except Exception as e:
            print(f"Error checking {symbol}: {e}")

def start_bot():
    while True:
        try:
            check_scalping_signals()
        except Exception as e:
            print(f"Bot error: {e}")
        time.sleep(30)

# ---------------------------
# Flask Keep-Alive
# ---------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Scalping bot running!"

if __name__ == "__main__":
    Thread(target=start_bot).start()
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
