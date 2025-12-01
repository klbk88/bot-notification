"""
Webhook version of admin bot - no polling conflicts!
"""
import os
from flask import Flask, request
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()

ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # Railway URL

app = Flask(__name__)
bot = TeleBot(ADMIN_BOT_TOKEN)

# Import all handlers from original bot
import sys
sys.path.insert(0, '/app/bots')
# Reuse handlers from admin_bot.py but switch to webhook mode

@app.route('/' + ADMIN_BOT_TOKEN, methods=['POST'])
def webhook():
    """Handle webhook updates from Telegram."""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = bot.process_new_updates([bot.update_from_json(json_string)])
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200

if __name__ == '__main__':
    # Set webhook
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{ADMIN_BOT_TOKEN}")

    # Run Flask
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
