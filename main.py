import os
import time
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = "https://api.ourbit.com"

CHECK_INTERVAL = 30
DROP_PERCENT = 50

alerted = set()


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram Error:", e)


def get_symbols():
    url = BASE_URL + "/api/v3/ticker/price"

    r = requests.get(url, timeout=20)
    r.raise_for_status()

    return r.json()


def get_old_price(symbol):
    url = BASE_URL + "/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 2
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()

    candles = r.json()

    if len(candles) < 2:
        return None

    return float(candles[0][4])def check_market():

    symbols = get_symbols()

    for item in symbols:

        try:

            symbol = item["symbol"]

            if not symbol.endswith("USDT"):
                continue

            current_price = float(item["price"])

            old_price = get_old_price(symbol)

            if old_price is None:
                continue

            drop = ((old_price - current_price) / old_price) * 100

            if drop >= DROP_PERCENT:

                if symbol not in alerted:

                    message = (
                        f"🚨 OURBIT ALERT 🚨\n\n"
                        f"Coin: {symbol}\n"
                        f"1 Hour Drop: {drop:.2f}%\n"
                        f"Old Price: {old_price}\n"
                        f"Current Price: {current_price}"
                    )

                    send_telegram(message)

                    alerted.add(symbol)

                    print(f"Alert Sent -> {symbol}")

        except Exception as e:

            print("Error:", e)


print("Ourbit Alert Bot Started...")

while True:

    try:

        check_market()

    except Exception as e:

        print("Loop Error:", e)

    time.sleep(CHECK_INTERVAL)
