import os
import time
import threading
import requests
from flask import Flask

# === Telegram Setup ===
BOT_TOKEN = os.getenv("BOT_TOKEN")       # set in Render environment
CHAT_ID = os.getenv("CHAT_ID")           # set in Render environment
TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram(msg):
    resp = requests.post(TG_URL, data={"chat_id": CHAT_ID, "text": msg})
    print("Telegram response:", resp.status_code, resp.text)

# === Coinalyze API ===
BASE_URL = "https://api.coinalyze.net/v1/futures"

def get_candles(symbol, interval="1m", limit=20):
    url = f"{BASE_URL}/candles?symbol={symbol}&interval={interval}&limit={limit}"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else []

def get_price(symbol):
    url = f"{BASE_URL}/tickers?symbol={symbol}"
    r = requests.get(url)
    if r.status_code == 200 and r.json():
        return float(r.json()[0]["last"])
    return None

# === Bot Settings ===
SYMBOLS = ["BTCUSDT_PERP.A", "ETHUSDT_PERP.A"]
CANDLE_INTERVAL = "1m"

def check_signals():
    for symbol in SYMBOLS:
        candles = get_candles(symbol, interval=CANDLE_INTERVAL, limit=20)
        if not candles:
            continue

        highs = [float(c["high"]) for c in candles]
        closes = [float(c["close"]) for c in candles]
        volumes = [float(c["volume"]) for c in candles]

        price = get_price(symbol)
        if not price:
            continue

        # --- Breakout strategy ---
        recent_high = max(highs[:-1])  # exclude latest candle
        last_close = closes[-1]

        if last_close > recent_high:
            send_telegram(
                f"🚀 Breakout scalp\n"
                f"Pair: {symbol}\nPrice: {last_close:.2f}\nHigh: {recent_high:.2f}"
            )

        # --- Volume spike strategy ---
        avg_vol = sum(volumes[:-1]) / max(len(volumes) - 1, 1)
        last_vol = volumes[-1]

        if last_vol > avg_vol * 1.5:
            send_telegram(
                f"📊 Volume spike scalp\n"
                f"Pair: {symbol}\nVolume: {last_vol:.2f} (avg {avg_vol:.2f})"
            )

def bot_loop():
    send_telegram("✅ Scalping bot started! Now watching markets...")
    while True:
        try:
            check_signals()
        except Exception as e:
            send_telegram(f"⚠️ Bot error: {e}")
        time.sleep(60)  # check every 1 minute

# === Flask App for Keep-Alive ===
app = Flask(__name__)

@app.route("/")
def home():
    return "Scalping bot is running!"

if __name__ == "__main__":
    # Start bot loop in background thread
    threading.Thread(target=bot_loop, daemon=True).start()
    # Start web server for Render keep-alive
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
