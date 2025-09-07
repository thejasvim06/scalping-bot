import os
import time
import requests
from flask import Flask
from threading import Thread

# =======================
# Telegram Setup
# =======================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"
CHAT_ID = int(os.getenv("CHAT_ID") or "YOUR_CHAT_ID")
TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram(msg):
    """Send message to Telegram"""
    try:
        requests.post(TG_URL, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print(f"Telegram error: {e}")

# Send test message on startup
send_telegram("✅ Scalping bot started!")

# =======================
# Coinalyze API Functions
# =======================
BASE_URL = "https://api.coinalyze.net/v1/futures"

def get_candles(symbol, interval="5m", limit=20):
    url = f"{BASE_URL}/candles?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data
    except Exception as e:
        print(f"Candles fetch error for {symbol}: {e}")
    return []

def get_current_price(symbol):
    url = f"{BASE_URL}/tickers?symbol={symbol}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return float(data[0].get("last", 0))
    except Exception as e:
        print(f"Price fetch error for {symbol}: {e}")
    return None

def get_liquidation_data(symbol):
    url = f"{BASE_URL}/liquidation?symbol={symbol}&limit=20"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            volumes = [float(x.get("volume",0)) for x in data]
            total_liq = sum(volumes)
            avg_liq = total_liq / max(len(volumes), 1)
            return total_liq, avg_liq
    except Exception as e:
        print(f"Liquidation fetch error for {symbol}: {e}")
    return 0, 0

# =======================
# Bot Settings
# =======================
SYMBOLS = ["BTCUSDT_PERP.A", "ETHUSDT_PERP.A"]
CANDLE_INTERVAL = "5m"  # Use "1m" or "5m" for scalping

def check_scalping_signals():
    for symbol in SYMBOLS:
        candles = get_candles(symbol, interval=CANDLE_INTERVAL, limit=20)
        if not candles:
            continue

        highs = [float(c.get("high",0)) for c in candles if "high" in c]
        volumes = [float(c.get("volume",0)) for c in candles if "volume" in c]

        if not highs or not volumes:
            continue

        recent_high = max(highs)
        avg_vol = sum(volumes)/len(volumes)

        price = get_current_price(symbol)
        if price is None:
            continue

        total_liq, avg_liq = get_liquidation_data(symbol)

        # --- Breakout Signal ---
        if price > recent_high:
            send_telegram(f"🚀 Breakout scalp\nPair: {symbol}\nPrice: {price:.2f}\nRecent High: {recent_high:.2f}")

        # --- Volume Spike Signal ---
        if volumes[-1] > avg_vol * 1.5:
            send_telegram(f"📊 Volume spike scalp\nPair: {symbol}\nVolume: {volumes[-1]:.2f} (avg {avg_vol:.2f})")

        # --- Liquidation Spike Signal ---
        if total_liq > avg_liq * 1.5:
            send_telegram(f"💥 Liquidation spike scalp\nPair: {symbol}\nLiquidations: ${total_liq:,.0f} (avg ${avg_liq:,.0f})")

def start_bot():
    while True:
        try:
            check_scalping_signals()
        except Exception as e:
            print(f"Bot error: {e}")
        time.sleep(30)  # adjust frequency as needed

# =======================
# Flask Keep-Alive Server
# =======================
app = Flask(__name__)

@app.route("/")
def home():
    return "Scalping bot is running!"

# =======================
# Run Bot + Flask
# =======================
if __name__ == "__main__":
    # Run bot in a separate thread
    bot_thread = Thread(target=start_bot)
    bot_thread.start()

    # Run Flask server (Render free web service requires binding to a port)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
