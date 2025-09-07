import os, time, requests
from coinalyze import CoinalyzeClient

# === Telegram Setup ===
BOT_TOKEN = os.getenv("7955049742:AAFs7set_JJHoDZtekRh14VM22dyEz4IIag")          # Set in Render environment variables
CHAT_ID = int(os.getenv("460698568"))         # Set in Render environment variables
TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram(msg):
    requests.post(TG_URL, data={"chat_id": CHAT_ID, "text": msg})

# === Coinalyze Setup ===
API_KEY = os.getenv("68bc2b7e-5fef-444d-9471-23703e4af627")    # Set in Render environment variables
client = CoinalyzeClient(api_key=API_KEY)

SYMBOLS = ["BTCUSDT_PERP.A", "ETHUSDT_PERP.A"]
CANDLE_INTERVAL = "5m"

def check_scalping_signals():
    for symbol in SYMBOLS:
        # Fetch recent candles
        candles = client.get_candles(symbol, interval=CANDLE_INTERVAL, limit=20)
        highs = [float(c["high"]) for c in candles]
        volumes = [float(c["volume"]) for c in candles]

        recent_high = max(highs)
        avg_vol = sum(volumes)/len(volumes)

        # Fetch live data
        ticker = client.get_current_price(symbol)
        price = float(ticker["price"])

        liq_data = client.get_current_liquidation(symbol)
        volume = float(liq_data.get("volume", 0))
        liquidations = float(liq_data.get("liquidations", 0))
        avg_liq = sum([float(x) for x in client.get_liquidation_history(symbol, limit=20)]) / 20

        # Dynamic breakout signal
        if price > recent_high:
            send_telegram(f"🚀 Breakout scalp\nPair: {symbol}\nPrice: {price:.2f}\nRecent High: {recent_high:.2f}")

        # Volume spike signal
        if volume > avg_vol * 1.5:
            send_telegram(f"📊 Volume spike scalp\nPair: {symbol}\nVolume: {volume:.2f} (avg {avg_vol:.2f})")

        # Liquidation spike signal
        if liquidations > avg_liq * 1.5:
            send_telegram(f"💥 Liquidation spike scalp\nPair: {symbol}\nLiquidations: ${liquidations:,.0f} (avg ${avg_liq:,.0f})")

def main():
    while True:
        try:
            check_scalping_signals()
        except Exception as e:
            send_telegram(f"⚠️ Bot error: {e}")
        time.sleep(30)  # check every 30 seconds

if __name__ == "__main__":
    main()


