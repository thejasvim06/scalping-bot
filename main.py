import os
import time
import requests

# === Telegram Setup ===
BOT_TOKEN = os.getenv("BOT_TOKEN")          # Your Telegram bot token
CHAT_ID = int(os.getenv("CHAT_ID"))         # Your chat or group ID
TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram(msg):
    requests.post(TG_URL, data={"chat_id": CHAT_ID, "text": msg})

# === Coinalyze API Functions ===

BASE_URL = "https://api.coinalyze.net/v1/futures"

def get_candles(symbol, interval="15m", limit=20):
    """Fetch recent candles for a symbol"""
    url = f"{BASE_URL}/candles?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def get_current_price(symbol):
    """Fetch current price of a symbol"""
    url = f"{BASE_URL}/tickers?symbol={symbol}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        return float(response.json()[0]["last"])
    return None

def get_liquidation_data(symbol):
    """Fetch liquidation volume for a symbol"""
    url = f"{BASE_URL}/liquidation?symbol={symbol}&limit=20"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            volumes = [float(x.get("volume", 0)) for x in data]
            total_liq = sum(volumes)
            avg_liq = total_liq / max(len(volumes), 1)
            return total_liq, avg_liq
    return 0, 0

# === Bot Settings ===
SYMBOLS = ["BTCUSDT_PERP.A", "ETHUSDT_PERP.A"]
CANDLE_INTERVAL = "15m"

def check_scalping_signals():
    for symbol in SYMBOLS:
        # --- Fetch candle data ---
        candles = get_candles(symbol, interval=CANDLE_INTERVAL, limit=20)
        if not candles:
            continue

        highs = [float(c["high"]) for c in candles]
        volumes = [float(c["volume"]) for c in candles]

        recent_high = max(highs)
        avg_vol = sum(volumes)/len(volumes)

        # --- Fetch live price ---
        price = get_current_price(symbol)
        if price is None:
            continue

        # --- Fetch liquidation data ---
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

def main():
    while True:
        try:
            check_scalping_signals()
        except Exception as e:
            send_telegram(f"⚠️ Bot error: {e}")
        time.sleep(30)  # run every 30 seconds

if __name__ == "__main__":
    main()
