from flask import Blueprint, render_template, session
import requests
import datetime
import os

index_blueprint = Blueprint("index", __name__)


def send_telegram_alert(page_name):
    print("Checking if Telegram alert should be sent for", page_name)
    if not session.get('alerted'):
                
        telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        proxies = {
            'http': 'http://proxy.server:3128',
            'https': 'http://proxy.server:3128',
        }

        now = datetime.datetime.now().strftime("%H:%M:%S")
        message = f"🔔 {now} - New visitor on pythonanywhere {page_name}!"

        try:
            response = requests.get(
                f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                    params={
                    "chat_id": telegram_chat_id,
                    "text": message,
                },
                proxies=proxies,
                timeout=5,
                )
            response.raise_for_status()

        except Exception as e:
            print(f"Telegram failed: {e}")
            return
        
        session['alerted'] = True  # Mark as alerted for this browser session


# HOME PAGE
@index_blueprint.get("/", strict_slashes=False)
def index():
    send_telegram_alert("Homepage")
    return render_template("index.html")