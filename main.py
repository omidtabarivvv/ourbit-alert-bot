import os
import time
import json
import requests
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = "https://api.ourbit.com"

CHECK_INTERVAL = 30
DROP_PERCENT = 50

PRICE_FILE = "prices.json"
ALERT_FILE = "alerts.json"


def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except:
            return default
    return default


def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)


price_history = load_json(PRICE_FILE, {})
alerted = set(load_json(ALERT_FILE, []))


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=15
        )
    except Exception as e:
        print(e)


def get_all_prices():
    r = requests.get(
        BASE_URL + "/api/v3/ticker/price",
        timeout=20
    )

    r.raise_for_status()

    return r.json()


def save_alerts():
    save_json(ALERT_FILE, list(alerted))
    def update_price_history():

    now = int(time.time())

    prices = get_all_prices()

    for item in prices:

        symbol = item["symbol"]

        if not symbol.endswith("USDT"):
            continue

        price = float(item["price"])

        if symbol not in price_history:
            price_history[symbol] = []

        price_history[symbol].append({
            "time": now,
            "price": price
        })

        price_history[symbol] = [
            x for x in price_history[symbol]
            if now - x["time"] <= 3700
        ]

    save_json(PRICE_FILE, price_history)


def check_alerts():

    now = int(time.time())

    for symbol in price_history:

        if symbol in alerted:
            continue

        history = price_history[symbol]

        if len(history) < 2:
            continue

        current = history[-1]

        old = None

        for item in history:

            if now - item["time"] >= 3600:
                old = item

        if old is None:
            continue

        old_price = old["price"]
        current_price = current["price"]

        drop = ((old_price - current_price) / old_price) * 100

        if drop >= DROP_PERCENT:

            message = (
                f"🚨 OURBIT ALERT 🚨\n\n"
                f"Coin: {symbol}\n"
                f"Drop: {drop:.2f}%\n"
                f"60m Ago: {old_price}\n"
                f"Now: {current_price}"
            )

            send_telegram(message)

            alerted.add(symbol)

            save_alerts()

            print(symbol, "ALERT SENT")
            print("OURBIT ALERT BOT STARTED")

while True:

    try:

        update_price_history()

        check_alerts()

        print(
            datetime.now().strftime("%H:%M:%S"),
            "- Checked"
        )

    except Exception as e:

        print("ERROR:", e)

    time.sleep(CHECK_INTERVAL)
